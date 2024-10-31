#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
Prometheus client to export PowerScale network interface statistics
"""
# fmt: off
__title__         = "ps_net_stats"
__version__       = "0.1.0"
__date__          = "31 October 2024"
__license__       = "MIT"
__author__        = "Andrew Chung <andrew.chung@dell.com>"
__maintainer__    = "Andrew Chung <andrew.chung@dell.com>"
__email__         = "andrew.chung@dell.com"
# fmt: on
import logging
import re
import signal
import subprocess
import sys
import time

import helpers.constants as constants
import helpers.options_parser as options_parser

try:
    import yaml

    YAML_MODULE_AVAILABLE = True
except:
    YAML_MODULE_AVAILABLE = False
try:
    import prometheus_client as prometheus_client
    import prometheus_client.core as prometheus_core

    PROMETHEUS_MODULES_AVAILABLE = True
except:
    PROMETHEUS_MODULES_AVAILABLE = False

DEFAULT_LOG_FORMAT = "%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(message)s"
LOG = logging.getLogger()
PSCALE_ENDPOINTS = []
RE_NET_STAT_I = (
    r"\s*(?P<host>[^:]+)-(?P<lnn>[0-9]+):"
    r" *(?P<iface>[^ ]+)"
    r" *(?P<mtu>[^ ]+)"
    r" *(?P<net>[^ ]+)"
    r" *(?P<addr>[^ ]+)"
    r" *(?P<ipkts>[^ ]+)"
    r" *(?P<ierrs>[^ ]+)"
    r" *(?P<idrop>[^ ]+)"
    r" *(?P<opkts>[^ ]+)"
    r" *(?P<oerrs>[^ ]+)"
    r"*(?P<coll>[^\s]+)"
)
SSH_CMD_STR = "ssh {user}@{host} {cmd}"
CMD_CLUSTER_INFO = "isi cluster identity view"
CMD_NET_STATS = "sudo /usr/bin/isi_for_array -sX netstat -iW"


def get_cluster_name(endpoint):
    cluster_name = "UnableToGetClusterName"
    result = subprocess.run(
        [SSH_CMD_STR.format(user=endpoint["user"], host=endpoint["endpoint"], cmd=CMD_CLUSTER_INFO)],
        shell=True,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return cluster_name
    lines = result.stdout.split("\n")
    for line in lines:
        if "Name:" in line:
            parts = line.split(":")
            cluster_name = parts[1].strip()
    return cluster_name


def get_net_stats(endpoint):
    net_stats = None
    result = subprocess.run(
        [SSH_CMD_STR.format(user=endpoint["user"], host=endpoint["endpoint"], cmd=CMD_NET_STATS)],
        shell=True,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return net_stats
    return result.stdout


def parse_net_stats(net_stats_str):
    parsed_stats = {}
    lines = net_stats_str.split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            continue
        match = re.match(RE_NET_STAT_I, line)
        if not match:
            LOG.error("Unexpected line found in netstat -i output: %s" % line)
            continue
        lnn = match.group("lnn")
        if lnn not in parsed_stats:
            parsed_stats[lnn] = {}
        # Ignore header lines or loopback adapters
        if match.group("iface") in ["Name", "lo0"]:
            continue
        # Ignore the protocol specific entries in the netstat output
        if match.group("mtu") == "-":
            continue
        iface = match.group("iface")
        parsed_stats[lnn][iface] = {
            "ipkts": match.group("ipkts"),
            "ierrs": match.group("ierrs"),
            "idrop": match.group("idrop"),
            "opkts": match.group("opkts"),
            "oerrs": match.group("oerrs"),
            "coll": match.group("coll"),
        }
    return parsed_stats


def setup_logging(options):
    log_handler = logging.StreamHandler()
    log_handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
    LOG.addHandler(log_handler)
    if options.get("debug", 0):
        LOG.setLevel(logging.DEBUG)
    else:
        LOG.setLevel(logging.INFO)
    if options.get("debug", 0) < 2:
        # Disable loggers for sub modules
        for mod_name in ["libs.papi_lite"]:
            module_logger = logging.getLogger(mod_name)
            module_logger.setLevel(logging.WARN)


def signal_handler(signum, frame):
    global PSCALE_ENDPOINTS
    if signum in [signal.SIGINT, signal.SIGTERM]:
        sys.stdout.write("Terminating Prometheus proxy\n")
        sys.exit(0)


def to_float(val):
    if not val:
        return 0
    return float(val)


class NetStatsCollector(object):
    global PSCALE_ENDPOINTS

    def __init__(self):
        self.base_name = "isilon"
        self.stat_name = "net_stats"
        self.labels = [
            "cluster_name",
            "interface_name",
            "node_lnn",
        ]

    def collect(self):
        for endpoint in PSCALE_ENDPOINTS:
            raw_stats = get_net_stats(endpoint)
            if not raw_stats:
                LOG.warning("Unable to retrieve stats for endpoint: %s" % endpoint["endpoint"])
                continue
            parsed_stats = parse_net_stats(raw_stats)
            for node_lnn in parsed_stats.keys():
                for iface_name in parsed_stats[node_lnn].keys():
                    for stat in [
                        ["ipkts", "Number of packets received"],
                        ["ierrs", "Number of input errors"],
                        ["idrop", "Number of dropped input packets"],
                        ["opkts", "Number of packets sent"],
                        ["oerrs", "Number of output errors"],
                        ["coll", "Number of packet collisions"],
                    ]:
                        key_name = "_".join([self.base_name, self.stat_name, stat[0]])
                        description = stat[1]
                        metric = prometheus_core.CounterMetricFamily(key_name, description, labels=self.labels)
                        label_values = [
                            endpoint["cluster_name"],
                            iface_name,
                            node_lnn,
                        ]
                        metric.add_metric(label_values, to_float(parsed_stats[node_lnn][iface_name][stat[0]]))
                        yield metric


def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Setup command line parser and parse arguments
    (parser, options, args) = options_parser.parse(sys.argv, __version__, __date__)
    setup_logging(options)
    # Validate config options
    if not YAML_MODULE_AVAILABLE:
        sys.stderr.write(constants.STR_MISSING_MODULE_YAML)
        sys.exit(2)
    if not PROMETHEUS_MODULES_AVAILABLE:
        sys.stderr.write(constants.STR_MISSING_MODULE_PROMETHEUS)
        sys.exit(2)
    if not options["config"]:
        # If there are argument errors, exit with 1
        sys.stdout.write("A YAML configuration file is a required parameter\n")
        sys.exit(1)
    try:
        with open(options["config"], "r") as cfg_file:
            cfg_data = yaml.safe_load(cfg_file)
    except Exception as e:
        sys.stdout.write("An error occurred loading the configuration file: %s\n" % e)
        sys.exit(3)
    if not cfg_data:
        sys.stdout.write("An error occurred loading the configuration file: %s\n" % e)
        sys.exit(3)
    try:
        for item in cfg_data:
            if "cluster" in item:
                for key in ["endpoint", "user"]:
                    if key not in item["cluster"]:
                        LOG.error("Missing key (%s) in YAML configuration. Partial entry: %s" % (key, item["cluster"]))
                        break
                else:
                    PSCALE_ENDPOINTS.append(item["cluster"])
            else:
                LOG.warning("Unknown option in configuration file: %s" % item)
    except Exception as e:
        sys.stdout.write("An error occurred parsing the configuration file: %s\n" % e)
        sys.exit(4)

    if not PSCALE_ENDPOINTS:
        LOG.critical("No cluster endpoints found in the configuration file.")
        sys.exit(5)
    # Process each cluster group and generate metrics
    for endpoint in PSCALE_ENDPOINTS:
        LOG.debug("Configured to query: %s" % endpoint["endpoint"])
        endpoint["cluster_name"] = get_cluster_name(endpoint)
    try:
        prometheus_core.REGISTRY.unregister(prometheus_client.GC_COLLECTOR)
        prometheus_core.REGISTRY.unregister(prometheus_client.PLATFORM_COLLECTOR)
        prometheus_core.REGISTRY.unregister(prometheus_client.PROCESS_COLLECTOR)
    except Exception as e:
        LOG.error("Unable to unregister default Prometheus metrics: %s" % e)
    prometheus_core.REGISTRY.register(NetStatsCollector())
    # Start up the server to expose the metrics.
    prometheus_client.start_http_server(options["port"])
    while True:
        time.sleep(60)


if __name__ == "__main__" or __file__ == None:
    main()
