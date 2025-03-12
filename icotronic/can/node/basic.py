"""Communicate and control an ICOtronic device"""

# -- Imports ------------------------------------------------------------------

from __future__ import annotations

from icotronic.can.node.eeprom.node import NodeEEPROM
from icotronic.can.node.id import NodeId
from icotronic.can.node.spu import SPU


class Node:
    """Contains functionality shared by STU and sensor devices"""

    def __init__(
        self, spu: SPU, eeprom_class: type[NodeEEPROM], node_id: NodeId
    ) -> None:
        """Initialize the node

        spu:
            The SPU object used to communicate with the device

        eeprom:
            The EEPROM class of the device

        id:
            The node identifier for the device

        """

        self.spu = spu
        self.id = node_id
        self.eeprom = eeprom_class(spu, node_id)
