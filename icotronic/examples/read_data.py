"""Read some acceleration data of STH with device name Test-STH"""

# -- Imports ------------------------------------------------------------------

from asyncio import run

from icotronic.can import Connection, StreamingConfiguration

# -- Functions ----------------------------------------------------------------


async def read_streaming_data(identifier):
    async with Connection() as stu:
        async with stu.connect_sensor_device(identifier) as sensor_device:
            # Read data of first channel
            async with sensor_device.open_data_stream(
                StreamingConfiguration(first=True)
            ) as stream:
                messages = 5
                async for data, _ in stream:
                    print(f"Read data values: {data}")
                    messages -= 1
                    if messages <= 0:
                        break


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    run(read_streaming_data(identifier="Test-STH"))
