"""Read and write EEPROM data of ICOtronic devices"""

# -- Imports ------------------------------------------------------------------

from struct import pack, unpack

from semantic_version import Version

from icotronic.can.eeprom.status import EEPROMStatus
from icotronic.can.message import Message
from icotronic.can.node import NodeId
from icotronic.can.spu import SPU
from icotronic.utility.data import convert_bytes_to_text

# -- Classes ------------------------------------------------------------------


class EEPROM:
    """Read and write EEPROM data of ICOtronic devices (STU/sensor devices)"""

    def __init__(self, spu: SPU, node: NodeId) -> None:
        """Create an EEPROM instance using the given arguments

        Parameters
        ----------

        spu:
            A SPU object used to communicate with the ICOtronic system

        node:
            The node identifier of the node that contains the EEPROM

        """

        self.spu = spu
        self.id = node

    # ===========
    # = General =
    # ===========

    async def read(self, address: int, offset: int, length: int) -> list[int]:
        """Read EEPROM data

        Parameters
        ----------

        address:
            The page number in the EEPROM

        offset:
            The offset to the base address in the specified page

        length:
            This value specifies how many bytes you want to read

        Returns
        -------

        A list containing the EEPROM data at the specified location

        Example
        -------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Read EEPROM data from STU 1

        >>> async def read_eeprom():
        ...     async with Connection() as stu:
        ...         return await stu.eeprom.read(address=0, offset=1, length=8)
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

            # pylint: disable=protected-access
            response = await self.spu._request(
                message, description=f"read EEPROM data from “{node}”"
            )
            # pylint: enable=protected-access

            data_end = data_start + read_length
            read_data.extend(response.data[data_start:data_end])
            length -= read_length
            offset += read_length

        return read_data

    async def read_float(self, address: int, offset: int) -> float:
        """Read EEPROM data in float format

        Parameters
        ----------

        address:
            The page number in the EEPROM

        offset:
            The offset to the base address in the specified page

        Returns
        -------

        The float number at the specified location of the EEPROM

        Example
        -------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection
        >>> from icotronic.can.sth import STH

        Read slope of acceleration for x-axis of STH 1

        >>> async def read_slope():
        ...     async with Connection() as stu:
        ...         # We assume that at least one sensor device is available
        ...         async with stu.connect_sensor_device(0, STH) as sth:
        ...             return await sth.eeprom.read_float(address=8, offset=0)
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

        Parameters
        ----------

        address:
            The page number in the EEPROM

        offset:
            The offset to the base address in the specified page

        length:
            This value specifies how long the number is in bytes

        signed:
            Specifies if `value` is a signed number (`True`) or an
            unsigned number (`False`)

        Returns
        -------

        The number at the specified location of the EEPROM

        Example
        -------

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

        Parameters
        ----------

        address:
            The page number in the EEPROM

        offset:
            The offset to the base address in the specified page

        length:
            This value specifies how many characters you want to read

        Returns
        -------

        A string that contains the text at the specified location

        Example
        -------

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

        Parameters
        ----------

        address:
            The page number in the EEPROM

        offset:
            The offset to the base address in the specified page

        data:
            A list of byte value that should be stored at the specified EEPROM
            location

        length:
            This optional parameter specifies how many of the bytes in `data`
            should be stored in the EEPROM. If you specify a length that is
            greater, than the size of the data list, then the remainder of
            the EEPROM data will be filled with null bytes.

        Examples
        --------

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
            # pylint: disable=protected-access
            await self.spu._request(
                message, description=f"write EEPROM data in “{node}”"
            )
            # pylint: enable=protected-access

            data = data[4:]
            offset += write_length

    async def write_float(
        self,
        address: int,
        offset: int,
        value: float,
    ) -> None:
        """Write a float value at the specified EEPROM address

        Parameters
        ----------

        address:
            The page number in the EEPROM

        offset:
            The offset to the base address in the specified page

        value:
            The float value that should be stored at the specified location

        Examples
        --------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Write float value to and read (same) float value from EEPROM of STU 1

        >>> async def write_and_read_float(value):
        ...     async with Connection() as stu:
        ...         await stu.eeprom.write_float(address=10, offset=0,
        ...                                      value=value)
        ...         return await stu.eeprom.read_float(address=10, offset=0)
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

        Parameters
        ----------

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

        Example
        -------

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

        Parameters
        ----------

        address:
            The page number in the EEPROM

        offset:
            The offset to the base address in the specified page

        text:
            An ASCII string that should be written to the specified location

        length:
            This optional parameter specifies how many of the character in
            `text` should be stored in the EEPROM. If you specify a length
            that is greater than the size of the data list, then the
            remainder of the EEPROM data will be filled with null bytes.

        Examples
        --------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Write text to and read (same) text from EEPROM of STU 1

        >>> async def write_and_read_text(text):
        ...     async with Connection() as stu:
        ...         await stu.eeprom.write_text(address=10, offset=11,
        ...                                     text=text, length=len(text))
        ...         return await stu.eeprom.read_text(address=10, offset=11,
        ...                                           length=len(text))
        >>> run(write_and_read_text("something"))
        'something'

        """

        data = list(map(ord, list(text)))
        await self.write(address, offset, data, length)

    # ========================
    # = System Configuration =
    # ========================

    async def read_status(self) -> EEPROMStatus:
        """Retrieve EEPROM status byte

        Returns
        -------

        An EEPROM status object for the current status byte value

        Example
        -------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Read the status byte of STU 1

        >>> async def read_status_byte():
        ...     async with Connection() as stu:
        ...         return await stu.eeprom.read_status()
        >>> isinstance(run(read_status_byte()), EEPROMStatus)
        True

        """

        return EEPROMStatus(
            (await self.read(address=0, offset=0, length=1)).pop()
        )

    async def write_status(self, value: int | EEPROMStatus) -> None:
        """Change the value of the EEPROM status byte

        Parameters
        ----------

        value:
            The new value for the status byte


        Example
        -------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Write and read the status byte of STU 1

        >>> async def write_read_status_byte():
        ...     async with Connection() as stu:
        ...         await stu.eeprom.write_status(EEPROMStatus('Initialized'))
        ...         return await stu.eeprom.read_status()
        >>> status = run(write_read_status_byte())
        >>> status.is_initialized()
        True

        """

        await self.write_int(
            address=0, offset=0, length=1, value=EEPROMStatus(value).value
        )

    async def read_name(self) -> str:
        """Retrieve the name of the node from the EEPROM

        Returns
        -------

        The name of the node

        Examples
        --------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Read the name of STU 1

        >>> async def read_name():
        ...     async with Connection() as stu:
        ...         return await stu.eeprom.read_name()
        >>> isinstance(run(read_name()), str)
        True

        """

        return await self.read_text(address=0, offset=1, length=8)

    async def write_name(self, name: str) -> None:
        """Write the name of the node into the EEPROM

        Parameters
        ----------

        name:
            The new (Bluetooth advertisement) name of the node

        Examples
        --------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Write and read the name of STU 1

        >>> async def write_read_name(name):
        ...     async with Connection() as stu:
        ...         await stu.eeprom.write_name(name)
        ...         return await stu.eeprom.read_name()
        >>> run(write_read_name('Valerie'))
        'Valerie'

        """

        await self.write_text(address=0, offset=1, text=name, length=8)

    # ================
    # = Product Data =
    # ================

    async def read_gtin(self) -> int:
        """Read the global trade identifier number (GTIN) from the EEPROM

        Returns
        -------

        The GTIN of the specified node

        Examples
        --------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Read the GTIN of STU 1

        >>> async def read_gtin():
        ...     async with Connection() as stu:
        ...         return await stu.eeprom.read_gtin()
        >>> gtin = run(read_gtin())
        >>> isinstance(gtin, int)
        True

        """

        return await self.read_int(address=4, offset=0, length=8)

    async def write_gtin(self, gtin: int) -> None:
        """Write the global trade identifier number (GTIN) to the EEPROM

        Parameters
        ----------

        gtin:
            The new GTIN of the specified receiver

        Examples
        --------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Write and read the GTIN of STU 1

        >>> async def write_read_gtin(gtin):
        ...     async with Connection() as stu:
        ...         await stu.eeprom.write_gtin(gtin=gtin)
        ...         return await stu.eeprom.read_gtin()
        >>> run(write_read_gtin(0))
        0

        """

        await self.write_int(address=4, offset=0, length=8, value=gtin)

    async def read_hardware_version(self) -> Version:
        """Read the current hardware version from the EEPROM

        Returns
        -------

        The hardware version of the device

        Example
        -------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Read the hardware version of STU 1

        >>> async def read_hardware_version():
        ...     async with Connection() as stu:
        ...         return (await stu.eeprom.read_hardware_version())
        >>> hardware_version = run(read_hardware_version())
        >>> hardware_version.major >= 1
        True

        """

        major, minor, patch = await self.read(address=4, offset=13, length=3)
        return Version(major=major, minor=minor, patch=patch)

    async def write_hardware_version(self, version: str | Version):
        """Write hardware version to the EEPROM

        Parameters
        ----------

        version:
            The new hardware version of the device

        Examples
        --------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Write and read the hardware version of STU 1

        >>> async def write_read_hardware_version(version):
        ...     async with Connection() as stu:
        ...         await stu.eeprom.write_hardware_version(version=version)
        ...         return (await stu.eeprom.read_hardware_version())
        >>> hardware_version = run(write_read_hardware_version('1.3.2'))
        >>> hardware_version.patch == 2
        True

        """

        if isinstance(version, str):
            version = Version(version)

        await self.write(
            address=4,
            offset=13,
            length=3,
            data=[version.major, version.minor, version.patch],
        )

    async def read_firmware_version(self) -> Version:
        """Retrieve the current firmware version from the EEPROM

        Returns
        -------

        The firmware version of the device

        Example
        -------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Read the firmware version of STU 1

        >>> async def read_firmware_version():
        ...     async with Connection() as stu:
        ...         return await stu.eeprom.read_firmware_version()
        >>> firmware_version = run(read_firmware_version())
        >>> firmware_version.major >= 2
        True

        """

        major, minor, patch = await self.read(address=4, offset=21, length=3)
        return Version(major=major, minor=minor, patch=patch)

    async def write_firmware_version(self, version: str | Version) -> None:
        """Write firmware version to the EEPROM

        Parameters
        ----------

        version:
            The new firmware version

        Example
        -------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Write and read the firmware version of STU 1

        >>> async def write_read_firmware_version(version):
        ...     async with Connection() as stu:
        ...         await stu.eeprom.write_firmware_version(version)
        ...         return (await stu.eeprom.read_firmware_version())
        >>> version = '2.1.10'
        >>> firmware_version = run(write_read_firmware_version(version))
        >>> firmware_version == Version(version)
        True

        """

        if isinstance(version, str):
            version = Version(version)

        await self.write(
            address=4,
            offset=21,
            length=3,
            data=[version.major, version.minor, version.patch],
        )

    async def read_release_name(self) -> str:
        """Retrieve the current release name from the EEPROM

        Returns
        -------

        The firmware release name of the specified node

        Example
        -------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Read the release name of STU 1

        >>> async def read_release_name():
        ...     async with Connection() as stu:
        ...         return await stu.eeprom.read_release_name()
        >>> run(read_release_name())
        'Valerie'

        """

        return await self.read_text(address=4, offset=24, length=8)


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    from doctest import run_docstring_examples

    run_docstring_examples(
        EEPROM.read_release_name,
        globals(),
        verbose=True,
    )
