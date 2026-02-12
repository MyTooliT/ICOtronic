"""Command Line Parsing support"""

# -- Imports ------------------------------------------------------------------

from argparse import ArgumentParser

from icotronic.can.adc import ADCConfiguration
from icotronic.cmdline.types import (
    channel_number,
    node_name,
    mac_address,
    measurement_time,
    non_infinite_measurement_time,
    sensor_node_number,
)

# -- Functions ----------------------------------------------------------------


def add_identifier_arguments(parser: ArgumentParser) -> None:
    """Add node identifier arguments to given argument parser

    Args:

        parser:
            The parser which should include the node identifier arguments

    """

    identifier_arg_group = parser.add_argument_group(
        title="Sensor Node Identifier"
    )

    identifier_group = identifier_arg_group.add_mutually_exclusive_group(
        required=True
    )

    identifier_group.add_argument(
        "-n",
        "--name",
        dest="identifier",
        metavar="NAME",
        help="Name of sensor node",
        default="Test-STH",
        type=node_name,
    )
    identifier_group.add_argument(
        "-m",
        "--mac-address",
        dest="identifier",
        metavar="MAC_ADRESS",
        help="Bluetooth MAC address of sensor node",
        type=mac_address,
    )
    identifier_group.add_argument(
        "-d",
        "--number",
        type=sensor_node_number,
        dest="identifier",
        metavar="NUMBER",
        help="Node number of sensor node",
    )


def add_adc_arguments(parser: ArgumentParser) -> None:
    """Add ADC arguments to given argument parser

    Args:

        parser:
            The parser which should include the ADC arguments

    """

    adc_group = parser.add_argument_group(title="ADC")
    adc_group.add_argument(
        "-s",
        "--prescaler",
        type=int,
        choices=range(2, 128),
        metavar="2–127",
        default=2,
        required=False,
        help="Prescaler value",
    )
    adc_group.add_argument(
        "-a",
        "--acquisition",
        type=int,
        choices=sorted([2**number for number in range(9)] + [3]),
        default=8,
        required=False,
        help="Acquisition time value",
    )
    adc_group.add_argument(
        "-o",
        "--oversampling",
        type=int,
        choices=[2**number for number in range(13)],
        default=64,
        required=False,
        help="Oversampling rate value",
    )
    adc_group.add_argument(
        "-v",
        "--voltage-reference",
        choices=ADCConfiguration.REFERENCE_VOLTAGES,
        type=float,
        default=3.3,
        required=False,
        help="Reference voltage in V",
    )


def add_channel_arguments(group) -> None:
    """Add channel arguments to given argument parser group

    Args:

        group:
            The parser group to which the channel arguments should be added to

    """

    group.add_argument(
        "-1",
        "--first-channel",
        type=channel_number,
        default=1,
        const=1,
        nargs="?",
        help=(
            "sensor channel number for first measurement channel "
            "(1 - 255; 0 to disable)"
        ),
    )
    group.add_argument(
        "-2",
        "--second-channel",
        type=channel_number,
        default=0,
        const=2,
        nargs="?",
        help=(
            "sensor channel number for second measurement channel "
            "(1 - 255; 0 to disable)"
        ),
    )
    group.add_argument(
        "-3",
        "--third-channel",
        type=channel_number,
        default=0,
        const=3,
        nargs="?",
        help=(
            "sensor channel number for third measurement channel "
            "(1 - 255; 0 to disable)"
        ),
    )


def create_icon_parser() -> ArgumentParser:
    """Create command line parser for icon

    Returns:

        A parser for the CLI arguments of icon

    """

    parser = ArgumentParser(description="ICOtronic CLI tool")

    parser.add_argument(
        "--log",
        choices=("debug", "info", "warning", "error", "critical"),
        default="warning",
        required=False,
        help="minimum log level",
    )

    subparsers = parser.add_subparsers(
        required=True, title="Subcommands", dest="subcommand"
    )

    # ==========
    # = Config =
    # ==========

    subparsers.add_parser(
        "config", help="Open config file in default application"
    )

    # =============
    # = Data Loss =
    # =============

    dataloss_parser = subparsers.add_parser(
        "dataloss", help="Check data loss at different sample rates"
    )
    measurement_group = dataloss_parser.add_argument_group(title="Measurement")
    measurement_group.add_argument(
        "-t",
        "--time",
        type=non_infinite_measurement_time,
        help="Measurement time in seconds",
        default=10,
    )
    add_identifier_arguments(dataloss_parser)

    # ========
    # = List =
    # ========

    subparsers.add_parser("list", help="List sensor nodes")

    # ===========
    # = Measure =
    # ===========

    measurement_parser = subparsers.add_parser(
        "measure", help="Store measurement data"
    )

    measurement_group = measurement_parser.add_argument_group(
        title="Measurement"
    )

    measurement_group.add_argument(
        "-t",
        "--time",
        type=measurement_time,
        help="Measurement time in seconds (0 for infinite runtime)",
        default=10,
    )

    add_channel_arguments(measurement_group)
    add_identifier_arguments(measurement_parser)
    add_adc_arguments(measurement_parser)

    # ==========
    # = Rename =
    # ==========

    rename_parser = subparsers.add_parser(
        "rename", help="Rename a sensor node"
    )
    add_identifier_arguments(rename_parser)
    rename_parser.add_argument(
        "name",
        type=str,
        help="New name of sensor node",
        nargs="?",
        default="Test-STH",
    )

    # =======
    # = STU =
    # =======

    stu_parser = subparsers.add_parser(
        "stu", help="Execute commands related to stationary receiver unit"
    )

    stu_subparsers = stu_parser.add_subparsers(
        required=True, title="Subcommands", dest="stu_subcommand"
    )
    stu_subparsers.add_parser("mac", help="Show Bluetooth MAC address")
    stu_subparsers.add_parser("reset", help="Reset STU")

    return parser


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    from doctest import testmod

    testmod()
