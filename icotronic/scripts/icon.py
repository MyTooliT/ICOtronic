"""ICOn command line tool

See: https://mytoolit.github.io/ICOtronic/#icon-cli-tool

for more information
"""

# -- Imports ------------------------------------------------------------------

from argparse import Namespace
from asyncio import run, sleep
from functools import partial
from logging import basicConfig, getLogger
from pathlib import Path
from sys import stderr
from time import perf_counter_ns, process_time_ns, time
from typing import List

from can.interfaces.pcan import PcanError
from tqdm import tqdm

from icotronic.can import Connection
from icotronic.can.adc import ADCConfiguration
from icotronic.can.error import CANConnectionError, UnsupportedFeatureException
from icotronic.can.node.stu import SensorNodeInfo
from icotronic.can.node.sth import STH
from icotronic.can.streaming import StreamingTimeoutError
from icotronic.cmdline.parse import create_icon_parser
from icotronic.config import ConfigurationUtility, settings
from icotronic.measurement import convert_raw_to_g
from icotronic.measurement import Storage
from icotronic.measurement.sensor import SensorConfiguration

# -- Functions ----------------------------------------------------------------


async def get_acceleration_sensor_range_in_g(sth: STH) -> float:
    """Read sensor range of acceleration sensor

    Precondition
    ------------

    The STH object given as parameter needs to be connected to a sensor
    node before you call this coroutine

    Parameters
    ----------

    sth:
        The STH object used to read the sensor range

    Returns
    -------

    The sensor range of the acceleration sensor, or the default range of 200
    (± 100 g) sensor, if there was a problem reading the sensor range

    """

    sensor_range = 200

    try:
        sensor_range = await sth.get_acceleration_sensor_range_in_g()
        if sensor_range < 1:
            print(
                f"Warning: Sensor range “{sensor_range}” below 1 g — Using "
                "range 200 instead (± 100 g sensor)",
                file=stderr,
            )
            sensor_range = 200
    except ValueError:
        print(
            "Warning: Unable to determine sensor range from "
            "EEPROM value — Assuming ± 100 g sensor",
            file=stderr,
        )

    return sensor_range


def command_config(  # pylint: disable=unused-argument
    arguments: Namespace,
) -> None:
    """Open configuration file"""

    ConfigurationUtility.open_user_config()


# pylint: disable=too-many-locals


async def command_dataloss(arguments: Namespace) -> None:
    """Check data loss at different sample rates"""

    identifier = arguments.identifier
    logger = getLogger()

    async with Connection() as stu:
        logger.info("Connecting to “%s”", identifier)
        async with stu.connect_sensor_node(identifier, STH) as sth:
            assert isinstance(sth, STH)
            logger.info("Connected to “%s”", identifier)

            sensor_range = await get_acceleration_sensor_range_in_g(sth)
            conversion_to_g = partial(convert_raw_to_g, max_value=sensor_range)

            measurement_time_s = 10

            sensor_config = SensorConfiguration(first=1)

            for oversampling_rate in (
                2**exponent for exponent in range(6, 10)
            ):
                logger.info("Oversampling rate: %s", oversampling_rate)
                adc_config = ADCConfiguration(
                    prescaler=2,
                    acquisition_time=8,
                    oversampling_rate=oversampling_rate,
                )
                await sth.set_adc_configuration(**adc_config)
                sample_rate = adc_config.sample_rate()
                logger.info("Sample rate: %s Hz", sample_rate)

                filepath = Path(f"Measurement {sample_rate} Hz.hdf5")
                with Storage(
                    filepath.resolve(), sensor_config.streaming_configuration()
                ) as storage:
                    storage.write_sensor_range(sensor_range)
                    storage.write_sample_rate(adc_config)

                    progress = tqdm(
                        total=int(sample_rate * measurement_time_s),
                        desc="Read sensor data",
                        unit=" values",
                        leave=False,
                        disable=None,
                    )

                    start_time = time()
                    try:
                        async with sth.open_data_stream(
                            sensor_config.streaming_configuration()
                        ) as stream:
                            async for data, _ in stream:
                                storage.add_streaming_data(
                                    data.apply(conversion_to_g)
                                )
                                progress.update(3)
                                if time() - start_time >= measurement_time_s:
                                    break
                    except PcanError as error:
                        print(
                            f"Unable to collect streaming data: {error}",
                            file=stderr,
                        )

                    progress.close()
                print(f"Stored measurement data in “{filepath}”")


# pylint: enable=too-many-locals


async def command_list(
    arguments: Namespace,  # pylint: disable=unused-argument
) -> None:
    """Print a list of available sensor nodes

    Parameters
    ----------

    arguments:
        The given command line arguments

    """

    async with Connection() as stu:
        timeout = time() + 5
        sensor_nodes: List[SensorNodeInfo] = []
        sensor_nodes_before: List[SensorNodeInfo] = []

        # - First request for sensor nodes will produce empty list
        # - Subsequent retries should provide all available sensor nodes
        # - We wait until the number of sensor nodes is larger than 1 and
        #   has not changed between one iteration or the timeout is reached
        while (
            len(sensor_nodes) <= 0
            and time() < timeout
            or len(sensor_nodes) != len(sensor_nodes_before)
        ):
            sensor_nodes_before = list(sensor_nodes)
            sensor_nodes = await stu.get_sensor_nodes()
            await sleep(0.5)

        for node in sensor_nodes:
            print(node)


# pylint: disable=too-many-locals


async def command_measure(arguments: Namespace) -> None:
    """Open measurement stream and store data

    Parameters
    ----------

    arguments:
        The given command line arguments

    """

    logger = getLogger()

    identifier = arguments.identifier
    measurement_time_s = arguments.time

    async with Connection() as stu:
        async with stu.connect_sensor_node(identifier, STH) as sth:
            assert isinstance(sth, STH)

            adc_config = ADCConfiguration(
                reference_voltage=arguments.voltage_reference,
                prescaler=arguments.prescaler,
                acquisition_time=arguments.acquisition,
                oversampling_rate=arguments.oversampling,
            )
            await sth.set_adc_configuration(**adc_config)
            print(f"Sample Rate: {adc_config.sample_rate():.2f} Hz")

            user_sensor_config = SensorConfiguration(
                first=arguments.first_channel,
                second=arguments.second_channel,
                third=arguments.third_channel,
            )

            if user_sensor_config.requires_channel_configuration_support():
                try:
                    await sth.set_sensor_configuration(user_sensor_config)
                except UnsupportedFeatureException as exception:
                    raise UnsupportedFeatureException(
                        f"Sensor channel configuration “{user_sensor_config}”"
                        f" is not supported by the sensor node “{identifier}”"
                    ) from exception

            sensor_range = await get_acceleration_sensor_range_in_g(sth)
            conversion_to_g = partial(convert_raw_to_g, max_value=sensor_range)
            filepath = settings.get_output_filepath()

            with Storage(
                filepath, user_sensor_config.streaming_configuration()
            ) as storage:
                storage.write_sensor_range(sensor_range)
                storage.write_sample_rate(adc_config)

                streaming_config = user_sensor_config.streaming_configuration()
                logger.info("Streaming Configuration: %s", streaming_config)
                values_per_message = streaming_config.data_length()

                progress = tqdm(
                    total=round(
                        adc_config.sample_rate() * measurement_time_s, 0
                    ),
                    desc="Read sensor data",
                    unit=" values",
                    leave=False,
                    disable=None,
                )

                try:
                    async with sth.open_data_stream(
                        streaming_config
                    ) as stream:
                        start_time = time()
                        async for data, _ in stream:
                            storage.add_streaming_data(
                                data.apply(conversion_to_g)
                            )
                            progress.update(values_per_message)
                            if time() - start_time >= measurement_time_s:
                                break
                except KeyboardInterrupt:
                    pass
                finally:
                    progress.close()
                    print(f"Data Loss: {storage.dataloss() * 100} %")
                    print(f"Filepath: {filepath}")


# pylint: enable=too-many-locals


async def command_rename(arguments: Namespace) -> None:
    """Rename a sensor node

    Parameters
    ----------

    arguments:
        The given command line arguments

    """

    identifier = arguments.identifier
    name = arguments.name

    async with Connection() as stu:
        async with stu.connect_sensor_node(identifier) as sensor_node:
            old_name = await sensor_node.get_name()
            mac_address = await sensor_node.get_mac_address()

            await sensor_node.set_name(name)
            name = await sensor_node.get_name()
            print(
                f"Renamed sensor node “{old_name}” with MAC "
                f"address “{mac_address}” to “{name}”"
            )


async def command_stu(arguments: Namespace) -> None:
    """Run specific commands regarding stationary transceiver unit

    Parameters
    ----------

    arguments:
        The given command line arguments

    """

    subcommand = arguments.stu_subcommand

    async with Connection() as stu:
        if subcommand == "ota":
            # The coroutine below activates the advertisement required for the
            # Over The Air (OTA) firmware update.
            #
            # - The `deactivate_bluetooth` command called when the execution
            #   leaves the `async with` block seems to not turn off the
            #   advertisement for the STU.
            # - Even a **hard STU reset does not turn off the advertisement**.
            # - One way to turn off the advertisement seems to be to initiate a
            #   connection with a sensor node.
            await stu.activate_bluetooth()
        elif subcommand == "mac":
            print(await stu.get_mac_address())
        elif subcommand == "reset":
            await stu.reset()
        else:
            raise ValueError(f"Unknown STU subcommand “{subcommand}”")


def main():
    """ICOtronic command line tool"""

    parser = create_icon_parser()
    arguments = parser.parse_args()
    try:
        if arguments.subcommand == "measure":
            SensorConfiguration(
                first=arguments.first_channel,
                second=arguments.second_channel,
                third=arguments.third_channel,
            ).check()
    except ValueError as error:
        parser.prog = f"{parser.prog} {arguments.subcommand}"
        parser.error(str(error))

    basicConfig(
        level=arguments.log.upper(),
        style="{",
        format="{asctime} {levelname:7} {message}",
    )

    logger = getLogger()
    logger.info("CLI Arguments: %s", arguments)

    if arguments.subcommand == "config":
        command_config(arguments.subcommand)
    else:
        command_to_coroutine = {
            "dataloss": command_dataloss,
            "list": command_list,
            "measure": command_measure,
            "rename": command_rename,
            "stu": command_stu,
        }

        try:
            perf_start, cpu_start = perf_counter_ns(), process_time_ns()
            run(command_to_coroutine[arguments.subcommand](arguments))
            perf_end, cpu_end = perf_counter_ns(), process_time_ns()
            run_time_command = perf_end - perf_start
            cpu_time_command = cpu_end - cpu_start
            cpu_usage = cpu_time_command / run_time_command * 100
            logger.info(
                "Ran command “%s” in %.2f seconds (CPU time: %.2f seconds, "
                "CPU Usage: %.2f %%)",
                arguments.subcommand,
                run_time_command / 10**9,
                cpu_time_command / 10**9,
                cpu_usage,
            )
        except (
            CANConnectionError,
            TimeoutError,
            UnsupportedFeatureException,
            ValueError,
        ) as error:
            print(error, file=stderr)
        except StreamingTimeoutError as error:
            print(f"Quitting Measurement: {error}")
        except KeyboardInterrupt:
            pass


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    main()
