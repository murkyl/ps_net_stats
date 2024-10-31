VER:=$(shell grep __version__ ps_net_stats/ps_net_stats.py | head -n 1 | sed -E 's/.*"(.*)"/\1/')
all: ps_net_stats_release

ps_net_stats: clean
	mkdir -p build
	mkdir -p dist
	cd ps_net_stats; zip -r ../build/ps_net_stats.pyz *
	zip -r build/ps_net_stats.pyz *.md
	echo '#!/usr/bin/env python3' | cat - build/ps_net_stats.pyz > dist/ps_net_stats.pyz
	chmod a+x dist/ps_net_stats.pyz

ps_net_stats_release: ps_net_stats
	mkdir -p releases
	cp dist/ps_net_stats.pyz releases/
	cp dist/ps_net_stats.pyz releases/ps_net_stats-$(VER).pyz

.PHONY: clean
clean: clean_compiled
	-rm -rf build
	-rm -rf dist
	-rm -rf *.egg-info

.PHONY: clean_compiled
clean_compiled:
	find . -name __pycache__ -type d -exec rm -rf {} +
	find . -name *.pyc -delete

.PHONY: clean_releases
clean_releases:
	-rm -rf releases

.PHONY: format
format:
	find . -name \*.py -exec black {} +