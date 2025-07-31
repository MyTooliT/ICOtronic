"""Tests code for ICOsystem class"""

# -- Imports ------------------------------------------------------------------

from asyncio import sleep

from netaddr import EUI
from pytest import mark, raises

from icotronic.can.connection import Connection

# -- Globals ------------------------------------------------------------------

sensor_node_name = "Test-STH"

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
        async with stu.connect_sensor_node(sensor_node_name) as sensor_node:
            mac_address = await sensor_node.get_mac_address()
            assert isinstance(mac_address, EUI)

    with raises(TimeoutError):
        async with Connection() as stu:
            async with stu.connect_sensor_node(
                str(mac_address)
            ) as sensor_node:
                assert False
