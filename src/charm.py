#!/usr/bin/env python3
# Copyright 2021 Cornellius Metto
# See LICENSE file for licensing details.
#

import logging

from ops.charm import ActionEvent, CharmBase
from ops.charm import ConfigChangedEvent
from ops.main import main
from ops.model import ActiveStatus, ModelError
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

TEMPLATES_DIR = "templates"
FALCO_CONFIG_FILE = "/etc/falco/falco.yaml"
template_env = Environment(loader=FileSystemLoader(
    f"{TEMPLATES_DIR}/"), autoescape=select_autoescape())

CONTAINER_NAME, SERVICE_NAME = "falco", "falco"
K8S_AUDIT_RULES_FILE = "/etc/falco/k8s_audit_rules.yaml"


class CharmK8SFalcoCharm(CharmBase):
    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.falco_pebble_ready, self._on_falco_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.show_rules_action, self._on_show_rules_action)

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
        http_output = self.config["http-output"]
        context = {
            "http_output_enabled": False,
            "http_output_url": ""
        }
        if len(http_output) > 0:
            context["http_output_enabled"] = True
            context["http_output_url"] = http_output
        container = self.unit.get_container(CONTAINER_NAME)
        container.push(FALCO_CONFIG_FILE, template.render(context))

        logger.info("Restarting falco...")
        try:
            is_running = container.get_service(SERVICE_NAME).is_running()
            if is_running:
                container.stop(SERVICE_NAME)
                container.start(SERVICE_NAME)
        except (ModelError, RuntimeError):
            logging.info(f"Service '{SERVICE_NAME}' not found in container '{CONTAINER_NAME}'")

    def _on_show_rules_action(self, event: ActionEvent):
        logging.info("show rules action")

        container = self.unit.get_container(CONTAINER_NAME)
        rules = container.pull(K8S_AUDIT_RULES_FILE).read()
        print(rules)


if __name__ == "__main__":
    main(CharmK8SFalcoCharm)
