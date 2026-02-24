"""Tests code for ICOsystem class"""

# -- Imports ------------------------------------------------------------------

from time import time

from icotronic.can import SensorNode, StreamingConfiguration

# -- Functions ----------------------------------------------------------------


async def check_streaming(
    max_time_offset: float,
    sensor_node: SensorNode,
    configuration: StreamingConfiguration,
    values_length: int,
) -> None:
    """Check streaming data

    Args:

        max_time_offset:

            Allowed time offset of timestamps to local time in seconds

        sensor_node:

            Connected sensor node

        configuration:

            The streaming configuration

        values_length:

            The expected number of streaming elements

    """

    async with sensor_node.open_data_stream(configuration) as stream:
        async for data, _ in stream:
            current_time = time()

            assert (
                current_time - max_time_offset
                <= data.timestamp
                <= current_time + max_time_offset
            )
            assert len(data.values) == values_length
            assert 0 <= data.counter <= 255
            break


async def test_streaming_one_channel(max_time_offset, sensor_node: SensorNode):
    """Check it a single channel setup returns correct data"""

    await check_streaming(
        max_time_offset, sensor_node, StreamingConfiguration(first=True), 3
    )


async def test_streaming_two_channels(
    max_time_offset, sensor_node: SensorNode
):
    """Check it a two channel setup returns correct data"""

    await check_streaming(
        max_time_offset,
        sensor_node,
        StreamingConfiguration(first=True, second=True),
        2,
    )
