
# ps_net_stats
This script is designed to query multiple PowerScale clusters for network interface statistics. It reports on the network statistics gathered from a netstat -i on each cluster. This information can be used in a dashboard to display the network statistics on each node in a cluster. The script utilizes an SSH client to execute the netstat -i command on the remote cluster. It is assumed that the user defined in the configuration file already has SSH passwordless login configured and working.

This script currently only supports providing data to a Prometheus database.

## Installation

### Dependencies
The following Python libraries are required for this script to run:
 - pyyaml

### Configuration
The script requires a YAML file with user and endpoint settings. The configuration file can contain multiple clusters to monitor and each cluster has its own settings. The YAML file should have the following format:

    ---
    - cluster:
        user: "<user_name>"
        endpoint: "<endpoint>"
    - cluster:
        user: "net_poll_user"
        endpoint: "192.168.200.50:8080"

An example configuration can be found in the file: **example_config.yml**

The script listens on port 8000 by default. This can be changed with a CLI option (--port) or by setting the environment variable PS_NET_STATS_PORT to the desired value.

The user specified in the YAML file needs to have sudo privileges for a specific command or be the root user. The script requires the use of isi_for_array which itself requires root privileges to execute.

An example line in the sudoers file that properly sets permissions is as follows:
<user_name> ALL=(root) NOPASSWD: /usr/bin/isi_for_array -sX netstat -iW

The sudoers file on a cluster can be manually edited by running the **visudo** command.

Help and other options for the script can be found by running the script with the *--help* option.

## Execution

### Create RBAC user and role on clusters
The user specified in the config file needs to have permissions to login to a cluster over SSH. This requires the user to have the ISI_PRIV_LOGIN_SSH privilege. The example below creates a new user, a new role, and then assigns the user to the role.

    isi auth users create ps_net_stats --enabled=true --set-password
    isi auth roles create --name=net_stats_poll --zone=system
    isi auth roles modify net_stats_poll --add-priv-read=ISI_PRIV_LOGIN_SSH --add-user=ps_net_stats

Create a YAML configuration file that contains the user and endpoint information for each of the clusters you wish to monitor. The file **example_config.yml** can be used as an example template.

### Run the script
    (nohup python3 ps_net_stats.py --config=config.yml &)

As an alternative, a PYZ release of the code is also available which bundles all the script files required. This method may be more portable and easier to use.

    (nohup python3 ps_net_stats.pyz --config=config.yml &)

### Verifying operation
After starting the script, a web browser can be used to validate that the script is performing properly. Navigate to the IP address or use localhost and the port number to get a page with the collected statistics. An example output follows.

    # HELP isilon_net_stats_ipkts_total Number of packets received
    # TYPE isilon_net_stats_ipkts_total counter
    isilon_net_stats_ipkts_total{cluster_name="cluster",interface_name="em0",node_lnn="1"} 1.9669882e+07
    # HELP isilon_net_stats_ierrs_total Number of input errors
    # TYPE isilon_net_stats_ierrs_total counter
    isilon_net_stats_ierrs_total{cluster_name="cluster",interface_name="em0",node_lnn="1"} 0.0
    # HELP isilon_net_stats_idrop_total Number of dropped input packets
    # TYPE isilon_net_stats_idrop_total counter
    isilon_net_stats_idrop_total{cluster_name="cluster",interface_name="em0",node_lnn="1"} 0.0
    # HELP isilon_net_stats_opkts_total Number of packets sent
    # TYPE isilon_net_stats_opkts_total counter
    isilon_net_stats_opkts_total{cluster_name="cluster",interface_name="em0",node_lnn="1"} 2.909963e+06
    # HELP isilon_net_stats_oerrs_total Number of output errors
    # TYPE isilon_net_stats_oerrs_total counter
    isilon_net_stats_oerrs_total{cluster_name="cluster",interface_name="em0",node_lnn="1"} 0.0
    # HELP isilon_net_stats_coll_total Number of packet collisions
    # TYPE isilon_net_stats_coll_total counter
    isilon_net_stats_coll_total{cluster_name="cluster",interface_name="em0",node_lnn="1"} 0.0
    # HELP isilon_net_stats_ipkts_total Number of packets received
    # TYPE isilon_net_stats_ipkts_total counter
    isilon_net_stats_ipkts_total{cluster_name="cluster",interface_name="em1",node_lnn="1"} 2.3251657e+07
    # HELP isilon_net_stats_ierrs_total Number of input errors
    # TYPE isilon_net_stats_ierrs_total counter
    isilon_net_stats_ierrs_total{cluster_name="cluster",interface_name="em1",node_lnn="1"} 0.0
    # HELP isilon_net_stats_idrop_total Number of dropped input packets
    # TYPE isilon_net_stats_idrop_total counter
    isilon_net_stats_idrop_total{cluster_name="cluster",interface_name="em1",node_lnn="1"} 0.0
    # HELP isilon_net_stats_opkts_total Number of packets sent
    # TYPE isilon_net_stats_opkts_total counter
    isilon_net_stats_opkts_total{cluster_name="cluster",interface_name="em1",node_lnn="1"} 2.006008e+06
    # HELP isilon_net_stats_oerrs_total Number of output errors
    # TYPE isilon_net_stats_oerrs_total counter
    isilon_net_stats_oerrs_total{cluster_name="cluster",interface_name="em1",node_lnn="1"} 0.0
    # HELP isilon_net_stats_coll_total Number of packet collisions
    # TYPE isilon_net_stats_coll_total counter
    isilon_net_stats_coll_total{cluster_name="cluster",interface_name="em1",node_lnn="1"} 0.0
    # HELP isilon_net_stats_ipkts_total Number of packets received
    # TYPE isilon_net_stats_ipkts_total counter
    isilon_net_stats_ipkts_total{cluster_name="cluster",interface_name="em2",node_lnn="1"} 2.0336892e+07
    # HELP isilon_net_stats_ierrs_total Number of input errors
    # TYPE isilon_net_stats_ierrs_total counter
    isilon_net_stats_ierrs_total{cluster_name="cluster",interface_name="em2",node_lnn="1"} 0.0
    # HELP isilon_net_stats_idrop_total Number of dropped input packets
    # TYPE isilon_net_stats_idrop_total counter
    isilon_net_stats_idrop_total{cluster_name="cluster",interface_name="em2",node_lnn="1"} 0.0
    # HELP isilon_net_stats_opkts_total Number of packets sent
    # TYPE isilon_net_stats_opkts_total counter
    isilon_net_stats_opkts_total{cluster_name="cluster",interface_name="em2",node_lnn="1"} 2.909961e+06
    # HELP isilon_net_stats_oerrs_total Number of output errors
    # TYPE isilon_net_stats_oerrs_total counter
    isilon_net_stats_oerrs_total{cluster_name="cluster",interface_name="em2",node_lnn="1"} 0.0
    # HELP isilon_net_stats_coll_total Number of packet collisions
    # TYPE isilon_net_stats_coll_total counter
    isilon_net_stats_coll_total{cluster_name="cluster",interface_name="em2",node_lnn="1"} 0.0

### Performance
The default polling interval for Prometheus is 15 seconds. The script uses SSH to gather the network statistics and there is some overhead to gather all the network statistics. Thus a larger polling interval is suggested. An interval of 5 minutes may be a reasonable compromise between low overhead and having current information. 

## Data format
The script sends 6 counter metrics for each interface on each node to Prometheus. Each attribute includes labels for the following fields:

 - Cluster name (cluster_name)
 - Network interface name (interface_name)
 - Node logical node number (node_lnn)

The 6 metrics with values are:
 - isilon_net_stats_ipkts_total (Total number of packets received on the interface)
 - isilon_net_stats_ierrs_total (Total number of input errors, e.g. malformed packets, checksum errors, or insufficient buffer space)
 - isilon_net_stats_idrop_total (Total number of dropped incoming packets)
 - isilon_net_stats_opkts_total (Total number of packets sent on the interface)
 - isilon_net_stats_oerrs_total (Total number of output errors, e.g. insufficient buffer space)
 - isilon_net_stats_coll_total (Total number of packet collisions)

## Security
The script connects to a PowerScale cluster over SSH. SSH passwordless login is required as is the ability to execute the isi_for_array command on the cluster. If the user being used to connect to the cluster is not root, then an entry in the sudoers file is required.

The user connecting to the cluster needs only the following RBAC privileges:
Read - ISI_PRIV_LOGIN_SSH (Required to connect via SSH)

## Issues, bug reports, and suggestions
For any issues with the script, please re-run the script with debug enabled (--debug command line option) and open an issue with the debug output and description of the problem.
