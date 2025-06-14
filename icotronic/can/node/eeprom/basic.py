"""Basic EEPROM support for ICOtronic nodes"""

# -- Imports ------------------------------------------------------------------

from struct import pack, unpack

from icotronic.can.protocol.message import Message
from icotronic.can.node.id import NodeId
from icotronic.can.node.spu import SPU
from icotronic.utility.data import convert_bytes_to_text

# -- Classes ------------------------------------------------------------------


class EEPROM:
    """Read and write EEPROM data of ICOtronic nodes

    Args:

        spu:
            A SPU object used to communicate with the ICOtronic system

        node:
            The node identifier of the node that contains the EEPROM

    """

    def __init__(self, spu: SPU, node: NodeId) -> None:

        self.spu = spu
        self.id = node

    async def read(self, address: int, offset: int, length: int) -> list[int]:
        """Read EEPROM data

        Args:

            address:
                The page number in the EEPROM

            offset:
                The offset to the base address in the specified page

            length:
                This value specifies how many bytes you want to read

        Returns:

            A list containing the EEPROM data at the specified location

        Examples:

            Import required library code

            >>> from asyncio import run
            >>> from icotronic.can.connection import Connection

            Read EEPROM data from STU 1

            >>> async def read_eeprom():
            ...     async with Connection() as stu:
            ...         return await stu.eeprom.read(
            ...             address=0, offset=1, length=8)
            >>> data = run(read_eeprom())
            >>> len(data)
            8
            >>> all((0 <= byte <= 255 for byte in data))
            True

        """

        read_data: list[int] = []
        reserved = [0] * 5
        data_start = 4  # Start index of data in response message

        node = self.id
        while length > 0:
            # Read at most 4 bytes of data at once
            read_length = 4 if length > 4 else length
            message = Message(
                block="EEPROM",
                block_command="Read",
                sender=self.spu.id,
                receiver=node,
                request=True,
                data=[address, offset, read_length, *reserved],
            )

            response = await self.spu.request(
                message, description=f"read EEPROM data from “{node}”"
            )

            data_end = data_start + read_length
            read_data.extend(response.data[data_start:data_end])
            length -= read_length
            offset += read_length

        return read_data

    async def read_float(self, address: int, offset: int) -> float:
        """Read EEPROM data in float format

        Args:

            address:
                The page number in the EEPROM

            offset:
                The offset to the base address in the specified page

        Returns:

            The float number at the specified location of the EEPROM

        Examples:

            Import required library code

            >>> from asyncio import run
            >>> from icotronic.can.connection import Connection
            >>> from icotronic.can.node.sth import STH

            Read slope of acceleration for x-axis of STH 1

            >>> async def read_slope():
            ...     async with Connection() as stu:
            ...         # We assume that at least one sensor node is available
            ...         async with stu.connect_sensor_node(0, STH) as sth:
            ...             return await sth.eeprom.read_float(
            ...                 address=8, offset=0)
            >>> slope = run(read_slope())
            >>> isinstance(slope, float)
            True

        """

        data = await self.read(address, offset, length=4)
        return unpack("<f", bytearray(data))[0]

    async def read_int(
        self,
        address: int,
        offset: int,
        length: int,
        signed: bool = False,
    ) -> int:
        """Read an integer value from the EEPROM

        Args:

            address:
                The page number in the EEPROM

            offset:
                The offset to the base address in the specified page

            length:
                This value specifies how long the number is in bytes

            signed:
                Specifies if `value` is a signed number (`True`) or an
                unsigned number (`False`)

        Returns:

            The number at the specified location of the EEPROM

        Examples:

            Import required library code

            >>> from asyncio import run
            >>> from icotronic.can.connection import Connection

            Read the operating time (in seconds) of STU 1

            >>> async def read_operating_time():
            ...     async with Connection() as stu:
            ...         return await stu.eeprom.read_int(address=5, offset=8,
            ...                                          length=4)
            >>> operating_time = run(read_operating_time())
            >>> operating_time >= 0
            True

        """

        return int.from_bytes(
            await self.read(address, offset, length),
            "little",
            signed=signed,
        )

    async def read_text(self, address: int, offset: int, length: int) -> str:
        """Read EEPROM data in ASCII format

        Please note, that this function will only return the characters up
        to the first null byte.

        Args:

            address:
                The page number in the EEPROM

            offset:
                The offset to the base address in the specified page

            length:
                This value specifies how many characters you want to read

        Returns:

            A string that contains the text at the specified location

        Examples:

            Import required library code

            >>> from asyncio import run
            >>> from icotronic.can.connection import Connection

            Read name of STU 1

            >>> async def read_name_eeprom():
            ...     async with Connection() as stu:
            ...         return await stu.eeprom.read_text(address=0, offset=1,
            ...                                           length=8)
            >>> name = run(read_name_eeprom())
            >>> 0 <= len(name) <= 8
            True
            >>> isinstance(name, str)
            True

        """

        data = await self.read(address, offset, length)
        return convert_bytes_to_text(data, until_null=True)

    async def write(
        self,
        address: int,
        offset: int,
        data: list[int],
        length: int | None = None,
    ) -> None:
        """Write EEPROM data at the specified address

        Args:

            address:
                The page number in the EEPROM

            offset:
                The offset to the base address in the specified page

            data:
                A list of byte value that should be stored at the specified
                EEPROM location

            length:
                This optional parameter specifies how many of the bytes in
                ``data`` should be stored in the EEPROM. If you specify a
                length that is greater, than the size of the data list, then
                the remainder of the EEPROM data will be filled with null
                bytes.

        Examples:

            Import required library code

            >>> from asyncio import run
            >>> from icotronic.can.connection import Connection

            Write data to and read (same) data from EEPROM of STU 1

            >>> async def write_and_read_eeprom(data):
            ...     async with Connection() as stu:
            ...         await stu.eeprom.write(address=10, offset=3, data=data)
            ...         return await stu.eeprom.read(address=10, offset=3,
            ...                                      length=len(data))
            >>> data = [1, 3, 3, 7]
            >>> read_data = run(write_and_read_eeprom(data))
            >>> data == read_data
            True

        """

        # Change data, if
        # - only a subset, or
        # - additional data
        # should be written to the EEPROM.
        if length is not None:
            # Cut off additional data bytes
            data = data[:length]
            # Fill up additional data bytes
            data.extend([0] * (length - len(data)))

        node = self.id

        while data:
            write_data = data[:4]  # Maximum of 4 bytes per message
            write_length = len(write_data)
            # Use zeroes to fill up missing data bytes
            write_data.extend([0] * (4 - write_length))

            reserved = [0] * 1
            message = Message(
                block="EEPROM",
                block_command="Write",
                sender=self.spu.id,
                receiver=node,
                request=True,
                data=[address, offset, write_length, *reserved, *write_data],
            )

            await self.spu.request(
                message, description=f"write EEPROM data in “{node}”"
            )

            data = data[4:]
            offset += write_length

    async def write_float(
        self,
        address: int,
        offset: int,
        value: float,
    ) -> None:
        """Write a float value at the specified EEPROM address

        Args:

            address:
                The page number in the EEPROM

            offset:
                The offset to the base address in the specified page

            value:
                The float value that should be stored at the specified location

        Examples:

            Import required library code

            >>> from asyncio import run
            >>> from icotronic.can.connection import Connection

            Write float value to and read (same) value from EEPROM of STU 1

            >>> async def write_and_read_float(value):
            ...     async with Connection() as stu:
            ...         await stu.eeprom.write_float(address=10, offset=0,
            ...                                      value=value)
            ...         return await stu.eeprom.read_float(
            ...             address=10, offset=0)
            >>> value = 42.5
            >>> read_value = run(write_and_read_float(value))
            >>> value == read_value
            True

        """

        data = list(pack("f", value))
        await self.write(address, offset, data)

    # pylint: disable=too-many-arguments, too-many-positional-arguments

    async def write_int(
        self,
        address: int,
        offset: int,
        value: int,
        length: int,
        signed: bool = False,
    ) -> None:
        """Write an integer number at the specified EEPROM address

        Args:

            address:
                The page number in the EEPROM

            offset:
                The offset to the base address in the specified page

            value:
                The number that should be stored at the specified location

            length:
                This value specifies how long the number is in bytes

            signed:
                Specifies if `value` is a signed number (`True`) or an
                unsigned number (`False`)

        Examples:

            Import required library code

            >>> from asyncio import run
            >>> from icotronic.can.connection import Connection

            Write int value to and read (same) int value from EEPROM of STU 1

            >>> async def write_and_read_int(value):
            ...     async with Connection() as stu:
            ...         await stu.eeprom.write_int(address=10, offset=0,
            ...             value=value, length=8, signed=True)
            ...         return await stu.eeprom.read_int(address=10, offset=0,
            ...                 length=8, signed=True)
            >>> value = -1337
            >>> read_value = run(write_and_read_int(value))
            >>> value == read_value
            True

        """

        data = list(value.to_bytes(length, byteorder="little", signed=signed))
        await self.write(address, offset, data)

    # pylint: enable=too-many-arguments, too-many-positional-arguments

    async def write_text(
        self,
        address: int,
        offset: int,
        text: str,
        length: int,
    ) -> None:
        """Write a string at the specified EEPROM address

        Args:

            address:
                The page number in the EEPROM

            offset:
                The offset to the base address in the specified page

            text:
                An ASCII string that should be written to the specified
                location

            length:
                This optional parameter specifies how many of the character in
                ``text`` should be stored in the EEPROM. If you specify a
                length that is greater than the size of the data list, then
                the remainder of the EEPROM data will be filled with null
                bytes.

        Examples:

            Import required library code

            >>> from asyncio import run
            >>> from icotronic.can.connection import Connection

            Write text to and read (same) text from EEPROM of STU 1

            >>> async def write_and_read_text(text):
            ...     async with Connection() as stu:
            ...         await stu.eeprom.write_text(address=10,
            ...                                     offset=11,
            ...                                     text=text,
            ...                                     length=len(text))
            ...         return await stu.eeprom.read_text(
            ...             address=10, offset=11, length=len(text))
            >>> run(write_and_read_text("something"))
            'something'

        """

        data = list(map(ord, list(text)))
        await self.write(address, offset, data, length)


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    from doctest import testmod

    testmod()
