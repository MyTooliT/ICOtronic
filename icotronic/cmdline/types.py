"""Support for checking different CLI input types"""

# -- Imports ------------------------------------------------------------------

from argparse import ArgumentTypeError
from math import inf
from re import compile as re_compile

from netaddr import AddrFormatError, EUI

# -- Functions ----------------------------------------------------------------


def base64_mac_address(name):
    """Check if the given text represents a Base64 encoded MAC address

    Returns:

        The given text on success

    Raises:

        An argument type error in case the given value does not represent a MAC
        address

    Examples:

        Parse valid Base64 encoded MAC address

        >>> base64_mac_address("CGvXAd6B")
        'CGvXAd6B'

        Parse invalid Base64 encoded MAC address

        >>> base64_mac_address("CGvXAd") # doctest:+NORMALIZE_WHITESPACE
        Traceback (most recent call last):
           ...
        argparse.ArgumentTypeError: “CGvXAd” is not a Base64 encoded MAC
                                    address

    """

    base64_regex = re_compile("[A-Za-z0-9/+]{8}$")
    if base64_regex.match(name):
        return name
    raise ArgumentTypeError(f"“{name}” is not a Base64 encoded MAC address")


def byte_value(value):
    """Check if the given string represents a byte value

    Returns:

        An integer representing the given value on success

    Raises:

        An argument type error in case the given value does not represent a
        (positive) byte value

    Examples:

        Parse valid byte values

        >>> byte_value("0xa")
        10
        >>> byte_value("137")
        137

        Parse incorrect byte value

        >>> byte_value("256")
        Traceback (most recent call last):
           ...
        argparse.ArgumentTypeError: “256” is not a valid byte value

    """

    try:
        number = int(value, base=0)
        if number < 0 or number > 255:
            raise ValueError()
        return number
    except ValueError as error:
        raise ArgumentTypeError(
            f"“{value}” is not a valid byte value"
        ) from error


def channel_number(value: str):
    """Check if the given string represents a valid channel number (0 – 255)

    Raises:

        An argument type error in case the given value does not represent a
        channel number

    Returns:

        An integer representing the given channel number on success

    Examples:

        Parse correct channel numbers

        >>> channel_number("1")
        1
        >>> channel_number("123")
        123
        >>> channel_number("0")
        0
        >>> channel_number("255")
        255

        Parsing an incorrect negative channel number will fail

        >>> channel_number("-1")
        Traceback (most recent call last):
           ...
        argparse.ArgumentTypeError: “-1” is not a valid channel number

        Parse an incorrectly large channel number will fail

        >>> channel_number("256")
        Traceback (most recent call last):
           ...
        argparse.ArgumentTypeError: “256” is not a valid channel number

    """

    try:
        number: int | None = None
        number = int(value)
        if number < 0 or number > 255:
            raise ValueError()
        return number
    except ValueError as error:
        raise ArgumentTypeError(
            f"“{number if number is not None else value}” is not a valid "
            "channel number"
        ) from error


def mac_address(address: str) -> EUI:
    """Check if the given text represents a MAC address

    Returns:

        The parsed MAC address

    Raises:

        An argument type error in case the given text does not store a MAC
        address of the form

        - ``xx:xx:xx:xx:xx:xx`` or
        - ``xx-xx-xx-xx-xx-xx``

        where `x` represents a hexadecimal number.

    Examples:

        Parse a correct MAC address

        >>> mac_address("08:6b:d7:01:de:81")
        EUI('08-6B-D7-01-DE-81')

        Parsing an incorrect MAC address will fails

        >>> mac_address("08:6b:d7:01:de:666") # doctest:+NORMALIZE_WHITESPACE
        Traceback (most recent call last):
           ...
        argparse.ArgumentTypeError: “08:6b:d7:01:de:666” is not a valid MAC
                                    address

    """

    try:
        eui = EUI(address)
    except AddrFormatError as error:
        raise ArgumentTypeError(
            f"“{address}” is not a valid MAC address"
        ) from error

    return eui


def measurement_time(value: str) -> float:
    """Check if the given number is valid measurement time

    0 will be interpreted as infinite measurement runtime

    Returns:

        A float value representing the measurement time on success

    Raises:

        ArgumentTypeError:
             If the given text is not a valid measurement time value


    Examples:

        Parse correct measurement times

        >>> measurement_time("0")
        inf

        >>> measurement_time("0.1")
        0.1

        >>> measurement_time("12.34")
        12.34

        Parsing a negative measurement time fails

        >>> measurement_time("-1")
        Traceback (most recent call last):
           ...
        argparse.ArgumentTypeError: “-1” is not a valid measurement time

        Parsing an incorrect measurement time fails

        >>> measurement_time("something")
        Traceback (most recent call last):
           ...
        argparse.ArgumentTypeError: “something” is not a valid measurement time

    """

    try:
        number = float(value)
        if number < 0:
            raise ValueError()
        if number == 0:
            return inf
        return number
    except ValueError as error:
        raise ArgumentTypeError(
            f"“{value}” is not a valid measurement time"
        ) from error


def non_infinite_measurement_time(value: str) -> float:
    """Check if the given number is valid (non-infinite) measurement time

    0 will be interpreted as infinite measurement runtime

    Returns:

        A float value representing the measurement time on success

    Raises:

        ArgumentTypeError:
             If the given text is not a valid measurement time value

    Examples:

        Parse correct measurement time

        >>> non_infinite_measurement_time("0.1")
        0.1

        Parsing an “infinite” measurement time fails

        >>> non_infinite_measurement_time("0") # doctest:+NORMALIZE_WHITESPACE
        Traceback (most recent call last):
           ...
        argparse.ArgumentTypeError: “0” is not a valid positive measurement
                                    time

    """

    runtime = measurement_time(value)
    if runtime == inf:
        raise ArgumentTypeError(
            f"“{value}” is not a valid positive measurement time"
        )

    return runtime


def sensor_node_number(value: str) -> int:
    """Check if the given number is valid Bluetooth node number

    Returns:

        An integer representing the given channel number on success

    Raises:

        ArgumentTypeError:
             If the given text is not a valid sensor node number

    Examples:

        Parse correct sensor node numbers

        >>> sensor_node_number("0")
        0

        >>> sensor_node_number("123")
        123

        Parsing an incorrect negative sensor node number fails

        >>> sensor_node_number("-1")
        Traceback (most recent call last):
           ...
        argparse.ArgumentTypeError: “-1” is not a valid Bluetooth node number

        Parsing an incorrect sensor node number fails

        >>> sensor_node_number("hello") # doctest:+NORMALIZE_WHITESPACE
        Traceback (most recent call last):
           ...
        argparse.ArgumentTypeError: “hello” is not a valid Bluetooth node
                                    number

    """

    try:
        number = int(value)
        if number < 0:
            raise ValueError()
        return number
    except ValueError as error:
        raise ArgumentTypeError(
            f"“{value}” is not a valid Bluetooth node number"
        ) from error


def node_name(name: str) -> str:
    """Check if the given text is a valid node name

    Returns:

        The given name on success

    Raises:

        An argument type error in case the given text does not store a valid
        node name. This is the case, if the name

        - is longer than 8 characters or
        - contains non-ASCII data.

    Examples:

        Parse a correct node name

        >>> node_name("Blubb")
        'Blubb'

        A node name is not allowed to contain non-ASCII data

        >>> node_name("Blübb")
        Traceback (most recent call last):
           ...
        argparse.ArgumentTypeError: “Blübb” is not a valid name

        A node name can not be longer than 8 characters

        >>> node_name("123456789") # doctest:+NORMALIZE_WHITESPACE
        Traceback (most recent call last):
           ...
        argparse.ArgumentTypeError: “123456789” is too long to be a valid
                                    name

    """

    try:
        name.encode("ascii")
    except UnicodeEncodeError as error:
        raise ArgumentTypeError(f"“{name}” is not a valid name") from error

    if len(name) > 8:
        raise ArgumentTypeError(f"“{name}” is too long to be a valid name")

    return name
