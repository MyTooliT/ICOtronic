"""Support for sensor nodes (SHA, SMH and STH)"""

# pylint: disable=too-many-lines

# -- Imports ------------------------------------------------------------------

from __future__ import annotations

from asyncio import CancelledError
from logging import getLogger
from types import TracebackType
from typing import NamedTuple

from netaddr import EUI

from icotronic.can.constants import (
    ADVERTISEMENT_TIME_EEPROM_TO_MS,
    SENSOR_NODE_NUMBER_SELF_ADDRESSING,
)
from icotronic.can.adc import ADCConfiguration
from icotronic.can.node.eeprom.sensor import SensorNodeEEPROM
from icotronic.can.error import (
    ErrorResponseError,
    NoResponseError,
    UnsupportedFeatureException,
)
from icotronic.can.protocol.message import Message
from icotronic.can.node.basic import Node
from icotronic.can.node.id import NodeId
from icotronic.can.streaming import (
    AsyncStreamBuffer,
    StreamingConfiguration,
    StreamingData,
    StreamingFormat,
    StreamingFormatVoltage,
)
from icotronic.can.node.spu import SPU
from icotronic.config import settings
from icotronic.measurement.sensor import SensorConfiguration
from icotronic.measurement.voltage import convert_raw_to_supply_voltage

# -- Classes ------------------------------------------------------------------


class DataStreamContextManager:
    """Open and close a data stream from a sensor node

    Args:

        sensor_node:
            The sensor node for which this context manager handles
            the streaming data

        channels:
            A streaming configuration that specifies which of the three
            streaming channels should be enabled or not

        timeout
            The amount of seconds between two consecutive messages, before
            a TimeoutError will be raised

    """

    def __init__(
        self,
        sensor_node: SensorNode,
        channels: StreamingConfiguration,
        timeout: float,
    ) -> None:

        self.node = sensor_node
        self.channels = channels
        self.timeout = timeout
        self.reader: AsyncStreamBuffer | None = None
        self.logger = getLogger()
        self.logger.debug("Initialized data stream context manager")

    async def __aenter__(self) -> AsyncStreamBuffer:
        """Open the stream of measurement data

        Returns:

            The stream buffer for the measurement stream

        """

        adc_config = await self.node.get_adc_configuration()
        # Raise exception if there if there is more than one second worth
        # of buffered data
        self.reader = AsyncStreamBuffer(
            self.channels,
            self.timeout,
            max_buffer_size=round(adc_config.sample_rate()),
        )

        self.node.spu.notifier.add_listener(self.reader)
        await self.node.start_streaming_data(self.channels)
        self.logger.debug("Entered data stream context manager")

        return self.reader

    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Clean up the resources used by the stream

        Args:

            exception_type:
                The type of the exception in case of an exception

            exception_value:
                The value of the exception in case of an exception

            traceback:
                The traceback in case of an exception

        """

        if self.reader is not None:
            self.reader.stop()
            self.node.spu.notifier.remove_listener(self.reader)

        if exception_type is None or isinstance(
            exception_type, type(CancelledError)
        ):
            self.logger.info("Stopping stream")
            await self.node.stop_streaming_data()
        else:
            # If there was an error while streaming data, then stoping the
            # stream will usually also fail. Because of this we only try once
            # and ignore any errors.
            #
            # If we did not do that, then the user of the API would be notified
            # about the error to disable the stream, but not about the original
            # error. It would also take considerably more time until the
            # computer would report an error, since the code would usually try
            # to stop the stream (and fail) multiple times beforehand.
            self.logger.info(
                "Stopping stream after error (%s)", exception_type
            )
            await self.node.stop_streaming_data(retries=1, ignore_errors=True)


class Times(NamedTuple):
    """Advertisement time and time until deeper sleep mode"""

    advertisement: float
    """Advertisement time"""

    sleep: int
    """Time until deeper sleep mode"""

    def __repr__(self) -> str:
        """Return a string representation of the object

        Returns:

            A string that contains the advertisement time and sleep time values

        """

        return ", ".join([
            f"Advertisement Time: {self.advertisement} ms",
            f"Sleep Time: {self.sleep} ms",
        ])


class SensorNode(Node):
    """Communicate and control a connected sensor node (SHA, STH, SMH)

    Args:

        spu:
            The SPU object used to connect to this sensor node

        eeprom:
            The EEPROM class of the node

    """

    def __init__(
        self, spu: SPU, eeprom: type[SensorNodeEEPROM] = SensorNodeEEPROM
    ) -> None:

        super().__init__(spu, eeprom, NodeId("STH 1"))

    # ==========
    # = System =
    # ==========

    # -------------
    # - Bluetooth -
    # -------------

    async def get_name(self) -> str:
        """Retrieve the name of the sensor node

        Returns:

            The (Bluetooth broadcast) name of the node

        Examples:

            Import required library code

            >>> from asyncio import run
            >>> from icotronic.can.connection import Connection

            Get Bluetooth advertisement name of node “0”

            >>> async def get_sensor_node_name():
            ...     async with Connection() as stu:
            ...         # We assume that at least one sensor node is available
            ...         async with stu.connect_sensor_node(0) as sensor_node:
            ...             return await sensor_node.get_name()
            >>> name = run(get_sensor_node_name())
            >>> isinstance(name, str)
            True
            >>> 0 <= len(name) <= 8
            True

        """

        return await self.spu.get_name(
            node=self.id, sensor_node_number=SENSOR_NODE_NUMBER_SELF_ADDRESSING
        )

    async def set_name(self, name: str) -> None:
        """Set the name of a sensor node

        Args:

            name:
                The new name for the node

        Examples:

            Import required library code

            >>> from asyncio import run
            >>> from icotronic.can.connection import Connection

            Change the name of a sensor node

            >>> async def test_naming(name):
            ...     async with Connection() as stu:
            ...         # We assume that at least one sensor node is available
            ...         # and that this node currently does not have the name
            ...         # specified in the variable `name`.
            ...         async with stu.connect_sensor_node(0) as sensor_node:
            ...             before = await sensor_node.get_name()
            ...             await sensor_node.set_name(name)
            ...             updated = await sensor_node.get_name()
            ...             await sensor_node.set_name(before)
            ...             after = await sensor_node.get_name()
            ...             return before, updated, after
            >>> before, updated, after = run(test_naming("Hello"))
            >>> before != "Hello"
            True
            >>> updated
            'Hello'
            >>> before == after
            True

        """

        if not isinstance(name, str):
            raise TypeError("Name must be str, not type(identifier).__name__")

        bytes_name = list(name.encode("utf-8"))
        length_name = len(bytes_name)
        if length_name > 8:
            raise ValueError(
                f"Name is too long ({length_name} bytes). "
                "Please use a name between 0 and 8 bytes."
            )

        node = self.id
        # Use 0 bytes at end of names that are shorter than 8 bytes
        bytes_name.extend([0] * (8 - length_name))
        description = f"name of “{node}”"

        await self.spu.request_bluetooth(
            node=node,
            subcommand=3,
            sensor_node_number=SENSOR_NODE_NUMBER_SELF_ADDRESSING,
            data=bytes_name[:6],
            description=f"set first part of {description}",
        )

        await self.spu.request_bluetooth(
            node=node,
            subcommand=4,
            sensor_node_number=SENSOR_NODE_NUMBER_SELF_ADDRESSING,
            data=bytes_name[6:] + [0] * 4,
            description=f"set second part of {description}",
        )

    async def get_rssi(self) -> int:
        """Retrieve the RSSI (Received Signal Strength Indication) of the node

        Returns:

            The RSSI of the node

        Examples:

            Import required library code

            >>> from asyncio import run
            >>> from icotronic.can.connection import Connection

            Get RSSI of node “0”

            >>> async def get_sensor_node_rssi():
            ...     async with Connection() as stu:
            ...         # We assume that at least one sensor node is available
            ...         async with stu.connect_sensor_node(0) as sensor_node:
            ...             return await sensor_node.get_rssi()
            >>> rssi = run(get_sensor_node_rssi())
            >>> -70 < rssi < 0
            True

        """

        return await self.spu.get_rssi(
            self.id, SENSOR_NODE_NUMBER_SELF_ADDRESSING
        )

    async def get_energy_mode_reduced(self) -> Times:
        """Read the reduced energy mode (mode 1) sensor node time values

        See also:

        - https://mytoolit.github.io/Documentation/#sleep-advertisement-times

        Returns:

            A tuple containing the advertisement time in the reduced energy
            mode in milliseconds and the time until the node will switch from
            the disconnected state to the low energy mode (mode 1) – if there
            is no activity – in milliseconds

        Examples:

            Import required library code

            >>> from asyncio import run
            >>> from icotronic.can.connection import Connection

            Retrieve the reduced energy time values of a sensor node

            >>> async def read_energy_mode_reduced():
            ...     async with Connection() as stu:
            ...         # We assume that at least one sensor node is available
            ...         async with stu.connect_sensor_node(0) as sensor_node:
            ...             return await sensor_node.get_energy_mode_reduced()
            >>> times = run(read_energy_mode_reduced())
            >>> round(times.advertisement)
            1250
            >>> times.sleep
            300000

        """

        response = await self.spu.request_bluetooth(
            node=self.id,
            sensor_node_number=SENSOR_NODE_NUMBER_SELF_ADDRESSING,
            subcommand=13,
            description="get reduced energy time values of sensor node",
        )

        wait_time = int.from_bytes(response.data[2:6], byteorder="little")
        advertisement_time = (
            int.from_bytes(response.data[6:], byteorder="little")
            * ADVERTISEMENT_TIME_EEPROM_TO_MS
        )

        return Times(sleep=wait_time, advertisement=advertisement_time)

    async def set_energy_mode_reduced(
        self, times: Times | None = None
    ) -> None:
        """Writes the time values for the reduced energy mode (mode 1)

        See also:

        - https://mytoolit.github.io/Documentation/#sleep-advertisement-times

        Args:

            times:
                The values for the advertisement time in the reduced energy
                mode in milliseconds and the time until the node will go into
                the low energy mode (mode 1) from the disconnected state – if
                there is no activity – in milliseconds.

                If you do not specify these values then the default values
                from the configuration will be used

        Examples:

            Import required library code

            >>> from asyncio import run
            >>> from icotronic.can.connection import Connection

            Read and write the reduced energy time values of a sensor node

            >>> async def read_write_energy_mode_reduced(sleep, advertisement):
            ...     async with Connection() as stu:
            ...         # We assume that at least one sensor node is available
            ...         async with stu.connect_sensor_node(0) as sensor_node:
            ...             await sensor_node.set_energy_mode_reduced(
            ...                 Times(sleep=sleep,
            ...                       advertisement=advertisement))
            ...             times = await sensor_node.get_energy_mode_reduced()
            ...
            ...             # Overwrite changed values with default config
            ...             # values
            ...             await sensor_node.set_energy_mode_reduced()
            ...
            ...             return times
            >>> times = run(read_write_energy_mode_reduced(200_000, 2000))
            >>> times.sleep
            200000
            >>> round(times.advertisement)
            2000

        """

        if times is None:
            time_settings = settings.sensor_node.bluetooth
            times = Times(
                sleep=time_settings.sleep_time_1,
                advertisement=time_settings.advertisement_time_1,
            )

        sleep_time = times.sleep
        advertisement_time = round(
            times.advertisement / ADVERTISEMENT_TIME_EEPROM_TO_MS
        )

        data = list(
            sleep_time.to_bytes(4, "little")
            + advertisement_time.to_bytes(2, "little")
        )

        await self.spu.request_bluetooth(
            node=self.id,
            sensor_node_number=SENSOR_NODE_NUMBER_SELF_ADDRESSING,
            subcommand=14,
            data=data,
            response_data=list(data),
            description="set reduced energy time values of sensor node",
        )

    async def get_energy_mode_lowest(self) -> Times:
        """Read the reduced lowest energy mode (mode 2) time values

        See also:

        - https://mytoolit.github.io/Documentation/#sleep-advertisement-times

        Returns:

            A tuple containing the advertisement time in the lowest energy
            mode in milliseconds and the time until the node will switch from
            the reduced energy mode (mode 1) to the lowest energy mode (mode
            2) – if there is no activity – in milliseconds

        Examples:

            Import required library code

            >>> from asyncio import run
            >>> from icotronic.can.connection import Connection

            Retrieve the reduced energy time values of a sensor node

            >>> async def read_energy_mode_lowest():
            ...     async with Connection() as stu:
            ...         # We assume that at least one sensor node is available
            ...         async with stu.connect_sensor_node(0) as sensor_node:
            ...             return await sensor_node.get_energy_mode_lowest()
            >>> times = run(read_energy_mode_lowest())
            >>> round(times.advertisement)
            2500
            >>> times.sleep
            259200000

        """

        response = await self.spu.request_bluetooth(
            node=self.id,
            sensor_node_number=SENSOR_NODE_NUMBER_SELF_ADDRESSING,
            subcommand=15,
            description="get lowest energy mode time values of sensor node",
        )

        wait_time = int.from_bytes(response.data[2:6], byteorder="little")
        advertisement_time = (
            int.from_bytes(response.data[6:], byteorder="little")
            * ADVERTISEMENT_TIME_EEPROM_TO_MS
        )

        return Times(sleep=wait_time, advertisement=advertisement_time)

    async def set_energy_mode_lowest(self, times: Times | None = None) -> None:
        """Writes the time values for the lowest energy mode (mode 2)

        See also:

        - https://mytoolit.github.io/Documentation/#sleep-advertisement-times

        Args:

            times:
                The values for the advertisement time in the reduced energy
                mode in milliseconds and the time until the node will go into
                the lowest energy mode (mode 2) from the reduced energy mode
                (mode 1) – if there is no activity – in milliseconds.

                If you do not specify these values then the default values
                from the configuration will be used

        Examples:

            Import required library code

            >>> from asyncio import run
            >>> from icotronic.can.connection import Connection

            Read and write the reduced energy time values of a sensor node

            >>> async def read_write_energy_mode_lowest(sleep, advertisement):
            ...     async with Connection() as stu:
            ...         # We assume that at least one sensor node is available
            ...         async with stu.connect_sensor_node(0) as sensor_node:
            ...             await sensor_node.set_energy_mode_lowest(
            ...                 Times(sleep=sleep,
            ...                       advertisement=advertisement))
            ...             times = await sensor_node.get_energy_mode_lowest()
            ...
            ...             # Overwrite changed values with default config
            ...             # values
            ...             await sensor_node.set_energy_mode_lowest()
            ...
            ...             return times
            >>> times = run(read_write_energy_mode_lowest(200_000, 2000))
            >>> times.sleep
            200000
            >>> round(times.advertisement)
            2000

        """

        if times is None:
            time_settings = settings.sensor_node.bluetooth
            times = Times(
                sleep=time_settings.sleep_time_2,
                advertisement=time_settings.advertisement_time_2,
            )

        sleep_time = times.sleep
        advertisement_time = round(
            times.advertisement / ADVERTISEMENT_TIME_EEPROM_TO_MS
        )

        data = list(
            sleep_time.to_bytes(4, "little")
            + advertisement_time.to_bytes(2, "little")
        )

        await self.spu.request_bluetooth(
            node=self.id,
            sensor_node_number=SENSOR_NODE_NUMBER_SELF_ADDRESSING,
            subcommand=16,
            data=data,
            response_data=list(data),
            description="set reduced energy time values of sensor node",
        )

    async def get_mac_address(self) -> EUI:
        """Retrieve the MAC address of the sensor node

        Returns:

            The MAC address of the specified sensor node

        Examples:

            Import required library code

            >>> from asyncio import run
            >>> from icotronic.can.connection import Connection

            Retrieve the MAC address of STH 1

            >>> async def get_bluetooth_mac():
            ...     async with Connection() as stu:
            ...         # We assume that at least one sensor node is available
            ...         async with stu.connect_sensor_node(0) as sensor_node:
            ...             return await sensor_node.get_mac_address()
            >>> mac_address = run(get_bluetooth_mac())
            >>> isinstance(mac_address, EUI)
            True
            >>> mac_address != EUI(0)
            True

        """

        return await self.spu.get_mac_address(
            self.id, SENSOR_NODE_NUMBER_SELF_ADDRESSING
        )

    # =============
    # = Streaming =
    # =============

    # --------
    # - Data -
    # --------

    async def get_streaming_data_single(
        self,
        channels=StreamingConfiguration(first=True, second=True, third=True),
    ) -> StreamingData:
        """Read a single set of raw ADC values from the sensor node

        Args:

            channels:
                Specifies which of the three measurement channels should be
                enabled or disabled

        Returns:

            The latest three ADC values measured by the sensor node

        Examples:

            >>> from asyncio import run
            >>> from icotronic.can.connection import Connection

            Read a single value from all three measurement channels

            >>> async def read_sensor_values():
            ...     async with Connection() as stu:
            ...         # We assume that at least one sensor node is available
            ...         async with stu.connect_sensor_node(0) as sensor_node:
            ...             return (await
            ...                 sensor_node.get_streaming_data_single())
            >>> data = run(read_sensor_values())
            >>> len(data.values)
            3
            >>> all([0 <= value <= 0xffff for value in data.values])
            True

        """

        streaming_format = StreamingFormat(
            channels=channels,
            sets=1,
        )

        node = self.id

        response = await self.spu.request(
            Message(
                block="Streaming",
                block_command="Data",
                sender=self.spu.id,
                receiver=self.id,
                request=True,
                data=[streaming_format.value],
            ),
            description=f"read single set of streaming values from “{node}”",
        )

        values = [
            int.from_bytes(word, byteorder="little")
            for word in (
                response.data[2:4],
                response.data[4:6],
                response.data[6:8],
            )
        ]
        assert len(values) == 2 or len(values) == 3

        data = StreamingData(
            values=values,
            timestamp=response.timestamp,
            counter=response.data[1],
        )

        return data

    async def start_streaming_data(
        self, channels: StreamingConfiguration
    ) -> None:
        """Start streaming data

        Args:

            channels:
                Specifies which of the three measurement channels should be
                enabled or disabled

        The CAN identifier that this coroutine returns can be used
        to filter CAN messages that contain the expected streaming data

        """

        streaming_format = StreamingFormat(
            channels=channels,
            streaming=True,
            sets=3 if channels.enabled_channels() <= 1 else 1,
        )
        node = self.id
        message = Message(
            block="Streaming",
            block_command="Data",
            sender=self.spu.id,
            receiver=node,
            request=True,
            data=[streaming_format.value],
        )

        measurement_channels = [
            channel
            for channel in (
                "first" if channels.first else "",
                "second" if channels.second else "",
                "third" if channels.third else "",
            )
            if channel
        ]
        channels_text = "".join(
            (f"{channel}, " for channel in measurement_channels[:-2])
        ) + " and ".join(measurement_channels[-2:])

        await self.spu.request(
            message,
            description=(
                f"enable streaming of {channels_text} measurement "
                f"channel of “{node}”"
            ),
        )

    async def stop_streaming_data(
        self, retries: int = 10, ignore_errors=False
    ) -> None:
        """Stop streaming data

        Args:

            retries:
                The number of times the message is sent again, if no response
                was sent back in a certain amount of time

            ignore_errors:
                Specifies, if this coroutine should ignore, if there were any
                problems while stopping the stream.

        """

        streaming_format = StreamingFormat(streaming=True, sets=0)
        node = self.id
        message = Message(
            block="Streaming",
            block_command="Data",
            sender=self.spu.id,
            receiver=node,
            request=True,
            data=[streaming_format.value],
        )

        try:

            await self.spu.request(
                message,
                description=f"disable data streaming of “{node}”",
                retries=retries,
            )

        except (NoResponseError, ErrorResponseError) as error:
            if not ignore_errors:
                raise error

    def open_data_stream(
        self,
        channels: StreamingConfiguration,
        timeout: float = 5,
    ) -> DataStreamContextManager:
        """Open measurement data stream

        Args:

            channels:
                Specifies which measurement channels should be enabled

            timeout:
                The amount of seconds between two consecutive messages, before
                a TimeoutError will be raised

        Returns:

            A context manager object for managing stream data

        Examples:

            Import required library code

            >>> from asyncio import run
            >>> from icotronic.can.connection import Connection

            Read data of first and third channel

            >>> async def read_streaming_data():
            ...     async with Connection() as stu:
            ...         # We assume that at least one sensor node is available
            ...         async with stu.connect_sensor_node(0) as sensor_node:
            ...             channels = StreamingConfiguration(first=True,
            ...                                               third=True)
            ...             async with sensor_node.open_data_stream(
            ...               channels) as stream:
            ...                 first = []
            ...                 third = []
            ...                 messages = 0
            ...                 async for data, _ in stream:
            ...                     first.append(data.values[0])
            ...                     third.append(data.values[1])
            ...                     messages += 1
            ...                     if messages >= 3:
            ...                         break
            ...                 return first, third
            >>> first, third = run(read_streaming_data())
            >>> len(first)
            3
            >>> len(third)
            3

        """

        return DataStreamContextManager(self, channels, timeout)

    # -----------
    # - Voltage -
    # -----------

    async def get_supply_voltage(self) -> float:
        """Read the current supply voltage

        Returns:

            The supply voltage of the sensor node

        Examples:

            Import required library code

            >>> from asyncio import run
            >>> from icotronic.can.connection import Connection

            Read the supply voltage of the sensor node with node number 0

            >>> async def get_supply_voltage():
            ...     async with Connection() as stu:
            ...         # We assume that at least one sensor node is available
            ...         async with stu.connect_sensor_node(0) as sensor_node:
            ...             return await sensor_node.get_supply_voltage()
            >>> supply_voltage = run(get_supply_voltage())
            >>> 3 <= supply_voltage <= 4.2
            True

        """

        streaming_format = StreamingFormatVoltage(
            channels=StreamingConfiguration(first=True), sets=1
        )
        node = self.id
        message = Message(
            block="Streaming",
            block_command="Voltage",
            sender=self.spu.id,
            receiver=node,
            request=True,
            data=[streaming_format.value],
        )

        response = await self.spu.request(
            message, description=f"read supply voltage of “{node}”"
        )

        voltage_bytes = response.data[2:4]
        voltage_raw = int.from_bytes(voltage_bytes, "little")

        adc_configuration = await self.get_adc_configuration()

        return convert_raw_to_supply_voltage(
            voltage_raw,
            reference_voltage=adc_configuration.reference_voltage,
        )

    # =================
    # = Configuration =
    # =================

    # -----------------------------
    # - Get/Set ADC Configuration -
    # -----------------------------

    async def get_adc_configuration(self) -> ADCConfiguration:
        """Read the current ADC configuration

        Returns:

            The ADC configuration of the sensor node

        Examples:

            Import required library code

            >>> from asyncio import run
            >>> from icotronic.can.connection import Connection

            Read ADC sensor config of sensor node with node id 0

            >>> async def read_adc_config():
            ...     async with Connection() as stu:
            ...         # We assume that at least one sensor node is available
            ...         async with stu.connect_sensor_node(0) as sensor_node:
            ...             return await sensor_node.get_adc_configuration()
            >>> run(read_adc_config()) # doctest:+NORMALIZE_WHITESPACE
            Get, Prescaler: 2, Acquisition Time: 8, Oversampling Rate: 64,
            Reference Voltage: 3.3 V

        """

        node = self.id

        message = Message(
            block="Configuration",
            block_command="Get/Set ADC Configuration",
            sender=self.spu.id,
            receiver=node,
            request=True,
            data=[0] * 8,
        )

        response = await self.spu.request(
            message, description=f"Read ADC configuration of “{node}”"
        )

        return ADCConfiguration(response.data[0:5])

    async def set_adc_configuration(
        self,
        reference_voltage: float = 3.3,
        prescaler: int = 2,
        acquisition_time: int = 8,
        oversampling_rate: int = 64,
    ) -> None:
        """Change the ADC configuration of a connected sensor node

        Args:

            reference_voltage:
                The ADC reference voltage in Volt
                (1.25, 1.65, 1.8, 2.1, 2.2, 2.5, 2.7, 3.3, 5, 6.6)

            prescaler:
                The ADC prescaler value (1 – 127)

            acquisition_time:
                The ADC acquisition time in number of cycles
                (1, 2, 3, 4, 8, 16, 32, … , 256)

            oversampling_rate:
                The ADC oversampling rate (1, 2, 4, 8, … , 4096)

        Examples:

            Import required library code

            >>> from asyncio import run
            >>> from icotronic.can.connection import Connection

            Read and write ADC sensor config

            >>> async def write_read_adc_config():
            ...     async with Connection() as stu:
            ...         # We assume that at least one sensor node is available
            ...         async with stu.connect_sensor_node(0) as sensor_node:
            ...             await sensor_node.set_adc_configuration(
            ...                 3.3, 8, 8, 64)
            ...             modified_config1 = (await
            ...                 sensor_node.get_adc_configuration())
            ...
            ...             adc_config = ADCConfiguration(
            ...                 reference_voltage=5.0,
            ...                 prescaler=16,
            ...                 acquisition_time=8,
            ...                 oversampling_rate=128)
            ...             await sensor_node.set_adc_configuration(
            ...                 **adc_config)
            ...             modified_config2 = (await
            ...                 sensor_node.get_adc_configuration())
            ...
            ...             # Write back default config values
            ...             await sensor_node.set_adc_configuration(
            ...                 3.3, 2, 8, 64)
            ...             return modified_config1, modified_config2
            >>> config1, config2 = run(write_read_adc_config())
            >>> config1 # doctest:+NORMALIZE_WHITESPACE
            Get, Prescaler: 8, Acquisition Time: 8, Oversampling Rate: 64,
            Reference Voltage: 3.3 V
            >>> config2 # doctest:+NORMALIZE_WHITESPACE
            Get, Prescaler: 16, Acquisition Time: 8, Oversampling Rate: 128,
            Reference Voltage: 5.0 V

        """

        node = self.id
        adc_configuration = ADCConfiguration(
            set=True,
            prescaler=prescaler,
            acquisition_time=acquisition_time,
            oversampling_rate=oversampling_rate,
            reference_voltage=reference_voltage,
        )

        message = Message(
            block="Configuration",
            block_command="Get/Set ADC Configuration",
            sender=self.spu.id,
            receiver=node,
            request=True,
            data=adc_configuration.data,
        )

        await self.spu.request(
            message, description=f"write ADC configuration of “{node}”"
        )

    # --------------------------------
    # - Get/Set Sensor Configuration -
    # --------------------------------

    async def get_sensor_configuration(self) -> SensorConfiguration:
        """Read the current sensor configuration

        Raises:

            UnsupportedFeatureException
                in case the sensor node replies with an error message

        Returns:

            The sensor number for the different axes

        Examples:

            Import required library code

            >>> from asyncio import run
            >>> from icotronic.can.connection import Connection

            Reading sensor config from node without sensor config support fails

            >>> async def read_sensor_config():
            ...     async with Connection() as stu:
            ...         # We assume that at least one sensor node is available
            ...         async with stu.connect_sensor_node(0) as sensor_node:
            ...             return await sensor_node.get_sensor_configuration()
            >>> config = run(
            ...     read_sensor_config()) #doctest: +IGNORE_EXCEPTION_DETAIL
            Traceback (most recent call last):
               ...
            UnsupportedFeatureException: Reading sensor configuration is not
            supported

        """

        node = self.id
        message = Message(
            block="Configuration",
            block_command=0x01,
            sender=self.spu.id,
            receiver=node,
            request=True,
            data=[0] * 8,
        )

        try:

            response = await self.spu.request(
                message, description=f"get sensor configuration of “{node}”"
            )

        except ErrorResponseError as error:
            raise UnsupportedFeatureException(
                "Reading sensor configuration not supported"
            ) from error

        channels = response.data[1:4]

        return SensorConfiguration(*channels)

    async def set_sensor_configuration(
        self, sensors: SensorConfiguration
    ) -> None:
        """Change the sensor numbers for the different measurement channels

        If you use the sensor number `0` for one of the different measurement
        channels, then the sensor (number) for that channel will stay the same.

        Args:

            sensors:
                The sensor numbers of the different measurement channels

        Examples:

            Import required library code

            >>> from asyncio import run
            >>> from icotronic.can.connection import Connection

            Setting sensor config from node without sensor config support fails

            >>> async def set_sensor_config():
            ...     async with Connection() as stu:
            ...         # We assume that at least one sensor node is available
            ...         async with stu.connect_sensor_node(0) as sensor_node:
            ...             await sensor_node.set_sensor_configuration(
            ...                 SensorConfiguration(
            ...                     first=0, second=0, third=0))
            >>> config = run(
            ...     set_sensor_config()) #doctest: +IGNORE_EXCEPTION_DETAIL
            Traceback (most recent call last):
               ...
            UnsupportedFeatureException: Writing sensor configuration is not
            supported

        """

        node = self.id
        data = [
            0b1000_0000,
            sensors.first,
            sensors.second,
            sensors.third,
            *(4 * [0]),
        ]
        message = Message(
            block="Configuration",
            block_command=0x01,
            sender=self.spu.id,
            receiver=node,
            request=True,
            data=data,
        )

        try:

            await self.spu.request(
                message, description=f"set sensor configuration of “{node}”"
            )

        except ErrorResponseError as error:
            raise UnsupportedFeatureException(
                "Writing sensor configuration not supported"
            ) from error


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    from doctest import testmod

    testmod()
