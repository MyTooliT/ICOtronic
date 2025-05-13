"""Communicate with the ICOtronic system"""

# -- Imports ------------------------------------------------------------------

from __future__ import annotations

from asyncio import wait_for
from logging import getLogger

from can import BusABC, Message as CANMessage, Notifier
from netaddr import EUI

from icotronic.can.protocol.message import Message
from icotronic.can.error import ErrorResponseError, NoResponseError
from icotronic.can.listener import ResponseListener
from icotronic.can.node.id import NodeId
from icotronic.utility.data import convert_bytes_to_text

# -- Classes ------------------------------------------------------------------


class SPU:
    """Communicate with the ICOtronic system acting as SPU"""

    def __init__(self, bus: BusABC, notifier: Notifier) -> None:
        """Create an SPU instance using the given arguments

        Parameters
        ----------

        bus:
            A CAN bus object used to communicate with the STU

        notifier:
            A notifier class that listens to the communication of `bus`

        """

        self.bus = bus
        self.notifier = notifier
        self.id = NodeId("SPU 1")

    # pylint: disable=too-many-arguments, too-many-positional-arguments

    async def request(
        self,
        message: Message,
        description: str,
        response_data: bytearray | list[int | None] | None = None,
        minimum_timeout: float = 0,
        retries: int = 10,
    ) -> CANMessage:
        """Send a request message and wait for the response

        Parameters
        ----------

        message:
            The message containing the request

        description:
            A description of the request used in error messages

        response_data:
           Specifies the expected data in the acknowledgment message

        minimum_timeout:
           Minimum time before attempting additional connection attempt
           in seconds

        retries:
           The number of times the message is sent again, if no response was
           sent back in a certain amount of time

        Returns
        -------

        The response message for the given request

        Raises
        ------

        NoResponseError:
            If the receiver did not respond to the message after retries
            amount of messages sent

        ErrorResponseError:
            If the receiver answered with an error message

        """

        logger = getLogger()
        logger.debug("Send request to %s", description)

        for attempt in range(retries):
            listener = ResponseListener(message, response_data)
            self.notifier.add_listener(listener)
            getLogger("icotronic.can").debug("%s", message)
            self.bus.send(message.to_python_can())

            try:
                # We increase the timeout after the first and second try.
                # This way we reduce the chance of the warning:
                #
                # - “Bus error: an error counter reached the 'heavy'/'warning'
                #   limit”
                #
                # happening. This warning might show up after
                #
                # - we flashed the STU,
                # - sent a reset command to the STU, and then
                # - wait for the response of the STU.
                timeout = max(min(attempt * 0.1 + 0.5, 2), minimum_timeout)
                response = await wait_for(
                    listener.on_message(), timeout=timeout
                )
                assert response is not None
            except TimeoutError:
                continue
            finally:
                listener.stop()
                self.notifier.remove_listener(listener)

            if response.is_error:
                raise ErrorResponseError(
                    "Received unexpected response for request to "
                    f"{description}:\n\n{response.error_message}\n"
                    f"Response Message: {Message(response.message)}"
                )

            logger.debug("Retrieved answer for request to %s", description)
            return response.message

        raise NoResponseError(f"Unable to {description}")

    async def request_bluetooth(
        self,
        node: str | NodeId,
        subcommand: int,
        description: str,
        device_number: int | None = None,
        data: list[int] | None = None,
        response_data: list[int | None] | None = None,
    ) -> CANMessage:
        """Send a request for a certain Bluetooth command

        Parameters
        ----------

        node:
            The node on which the Bluetooth command should be executed

        subcommand:
            The number of the Bluetooth subcommand

        device_number:
            The device number of the Bluetooth device

        description:
            A description of the request used in error messages

        data:
            An optional list of bytes that should be included in the request

        response_data:
            An optional list of expected data bytes in the response message

        Returns
        -------

        The response message for the given request

        """

        device_number = 0 if device_number is None else device_number
        data = [0] * 6 if data is None else data
        message = Message(
            block="System",
            block_command="Bluetooth",
            sender=self.id,
            receiver=node,
            request=True,
            data=[subcommand, device_number] + data,
        )

        # The Bluetooth subcommand and device number should be the same in the
        # response message.
        #
        # Unfortunately the device number is currently not the same for:
        #
        # - the subcommand that sets the second part of the name, and
        # - the subcommand that retrieves the MAC address
        # - the subcommand that writes the time values for the reduced energy
        #   mode
        #
        # The subcommand number in the response message for the commands to
        # set the time values for
        #
        # - the reduced energy mode and
        # - the lowest energy mode
        #
        # are unfortunately also not correct.
        set_second_part_name = 4
        set_times_reduced_energy = 14
        set_times_reduced_lowest = 16
        get_mac_address = 17
        expected_data: list[int | None]
        if subcommand in {get_mac_address, set_second_part_name}:
            expected_data = [subcommand, None]
        elif subcommand in {
            set_times_reduced_energy,
            set_times_reduced_lowest,
        }:
            expected_data = [None, None]
        else:
            expected_data = [subcommand, device_number]

        if response_data is not None:
            expected_data.extend(response_data)

        return await self.request(
            message, description=description, response_data=expected_data
        )

    async def request_product_data(
        self,
        block_command: str | int,
        description: str,
        node: str | NodeId,
    ) -> CANMessage:
        """Send a request for product data

        Parameters
        ----------

        node:
            The node on which the block command should be executed

        block_command:
            The name or number of the block command

        description:
            A description of the request used in error messages

        Returns
        -------

        The response message for the given request

        """

        message = Message(
            block="Product Data",
            block_command=block_command,
            sender=self.id,
            receiver=node,
            request=True,
            data=[0] * 8,
        )

        return await self.request(message, description=description)

    # pylint: enable=too-many-arguments, too-many-positional-arguments

    async def get_name(
        self, node: str | NodeId = "STU 1", device_number: int = 0xFF
    ) -> str:
        """Retrieve the name of a Bluetooth device

        You can use this method to name of both

        1. disconnected and
        2. connected

        devices.

        1. For disconnected sensor devices you will usually use the STU (e.g.
           `STU 1`) and the device number at the STU (in the range `0` up to
           the number of devices - 1) to retrieve the name.

        2. For connected devices you will use the device name and the special
           “self addressing” device number (`0xff`) to ask a device about its
           own name. **Note**: A connected STH will return its own name,
           regardless of the value of the device number.

        Parameters
        ----------

        node:
            The node which has access to the Bluetooth device

        device_number:
            The number of the Bluetooth device (0 up to the number of
            available devices - 1; 0xff for self addressing).

        Returns
        -------

        The (Bluetooth broadcast) name of the device

        """

        description = f"name of device “{device_number}” from “{node}”"

        answer = await self.request_bluetooth(
            node=node,
            subcommand=5,
            device_number=device_number,
            description=f"get first part of {description}",
        )

        first_part = convert_bytes_to_text(answer.data[2:])

        answer = await self.request_bluetooth(
            node=node,
            device_number=device_number,
            subcommand=6,
            description=f"get second part of {description}",
        )

        second_part = convert_bytes_to_text(answer.data[2:])

        return first_part + second_part

    async def get_rssi(
        self, node: str | NodeId = "STH 1", device_number: int = 0xFF
    ):
        """Retrieve the RSSI (Received Signal Strength Indication) of a device

        You can use this method to retrieve the RSSI of both

        1. disconnected and
        2. connected

        devices.

        1. For disconnected devices (STHs) you will usually use the STU (e.g.
           `STU 1`) and the device number at the STU (in the range `0` up to
           the number of devices - 1) to retrieve the RSSI.

        2. For connected devices you will use the device name and the special
           “self addressing” device number (`0xff`) to ask a device about its
           own RSSI.

        Parameters
        ----------

        node:
            The node which should retrieve the RSSI

        device_number:
            The number of the Bluetooth device (0 up to the number of
            available devices - 1; 0xff for self addressing).

        Returns
        -------

        The RSSI of the device specified via node and device number

        Examples
        --------

        >>> from asyncio import run, sleep
        >>> from icotronic.can.connection import Connection

        Retrieve the RSSI of a disconnected STH

        >>> async def get_bluetooth_rssi():
        ...     async with Connection() as stu:
        ...         await stu.activate_bluetooth()
        ...
        ...         # We assume that at least one STH is available
        ...         # Get the RSSI of device “0”
        ...         return await stu.spu.get_rssi('STU 1', 0)
        >>> rssi = run(get_bluetooth_rssi())
        >>> -70 < rssi < 0
        True

        """

        response = await self.request_bluetooth(
            node=node,
            device_number=device_number,
            subcommand=12,
            description=f"get RSSI of “{device_number}” from “{node}”",
        )

        return int.from_bytes(
            response.data[2:3], byteorder="little", signed=True
        )

    async def get_mac_address(
        self, node: str | NodeId = "STH 1", device_number: int = 0xFF
    ) -> EUI:
        """Retrieve the Bluetooth MAC address of a device

        You can use this method to retrieve the address of both

        1. disconnected and
        2. connected

        devices.

        1. For disconnected devices (STHs) you will usually use the STU (e.g.
           `STU 1`) and the device number at the STU (in the range `0` up to
           the number of devices - 1) to retrieve the MAC address.

        2. For connected devices you will use the device name and the special
           “self addressing” device number (`0xff`) to ask a device about its
           own device number. **Note**: A connected STH will return its own
           MAC address, regardless of the value of the device number.

        Parameters
        ----------

        node:
            The node which should retrieve the MAC address

        device_number:
            The number of the Bluetooth device (0 up to the number of
            available devices - 1; 0xff for self addressing).

        Returns
        -------

        The MAC address of the device specified via node and device number

        """

        response = await self.request_bluetooth(
            node=node,
            device_number=device_number,
            subcommand=17,
            description=f"get MAC address of “{device_number}” from “{node}”",
        )

        return EUI(":".join(f"{byte:02x}" for byte in response.data[:1:-1]))


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    from doctest import testmod

    testmod()
