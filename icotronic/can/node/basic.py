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

    # ================
    # = Product Data =
    # ================

    async def get_gtin(self) -> int:
        """Retrieve the GTIN (Global Trade Identification Number) of the node

        Returns
        -------

        The Global Trade Identification Number

        Example
        -------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Read the GTIN of STU 1

        >>> async def read_gtin():
        ...     async with Connection() as stu:
        ...         return await stu.get_gtin()
        >>> gtin = run(read_gtin())
        >>> isinstance(gtin, int)
        True

        """

        node = self.id
        response = await self.spu._request_product_data(
            node=node,
            description=f"read GTIN of node “{node}”",
            block_command="GTIN",
        )

        return int.from_bytes(response.data, byteorder="little")


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    from doctest import testmod

    testmod()
