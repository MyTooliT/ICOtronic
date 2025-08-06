"""Tests code for ICOsystem class"""

# -- Imports ------------------------------------------------------------------

from netaddr import EUI
from pytest import mark, raises

from icotronic.can.connection import Connection

# -- Globals ------------------------------------------------------------------

SENSOR_NODE_NAME = "Test-STH"

# -- Functions ----------------------------------------------------------------


@mark.asyncio
async def test_connect_mac_as_name():
    """Check it is not possible to connect with str version of MAC address

    While this might sound like a good idea, we designed the API to assume
    that the type of the identifier object specifies the type of the
    identifier. If you want to connect to an STU with a certain MAC address
    (e.g. ``08-6B-D7-01-DE-81``) you need to use an ``EUI`` (Extended Unique
    Identifier aka MAC address) object. If you use the **string
    representation** then the (fixed version of) ``STU.connect_sensor_device``
    assumes that you want to to connect to a **device with the name**
    ``08-6B-D7-01-DE-81``.

    """

    mac_address = None
    async with Connection() as stu:
        async with stu.connect_sensor_node(SENSOR_NODE_NAME) as sensor_node:
            mac_address = await sensor_node.get_mac_address()
            assert isinstance(mac_address, EUI)

    with raises(
        ValueError, match="“08-6B-D7-01-DE-81” is too long to be a valid name"
    ):
        async with Connection() as stu:
            async with stu.connect_sensor_node(str(mac_address)):
                assert False


@mark.asyncio
async def test_connect_invalid_number():
    """Check that specifying an invalid sensor node number fails"""

    with raises(ValueError, match="“-1” is not a valid Bluetooth node number"):
        async with Connection() as stu:
            async with stu.connect_sensor_node(-1):
                pass


@mark.asyncio
async def test_connect_invalid_name():
    """Check that specifying an invalid name fails"""

    with raises(ValueError, match="“👋” is not a valid name"):
        async with Connection() as stu:
            async with stu.connect_sensor_node("👋"):
                pass
