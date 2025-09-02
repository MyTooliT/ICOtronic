"""Tests code for ICOsystem class"""

# -- Imports ------------------------------------------------------------------

from netaddr import EUI
from pytest import raises
from time import time

from icotronic.can import Connection, SensorNode, StreamingConfiguration

# -- Functions ----------------------------------------------------------------


async def test_streaming_one_channel(max_time_offset, sensor_node: SensorNode):
    """Check it a single channel setup returns correct data"""

    async with sensor_node.open_data_stream(
        StreamingConfiguration(first=True)
    ) as stream:
        async for data, _ in stream:
            current_time = time()

            assert (
                current_time - max_time_offset
                <= data.timestamp
                <= current_time + max_time_offset
            )
            assert len(data.values) == 3
            assert 0 <= data.counter <= 255
            break
