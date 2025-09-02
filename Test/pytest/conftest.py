"""Configuration for pytest"""

# -- Imports ------------------------------------------------------------------

from pytest import fixture

from netaddr import EUI

from icotronic.can import Connection, SensorNode, STU

# pylint: disable=redefined-outer-name

# -- Fixtures -----------------------------------------------------------------


@fixture(scope="session")
async def max_time_offset() -> float:
    """Allowed time offset of timestamps to local time in seconds"""

    return 1


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


@fixture
async def stu() -> STU:
    """Connect to and disconnect from STU"""

    async with Connection() as stu:
        yield stu


@fixture
async def sensor_node(stu, sensor_node_name) -> SensorNode:
    """Connect to and disconnect from sensor node"""

    async with stu.connect_sensor_node(sensor_node_name) as sensor_node:
        yield sensor_node
