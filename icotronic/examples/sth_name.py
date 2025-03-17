"""Read name of STH with device number 0"""

# -- Imports ------------------------------------------------------------------

from asyncio import run

from icotronic.can import Connection

# -- Functions ----------------------------------------------------------------


async def read_name(identifier):
    async with Connection() as stu:
        async with stu.connect_sensor_device(identifier) as sensor_device:
            name = await sensor_device.get_name()
            print(f"Connected to sensor device “{name}”")


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    # Possible Identifiers:
    # - Name:          e.g. `"Test-STH"`
    # - Device Number: e.g. `1`
    # - MAC Address:   e.g. `netaddr.EUI('08-6B-D7-01-DE-81')`
    run(read_name(identifier=0))
