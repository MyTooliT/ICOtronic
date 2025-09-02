"""Configuration for pytest"""

# -- Imports ------------------------------------------------------------------

from pytest import fixture

# -- Fixtures -----------------------------------------------------------------


@fixture(scope="session")
def sensor_node_name():
    """Returns the name of the sensor node used for the test"""

    return "Test-STH"
