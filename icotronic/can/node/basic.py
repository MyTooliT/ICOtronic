"""Communicate and control an ICOtronic device"""

# -- Imports ------------------------------------------------------------------

from __future__ import annotations

from semantic_version import Version

from icotronic.can.node.eeprom.node import NodeEEPROM
from icotronic.can.node.id import NodeId
from icotronic.can.node.spu import SPU

# -- Classes ------------------------------------------------------------------


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

    async def get_hardware_version(self) -> Version:
        """Retrieve the hardware version of a node

        Returns
        -------

        The hardware version of the node

        Example
        -------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Read the hardware version of STU 1

        >>> async def read_hardware_version():
        ...     async with Connection() as stu:
        ...         return await stu.get_hardware_version()
        >>> hardware_version = run(read_hardware_version())
        >>> hardware_version.major
        1

        """

        node = self.id
        response = await self.spu._request_product_data(
            node=node,
            description=f"read hardware version of node “{node}”",
            block_command="Hardware Version",
        )

        major, minor, patch = response.data[-3:]
        return Version(major=major, minor=minor, patch=patch)

    async def get_firmware_version(self) -> Version:
        """Retrieve the firmware version of the node

        Returns
        -------

        The firmware version of the node

        Example
        -------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Read the firmware version of STU 1

        >>> async def read_firmware_version():
        ...     async with Connection() as stu:
        ...         return await stu.get_firmware_version()
        >>> firmware_version = run(read_firmware_version())
        >>> firmware_version.major
        2

        """

        node = self.id
        response = await self.spu._request_product_data(
            node=node,
            description=f"read firmware version of node “{node}”",
            block_command="Firmware Version",
        )

        major, minor, patch = response.data[-3:]
        return Version(major=major, minor=minor, patch=patch)


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    from doctest import run_docstring_examples

    run_docstring_examples(
        Node.get_firmware_version,
        globals(),
        verbose=True,
    )
