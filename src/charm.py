#!/usr/bin/env python3
# Copyright 2021 Cornellius Metto
# See LICENSE file for licensing details.
#

import logging

from ops.charm import CharmBase
from ops.charm import ConfigChangedEvent
from ops.main import main
from ops.model import ActiveStatus, ModelError
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
        container_name, service_name = "falco", "falco"
        template = template_env.get_template("falco.yaml")
        http_output = self.config["http-output"]
        context = {
            "http_output_enabled": False,
            "http_output_url": ""
        }
        if len(http_output) > 0:
            context["http_output_enabled"] = True
            context["http_output_url"] = http_output
        container = self.unit.get_container(container_name)
        container.push(FALCO_CONFIG_FILE, template.render(context))

        logger.info("Restarting falco...")
        try:
            is_running = container.get_service(service_name).is_running()
            if is_running:
                container.stop(service_name)
                container.start(service_name)
        except (ModelError, RuntimeError):
            logging.info(f"Service '{service_name}' not found in container '{container_name}'")


if __name__ == "__main__":
    main(CharmK8SFalcoCharm)
