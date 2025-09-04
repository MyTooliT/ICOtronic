"""Support code for sensors and sensor configuration"""

# -- Imports ------------------------------------------------------------------

from collections.abc import Iterable, Iterator, Mapping
from enum import auto, Enum
from statistics import mean
from typing import Callable, NamedTuple

from icotronic.can.streaming import StreamingConfiguration, StreamingData

# -- Classes ------------------------------------------------------------------

# pylint: disable=too-few-public-methods


class ChannelConfiguration:
    """Attributes for channel configuration

    Args:

        channel:

            Sensor channel number

        conversion:

            Conversion function that will be applied to streaming data

    """

    def __init__(
        self,
        channel: int = 0,
        conversion: Callable[[StreamingData], StreamingData] | None = None,
    ) -> None:

        self.channel = channel
        """Sensor channel number"""
        self.conversion = (
            (lambda data: data) if conversion is None else conversion
        )
        """Function that will be used to convert streaming data"""

    def __repr__(self) -> str:
        """Return the textual representation of the configuration

        Returns:

            A string containing the attributes of the channel configuration

        """

        return f"Sensor Channel: {self.channel}"


# pylint: enable=too-few-public-methods


class SensorConfiguration(Mapping):
    """Used to store the configuration of the three sensor channels

    Args:

        first:
            The sensor number for the first measurement channel

        second:
            The sensor number for the second measurement channel

        third:
            The sensor number for the third measurement channel


    Examples:

        Create an example sensor configuration

        >>> SensorConfiguration(first=0, second=1, third=2)
        M1: None, M2: S1, M3: S2

        Initializing a sensor configuration with incorrect values will fail

        >>> SensorConfiguration(first=256, second=1, third=2)
        Traceback (most recent call last):
        ...
        ValueError: Incorrect value for first channel: “256”

        >>> SensorConfiguration(first=0, second=1, third=-1)
        Traceback (most recent call last):
        ...
        ValueError: Incorrect value for third channel: “-1”

    """

    def __init__(self, first: int = 0, second: int = 0, third: int = 0):

        self.attributes = {
            "first": ChannelConfiguration(first),
            "second": ChannelConfiguration(second),
            "third": ChannelConfiguration(third),
        }

        for name, config in self.attributes.items():
            if config.channel < 0 or config.channel > 255:
                raise ValueError(
                    f"Incorrect value for {name} channel: “{config.channel}”"
                )

    def __getitem__(self, item: str) -> ChannelConfiguration:
        """Return values of the mapping provided by this class

        Note:

            This method allow access to the object via the splat operators (*,
            **)

        Args:

            item:
                The attribute for which we want to retrieve the value

        Returns:

            The value of the attribute

        Examples:

            Create an “empty” example sensor configuration

            >>> dict(**SensorConfiguration()) # doctest:+NORMALIZE_WHITESPACE
            {'first': Sensor Channel: 0,
             'second': Sensor Channel: 0,
             'third': Sensor Channel: 0}

            Create an example sensor configuration using init values

            >>> dict(**SensorConfiguration(first=1, second=2, third=3)
            ...     ) # doctest:+NORMALIZE_WHITESPACE
            {'first': Sensor Channel: 1,
             'second': Sensor Channel: 2,
             'third': Sensor Channel: 3}

        """

        return self.attributes[item]

    def __iter__(self) -> Iterator:
        """Return an iterator over the mapping provided by this class

        Note:

            This method allow access to the object via the splat operators (*,
            **)

        Returns:

            The names of the “important” properties of the sensor
            configuration:

            - first
            - second
            - third

        Examples:

            Get the important sensor config attributes

            >>> for attribute in SensorConfiguration():
            ...     print(attribute)
            first
            second
            third

        """

        return iter(self.attributes)

    def __len__(self) -> int:
        """Return the length of the mapping provided by this class

        Note:

            This method allow access to the object via the splat operators (*,
            **)

        Returns:

            The number of “important” properties of the sensor configuration:

            - first
            - second
            - third

        Examples:

            Get the static length of some example sensor configurations

            >>> len(SensorConfiguration())
            3

            >>> len(SensorConfiguration(second=10))
            3

        """

        return len(self.attributes)

    def __str__(self) -> str:
        """The string representation of the sensor configuration

        Returns:

            A textual representation of the sensor configuration

        Examples:


            Get the string representation of some example sensor configs

            >>> str(SensorConfiguration(first=1, second=3, third=2))
            'M1: S1, M2: S3, M3: S2'

            >>> str(SensorConfiguration())
            ''

            >>> str(SensorConfiguration(second=1))
            'M2: S1'

        """

        return ", ".join((
            f"M{sensor}: S{config.channel}"
            for sensor, config in enumerate(self.attributes.values(), start=1)
            if config.channel != 0
        ))

    def __repr__(self) -> str:
        """The textual representation of the sensor configuration

        Returns:

            A textual representation of the sensor configuration

        Examples:

            Get the textual representation of some example sensor configs

            >>> repr(SensorConfiguration(first=1, second=3, third=2))
            'M1: S1, M2: S3, M3: S2'

            >>> repr(SensorConfiguration())
            'M1: None, M2: None, M3: None'

        """

        return ", ".join((
            f"M{sensor}: "
            f"{f'S{config.channel}' if config.channel != 0 else 'None'}"
            for sensor, config in enumerate(self.attributes.values(), start=1)
        ))

    @property
    def first(self) -> ChannelConfiguration:
        """Get the channel configuration for the first channel

        Returns:

            The sensor configuration of the first channel

        Examples:

            Get the sensor number for the first channel of a sensor config

            >>> SensorConfiguration(first=1, second=3, third=2).first.channel
            1

        """

        return self.attributes["first"]

    @property
    def second(self) -> ChannelConfiguration:
        """Get the channel configuration for the second channel

        Returns:

            The sensor configuration of the second channel

        Examples:

            Get the sensor number for the second channel of a sensor config

            >>> SensorConfiguration(first=1, second=3, third=2).second.channel
            3

        """

        return self.attributes["second"]

    @property
    def third(self) -> ChannelConfiguration:
        """Get the channel configuration for the third channel

        Returns:

            The sensor configuration of the third channel

        Examples:

            Get the sensor number for the third channel of a sensor config

            >>> SensorConfiguration(first=1, second=3, third=2).third.channel
            2

        """

        return self.attributes["third"]

    def disable_channel(
        self, first: bool = False, second: bool = False, third: bool = False
    ) -> None:
        """Disable certain (measurement) channels

        Args:

            first:
                Specifies if the first measurement channel should be disabled
                or not

            second:
                Specifies if the second measurement channel should be disabled
                or not

            third:
                Specifies if the third measurement channel should be disabled
                or not

        """

        if first:
            self.attributes["first"].channel = 0
        if second:
            self.attributes["second"].channel = 0
        if third:
            self.attributes["third"].channel = 0

    def requires_channel_configuration_support(self) -> bool:
        """Check if the sensor configuration requires channel config support

        Returns:

            - ``True``, if the configuration requires hardware that has
              support for changing the channel configuration
            - ``False``, otherwise

        Examples:

            Check if example sensor configs require channel config support

            >>> SensorConfiguration(first=1, second=3, third=2
            ...     ).requires_channel_configuration_support()
            True

            >>> SensorConfiguration(first=1, second=0, third=1
            ...     ).requires_channel_configuration_support()
            True

            >>> SensorConfiguration(first=1, second=2, third=3
            ...     ).requires_channel_configuration_support()
            False

            >>> SensorConfiguration().requires_channel_configuration_support()
            False

        """

        for measurement_channel, config in enumerate(
            self.attributes.values(), start=1
        ):
            if config.channel not in {0, measurement_channel}:
                return True
        return False

    def empty(self) -> bool:
        """Check if the sensor configuration is empty

        In an empty sensor configuration all of the channels are disabled.

        Returns:

            ``True``, if all channels are disabled, ``False`` otherwise

        Examples:

            Check if some example configurations are empty or not

            >>> SensorConfiguration(first=3).empty()
            False
            >>> SensorConfiguration().empty()
            True
            >>> SensorConfiguration(third=0).empty()
            True

        """

        return (
            self.first.channel == 0
            and self.second.channel == 0
            and self.third.channel == 0
        )

    def check(self):
        """Check that at least one measurement channel is enabled

        Raises:

            ValueError:
                if none of the measurement channels is enabled

        Examples:

            >>> SensorConfiguration(second=1).check()
            >>> SensorConfiguration().check()
            Traceback (most recent call last):
                ...
            ValueError: At least one measurement channel has to be enabled

        """

        if self.empty():
            raise ValueError(
                "At least one measurement channel has to be enabled"
            )

    def streaming_configuration(self) -> StreamingConfiguration:
        """Get a streaming configuration that represents this config

        Returns:

            A stream configuration where

            - every channel that is enabled in the sensor configuration is
              enabled, and
            - every channel that is disables in the sensor configuration is
              disabled.

        Examples:

            Get the streaming configuration for some example channel configs

            >>> SensorConfiguration(second=1).streaming_configuration()
            Channel 1 disabled, Channel 2 enabled, Channel 3 disabled

            >>> SensorConfiguration(first=10, third=2
            ...                    ).streaming_configuration()
            Channel 1 enabled, Channel 2 disabled, Channel 3 enabled

        """

        return StreamingConfiguration(**{
            channel: bool(config.channel)
            for channel, config in self.attributes.items()
        })


class SensorType(Enum):
    """Possible sensor types"""

    BROKEN = auto()
    """Broken sensor"""

    ACCELERATION = auto()
    """Acceleration sensor"""

    TEMPERATURE = auto()
    """Temperature sensor"""

    PIEZO = auto()
    """Piezoelectric sensor"""


class Sensor(NamedTuple):
    """Store information about a sensor"""

    type: SensorType
    """Sensor type"""

    mean: float
    """Mean value of raw ADC sensor data"""

    def __repr__(self) -> str:
        """Return a string representation of the sensor

        Returns:

            A string that describes the sensor

        Examples:

            Get the textual representation of some example sensor objects

            >>> Sensor(SensorType.BROKEN, mean=123)
            Broken Sensor (Mean: 123)

            >>> Sensor(SensorType.TEMPERATURE, mean=123)
            Temperature Sensor

        """

        representation = f"{self.type.name.capitalize()} Sensor"
        if self.type == SensorType.BROKEN:
            representation += f" (Mean: {self.mean})"

        return representation

    def works(self) -> bool:
        """Check if the sensor is working or not

        Returns:

            ``True`` if the sensor works, ``False`` otherwise

        """

        return not self.type == SensorType.BROKEN


# -- Functions ----------------------------------------------------------------


def guess_sensor(values: Iterable[int]) -> Sensor:
    """Guess the sensor type from raw 16 bit ADC values

    Args:

        values:
            Multiple raw 16 bit ADC measurement values

    Returns:

        An object representing the guessed sensor type

    Examples:

        Guess sensor types based on raw ADC values

        >>> guess_sensor([38024, 38000, 37950])
        Piezo Sensor

        >>> guess_sensor([32500, 32571, 32499])
        Acceleration Sensor

        >>> guess_sensor([10650, 10500, 10780])
        Temperature Sensor

        >>> guess_sensor([123, 10, 50])
        Broken Sensor (Mean: 61)

    """

    mean_raw = mean(values)
    half = 2**15

    tolerance_acceleration = 1000
    min_acceleration = half - tolerance_acceleration
    max_acceleration = half + tolerance_acceleration

    if 10000 <= mean_raw <= 11000:
        return Sensor(SensorType.TEMPERATURE, mean_raw)
    if min_acceleration <= mean_raw <= max_acceleration:
        return Sensor(SensorType.ACCELERATION, mean_raw)
    if 37500 <= mean_raw <= 38500:
        return Sensor(SensorType.PIEZO, mean_raw)

    return Sensor(SensorType.BROKEN, mean_raw)


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    from doctest import testmod

    testmod()
