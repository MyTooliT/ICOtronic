"""Read and store some acceleration data of STH with node name Test-STH"""

# -- Imports ------------------------------------------------------------------

from asyncio import run
from pathlib import Path
from time import monotonic

from netaddr import EUI

from icotronic.can import Connection, StreamingConfiguration
from icotronic.measurement.storage import Storage

# -- Functions ----------------------------------------------------------------


async def store_streaming_data(identifier: EUI | str | int) -> None:
    """Store streaming data in HDF5 file

    Args:

        identifier:

            Identifier of STH node

    """

    async with Connection() as stu:
        async with stu.connect_sensor_node(identifier) as sensor_node:

            filepath = Path("test.hdf5")
            stream_first = StreamingConfiguration(first=True)

            with Storage(filepath, channels=stream_first) as storage:
                # Store sampling rate (and ADC configuration as metadata)
                storage.write_sample_rate(
                    await sensor_node.get_adc_configuration()
                )
                async with sensor_node.open_data_stream(
                    stream_first
                ) as stream:
                    # Read data for about five seconds
                    end = monotonic() + 5
                    async for data, _ in stream:
                        # Store 16 bit ADC value
                        storage.add_streaming_data(data)
                        if monotonic() > end:
                            break


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    run(store_streaming_data(identifier="Test-STH"))
