"""Configuration for pytest"""

# -- Imports ------------------------------------------------------------------

from pytest import fixture

from netaddr import EUI

from icotronic.can import Connection

# pylint: disable=redefined-outer-name

# -- Fixtures -----------------------------------------------------------------


@fixture(scope="session")
def sensor_node_name() -> str:
    """Returns the name of the sensor node used for the test"""

    return "Test-STH"


@fixture(scope="session")
async def sensor_node_mac_address(sensor_node_name: str) -> EUI:
    """Return the MAC address of the sensor node used for the test"""

    async with Connection() as stu:
        async with stu.connect_sensor_node(sensor_node_name) as sensor_node:
            return await sensor_node.get_mac_address()
