#!/usr/bin/env python3
# Copyright 2021 Cornellius Metto
# See LICENSE file for licensing details.
#

import logging

from ops.charm import CharmBase
from ops.charm import ConfigChangedEvent
from ops.main import main
from ops.model import ActiveStatus
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

TEMPLATES_DIR = "templates"
FALCO_CONFIG_FILE = "/etc/falco/falco.yaml"
template_env = Environment(loader=FileSystemLoader(
    f"{TEMPLATES_DIR}/"), autoescape=select_autoescape())


class CharmK8SFalcoCharm(CharmBase):
    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.falco_pebble_ready, self._on_falco_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)

    def _on_falco_pebble_ready(self, event):
        """
        Set up the falco container.
        """
        container = event.workload
        pebble_layer = {
            "summary": "falco layer",
            "description": "pebble config layer for falco",
            "services": {
                "falco": {
                    "override": "replace",
                    "summary": "falco",
                    "command": "/falco-trace/bin/falco",
                    "startup": "enabled",
                }
            },
        }

        container.add_layer("falco", pebble_layer, combine=True)
        container.autostart()

        self.unit.status = ActiveStatus()

    def _on_config_changed(self, event: ConfigChangedEvent):
        """
        Update falco's config.
        """
        template = template_env.get_template("falco.yaml")
        container = self.unit.get_container("falco")
        container.push(FALCO_CONFIG_FILE, template.render())


if __name__ == "__main__":
    main(CharmK8SFalcoCharm)
