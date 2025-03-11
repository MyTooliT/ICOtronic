"""Read and write EEPROM data of ICOtronic sensory tool holders"""

# -- Imports ------------------------------------------------------------------

from icotronic.can.eeprom.sensor import SensorNodeEEPROM

# -- Sensor -------------------------------------------------------------------


class STHEEPROM(SensorNodeEEPROM):
    """Read and write EEPROM data of sensory tool holders"""

    # ===============
    # = Calibration =
    # ===============

    async def read_x_axis_acceleration_slope(self) -> float:
        """Retrieve the acceleration slope of the x-axis from the EEPROM

        Returns
        -------

        The x-axis acceleration slope of STH 1

        Example
        -------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection
        >>> from icotronic.can.sth import STH

        >>> async def read_x_axis_acceleration_slope():
        ...     async with Connection() as stu:
        ...         # We assume that at least one sensor device is available
        ...         async with stu.connect_sensor_device(0, STH) as sth:
        ...             return (await
        ...                     sth.eeprom.read_x_axis_acceleration_slope())
        >>> x_axis_acceleration_slope = run(read_x_axis_acceleration_slope())
        >>> isinstance(x_axis_acceleration_slope, float)
        True

        """

        return await self.read_float(address=8, offset=0)


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    from doctest import run_docstring_examples

    run_docstring_examples(
        STHEEPROM.read_x_axis_acceleration_slope,
        globals(),
        verbose=True,
    )
