"""Support code for Bluetooth functionality"""

# -- Imports ------------------------------------------------------------------

from __future__ import annotations

from icotronic.can.constants import (
    ADVERTISEMENT_TIME_EEPROM_TO_MS,
)

# -- Classes ------------------------------------------------------------------


class Times:
    """Advertisement time and time until deeper sleep mode

    Args:

        advertisement:

            The advertisement time in milliseconds

        sleep:

            The time until the node falls into a deeper sleep mode in
            milliseconds

    Raises:

        ValueError: If one of the input values is too small or too large

    Examples:

        Create a times object with standard values for reduced energy mode

        >>> one_quarter_second = 1.25*1000
        >>> five_minutes = 5*60*1000
        >>> Times(advertisement=one_quarter_second, sleep=five_minutes)
        Advertisement Time: 1250.0 ms, Sleep Time: 300000 ms

        Create a times object with standard values for lowest energy mode

        >>> two_half_second = 2.5*1000
        >>> three_days = 3*24*3600*1000
        >>> Times(advertisement=two_half_second, sleep=three_days)
        Advertisement Time: 2500.0 ms, Sleep Time: 259200000 ms

        Creating time objects only works with positive values

        >>> Times(advertisement=0, sleep=five_minutes)
        Traceback (most recent call last):
        ...
        ValueError: Advertisement time value must be positive

        >>> Times(advertisement=one_quarter_second, sleep=0)
        Traceback (most recent call last):
        ...
        ValueError: Sleep time value must be positive

        Values that are too large do not work

        >>> too_large_advertisement = 2**16 * 0.625
        >>> Times(advertisement=too_large_advertisement,
        ...       sleep=five_minutes) # doctest:+NORMALIZE_WHITESPACE
        Traceback (most recent call last):
        ...
        ValueError: Advertisement time of 40960.0 ms is larger than maximum
                    time of 40959 ms

        >>> too_large_sleep = 2**32
        >>> Times(advertisement=one_quarter_second,
        ...       sleep=too_large_sleep) # doctest:+NORMALIZE_WHITESPACE
        Traceback (most recent call last):
        ...
        ValueError: Sleep time of 4294967296 ms is larger than maximum time
                    of 4294967295 ms

    """

    ADVERTISEMENT_MAX_VALUE = int(
        (2**16 - 1) * ADVERTISEMENT_TIME_EEPROM_TO_MS
    )
    SLEEP_TIME_MAX_VALUE = 2**32 - 1

    def __init__(self, advertisement: float, sleep: float) -> None:
        cls = type(self)

        if advertisement <= 0:
            raise ValueError("Advertisement time value must be positive")
        if advertisement > cls.ADVERTISEMENT_MAX_VALUE:
            raise ValueError(
                f"Advertisement time of {advertisement} ms is larger than "
                f"maximum time of {cls.ADVERTISEMENT_MAX_VALUE} ms"
            )
        self.advertisement = advertisement

        if sleep <= 0:
            raise ValueError("Sleep time value must be positive")
        if sleep > cls.SLEEP_TIME_MAX_VALUE:
            raise ValueError(
                f"Sleep time of {sleep} ms is larger than "
                f"maximum time of {cls.SLEEP_TIME_MAX_VALUE} ms"
            )
        self.sleep = sleep

    @classmethod
    def from_data(cls, values: bytearray | list[int]) -> Times:
        """Convert byte values into a times object

        Args:

            values:

                The byte values that represent the Python object

        Returns:

            A times object that store the advertisement and sleep times
            represented by ``values``

        Examples:

            Create a times object from its byte representation

            >>> times = Times(advertisement=4000, sleep=8000)
            >>> times_converted = Times.from_data(times.to_data())
            >>> times.advertisement == times_converted.advertisement
            True
            >>> times.sleep == times_converted.sleep
            True

        """

        byte_representation = bytearray(values)
        sleep_time = int.from_bytes(byte_representation[:4], "little")
        advertisement_time = (
            int.from_bytes(byte_representation[4:6], "little")
            * ADVERTISEMENT_TIME_EEPROM_TO_MS
        )

        return Times(advertisement=advertisement_time, sleep=sleep_time)

    def to_data(self) -> list[int]:
        """Get the bytes values of this times object

        Returns:

            A list of bytes that represent the times object

        Examples:

            Convert a times object into a list of bytes

            >>> times = Times(advertisement=1000, sleep=2000)
            >>> times_bytes = times.to_data()
            >>> int.from_bytes(bytearray(times_bytes[:4]), "little")
            2000
            >>> int.from_bytes(bytearray(times_bytes[4:]),
            ...                "little") == 1000 / 0.625
            True

        """

        advertisement_time = round(
            self.advertisement / ADVERTISEMENT_TIME_EEPROM_TO_MS
        )
        sleep_time = int(self.sleep)

        return list(
            sleep_time.to_bytes(4, "little")
            + advertisement_time.to_bytes(2, "little")
        )

    def __repr__(self) -> str:
        """Return a string representation of the object

        Returns:

            A string that contains the advertisement time and sleep time values

        Examples:

            Get the string representation of a simple times object

            >>> Times(advertisement=10, sleep=60_000)
            Advertisement Time: 10 ms, Sleep Time: 60000 ms

        """

        return ", ".join(
            [
                f"Advertisement Time: {self.advertisement} ms",
                f"Sleep Time: {self.sleep} ms",
            ]
        )


# -- Variables ----------------------------------------------------------------

ENERGY_MODE_REDUCED_DEFAULT: Times = Times(
    sleep=5 * 60 * 1000, advertisement=1.25 * 1000
)
"""Default Bluetooth Energy Mode Reduced timing values"""

ENERGY_MODE_LOWEST_DEFAULT = Times(
    sleep=3 * 24 * 3600 * 1000, advertisement=2.5 * 1000
)
"""Default Bluetooth Energy Mode Lowest timing values"""
