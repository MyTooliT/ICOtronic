"""ICOn command line tool

See: https://mytoolit.github.io/ICOtronic/#icon-cli-tool

for more information
"""

# -- Imports ------------------------------------------------------------------

from argparse import Namespace
from asyncio import run
from logging import basicConfig, getLogger
from sys import exit as sys_exit, stderr
from tempfile import NamedTemporaryFile
from time import monotonic, perf_counter_ns, process_time_ns

from can.exceptions import CanOperationError
from can.interfaces.pcan import PcanError
from tqdm import tqdm

from icotronic.can import Connection
from icotronic.can.adc import ADCConfiguration
from icotronic.can.error import CANConnectionError, UnsupportedFeatureException
from icotronic.can.node.sensor import SensorNode
from icotronic.can.sensor import SensorConfiguration
from icotronic.can.streaming import StreamingBufferError, StreamingTimeoutError
from icotronic.cmdline.parse import create_icon_parser
from icotronic.config import ConfigurationUtility, settings
from icotronic.measurement.storage import Storage, StorageData
from icotronic.utility.performance import PerformanceMeasurement

# -- Functions ----------------------------------------------------------------


def command_config() -> None:
    """Open configuration file"""

    ConfigurationUtility.open_user_config()


# pylint: disable=too-many-locals


async def read_data(
    sensor_node: SensorNode,
    sensor_config: SensorConfiguration,
    storage: StorageData,
    measurement_time_s: float,
) -> PerformanceMeasurement:
    """Read some acceleration data from the given sensor node

    Args:

        sensor_node:
            The sensor node from which data should be read

        sensor_config:
            The sensor configuration that should be used for reading data

        storage:
            The storage object that should be used to store the acceleration
            data

        measurement_time_s:
            The amount of time that should be used for reading data

    Returns:

        Information about the performance of the streaming code

    """

    streaming_config = sensor_config.streaming_configuration()
    logger = getLogger(__name__)
    logger.info("Streaming Configuration: %s", streaming_config)

    sample_rate = (await sensor_node.get_adc_configuration()).sample_rate()
    progress = tqdm(
        total=int(sample_rate * measurement_time_s),
        desc="Read sensor data",
        unit=" values",
        leave=False,
        disable=None,
    )

    values_per_message = streaming_config.data_length()

    performance_measurement = PerformanceMeasurement()
    try:
        async with sensor_node.open_data_stream(streaming_config) as stream:
            performance_measurement.start()
            start_time = monotonic()
            async for data, _ in stream:
                storage.add_streaming_data(data)
                progress.update(values_per_message)
                if monotonic() - start_time >= measurement_time_s:
                    break
            performance_measurement.stop()
    except PcanError as error:
        print(
            f"Unable to collect streaming data: {error}",
            file=stderr,
        )
    except KeyboardInterrupt:
        pass
    finally:
        progress.close()

    return performance_measurement


# pylint: enable=too-many-locals


def print_dataloss_data(storage: StorageData) -> None:
    """Print information about data loss

    Args:

        storage:
            The data that should be analyzed for data loss

    """

    data_time_us = float(storage.measurement_time())
    data_time_s = data_time_us / 10**6
    dataloss = storage.dataloss()
    data_loss_status = (
        "🟢"
        if dataloss < 0.01
        else ("🟡" if dataloss < 0.05 else ("🟠" if dataloss < 0.1 else "🔴"))
    )

    dataloss_percent = storage.dataloss() * 100
    sample_rate_data = storage.sampling_frequency()
    sample_rate = storage["Sample_Rate"]
    print(
        "ADC:\n"
        f"  Sample Rate:      {sample_rate}\n"
        "Measurement:\n"
        f"  Sample Rate:      {sample_rate_data:.2f} Hz\n"
        f"  Data Loss:        {dataloss_percent:.2f} % "
        f"{data_loss_status}\n"
        f"  Measurement Time: {data_time_s:.2f} s"
    )


async def command_dataloss(arguments: Namespace) -> None:
    """Check data loss at different sample rates

    Args:

        arguments:
            The given command line arguments

    """

    identifier = arguments.identifier
    measurement_time_s = arguments.time

    logger = getLogger(__name__)

    async with Connection() as stu:
        logger.info("Connecting to “%s”", identifier)
        async with stu.connect_sensor_node(identifier) as sensor_node:
            logger.info("Connected to “%s”", identifier)

            sensor_config = SensorConfiguration(first=1)

            oversampling_rates = [2**exponent for exponent in range(6, 10)]
            for oversampling_rate in oversampling_rates:
                logger.info("Oversampling rate: %s", oversampling_rate)
                adc_config = ADCConfiguration(
                    prescaler=2,
                    acquisition_time=8,
                    oversampling_rate=oversampling_rate,
                )
                await sensor_node.set_adc_configuration(**adc_config)
                logger.info("Sample rate: %s Hz", adc_config.sample_rate())

                with NamedTemporaryFile(
                    suffix=".hdf5", delete_on_close=False
                ) as temp:
                    logger.info("Temporary measurement file: %s", temp.name)
                    with Storage(
                        temp.name, sensor_config.streaming_configuration()
                    ) as storage:
                        storage.write_sample_rate(adc_config)

                        try:
                            performance = await read_data(
                                sensor_node,
                                sensor_config,
                                storage,
                                measurement_time_s,
                            )
                        except StreamingBufferError as error:
                            print(f"⚠️ {error}", file=stderr)
                        finally:
                            print_dataloss_data(storage)

                        print("Performance:")
                        print(f"  {performance}")

                        print(
                            (
                                ""
                                if oversampling_rate == oversampling_rates[-1]
                                else "\n"
                            ),
                            end="",
                        )


async def command_list(
    arguments: Namespace,  # pylint: disable=unused-argument
) -> None:
    """Print a list of available sensor nodes

    Args:

        arguments:
            The given command line arguments

    """

    async with Connection() as stu:
        sensor_nodes = await stu.collect_sensor_nodes()

        for node in sensor_nodes:
            print(node)


async def command_measure(arguments: Namespace) -> None:
    """Open measurement stream and store data

    Args:

        arguments:
            The given command line arguments

    """

    identifier = arguments.identifier
    measurement_time_s = arguments.time

    async with Connection() as stu:
        async with stu.connect_sensor_node(identifier) as sensor_node:

            adc_config = ADCConfiguration(
                reference_voltage=arguments.voltage_reference,
                prescaler=arguments.prescaler,
                acquisition_time=arguments.acquisition,
                oversampling_rate=arguments.oversampling,
            )
            await sensor_node.set_adc_configuration(**adc_config)
            print(f"Sample Rate: {adc_config.sample_rate():.2f} Hz")

            user_sensor_config = SensorConfiguration(
                first=arguments.first_channel,
                second=arguments.second_channel,
                third=arguments.third_channel,
            )

            if user_sensor_config.requires_channel_configuration_support():
                try:
                    await sensor_node.set_sensor_configuration(
                        user_sensor_config
                    )
                except UnsupportedFeatureException as exception:
                    raise UnsupportedFeatureException(
                        f"Sensor channel configuration “{user_sensor_config}”"
                        f" is not supported by the sensor node “{identifier}”"
                    ) from exception

            filepath = settings.get_output_filepath()

            with Storage(
                filepath, user_sensor_config.streaming_configuration()
            ) as storage:
                storage.write_sample_rate(adc_config)

                try:
                    await read_data(
                        sensor_node,
                        user_sensor_config,
                        storage,
                        measurement_time_s,
                    )
                except KeyboardInterrupt:
                    pass
                finally:
                    print(f"Data Loss: {storage.dataloss() * 100} %")
                    print(f"Filepath: {filepath}")


async def command_rename(arguments: Namespace) -> None:
    """Rename a sensor node

    Args:

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

    Args:

        arguments:
            The given command line arguments

    """

    subcommand = arguments.stu_subcommand

    async with Connection() as stu:
        if subcommand == "mac":
            print(await stu.get_mac_address())
        elif subcommand == "reset":
            await stu.reset()
        else:
            raise ValueError(f"Unknown STU subcommand “{subcommand}”")


def exit_error(message: str) -> None:
    """Exit the program with an error status

    Args:

        message:

            The message that should be printed to `stderr` as error reason

    """

    print(message, file=stderr)
    sys_exit(1)


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
        encoding="utf-8",
        format="{asctime} {levelname:7} {name:10} {message}",
        level=arguments.log.upper(),
        style="{",
    )

    logger = getLogger(__name__)
    logger.info("CLI Arguments: %s", arguments)

    if arguments.subcommand == "config":
        command_config()
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
            CanOperationError,
            StreamingBufferError,
            TimeoutError,
            UnsupportedFeatureException,
            ValueError,
        ) as error:
            exit_error(error)
        except StreamingTimeoutError as error:
            exit_error(f"Quitting Measurement: {error}")
        except KeyboardInterrupt:
            pass


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    main()
