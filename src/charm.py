#!/usr/bin/env python3
# Copyright 2021 Cornellius Metto
# See LICENSE file for licensing details.
#

import logging

from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus

logger = logging.getLogger(__name__)


class CharmK8SFalcoCharm(CharmBase):
    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.falco_pebble_ready, self._on_falco_pebble_ready)

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


if __name__ == "__main__":
    main(CharmK8SFalcoCharm)
