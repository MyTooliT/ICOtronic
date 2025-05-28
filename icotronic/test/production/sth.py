"""Test code for sensory tool holder (STH)/ assembly (SHA)

The difference between the SHA and the STH is that the SHA denotes only the
PCB while an STH also includes the tool holder that contains the SHA.
"""

# -- Imports ------------------------------------------------------------------

from itertools import chain, repeat
from time import time
from typing import List
from unittest import main as unittest_main, skipIf

from semantic_version import Version

from icotronic.can.streaming import StreamingConfiguration
from icotronic.config import settings
from icotronic.measurement.acceleration import (
    convert_raw_to_g,
    ratio_noise_max,
)
from icotronic.measurement.constants import ADC_MAX_VALUE
from icotronic.report.report import Report
from icotronic.utility.naming import convert_mac_base64
from icotronic.test.unit import ExtendedTestRunner
from icotronic.test.production.node import BaseTestCases

# -- Classes ------------------------------------------------------------------


class TestSTH(BaseTestCases.TestSensorNode):
    """This class contains tests for the Sensory Tool Holder (STH)"""

    @classmethod
    def setUpClass(cls):
        """Set up data for whole test"""

        super().setUpClass()

        cls.add_attribute("Holder Type", "{cls.holder_type}", pdf=True)
        cls.add_attribute(
            "Acceleration Sensor", "{cls.acceleration_sensor}", pdf=True
        )

        for axis in "xyz":
            cls.add_attribute(
                f"Acceleration Slope {axis.upper()}",
                "{cls.acceleration_slope_" + axis + ":.5f}",
                pdf=False,
            )
            cls.add_attribute(
                f"Acceleration Offset {axis.upper()}",
                "{cls.acceleration_offset_" + axis + ":.3f}",
                pdf=False,
            )

        cls.report = Report(node="STH")

        # Add data that only applies to the STH
        cls.holder_type = settings.sth.holder_type
        cls.status = settings.sth.status

        sensor_name = settings.sth.acceleration_sensor.sensor
        maximum_acceleration = (
            settings.acceleration_sensor().acceleration.maximum
        )
        cls.acceleration_sensor = (
            f"±{maximum_acceleration // 2} g Sensor ({sensor_name})"
        )

        # Manual checks
        cls.report.add_checkbox_list(
            title="Metal Blank",
            boxes=[
                "Okay",
                "Cylindrical thread defect",
                "Dent",
                "Oil spillage",
                "Shavings",
                "Milling errors",
            ],
            text_fields=1,
        )

        cls.report.add_checkbox_list(
            title="PCB",
            boxes=["Optical inspection: no defects"],
            text_fields=1,
        )

        cls.report.add_checkbox_list(
            title="Before Resin Cast",
            boxes=[
                "Battery test successful",
                "Charge in charging station was successful",
            ],
            text_fields=2,
        )

        cls.report.add_checkbox_list(
            title="Final Checks",
            boxes=[
                "Resin cast contains no bubbles",
                "Resin cast hardened completely",
                "No resin residue outside of pocket",
                "Pocket is completely filled with resin",
                "No oil spillage in vacuum chamber",
                "Charge in charging station was successful",
            ],
            text_fields=2,
        )

    async def asyncSetUp(self):
        """Set up hardware before a single test case"""

        await super().asyncSetUp()

        # Sensor node is connected after set up function unless the test
        # does not initiate a Bluetooth connection, which is the case if
        # the test name (method name) contains the text “disconnected”.
        if self._testMethodName.find("disconnected") < 0:
            # Change reference voltage depending on acceleration sensor
            reference_voltage = (
                settings.acceleration_sensor().reference_voltage
            )

            await self.node.set_adc_configuration(
                prescaler=2,
                acquisition_time=8,
                oversampling_rate=64,
                reference_voltage=reference_voltage,
            )

    async def _connect(self):
        """Create a connection to the STH"""

        await super()._connect_node(settings.sth_name())

    async def _disconnect(self):
        """Tear down connection to STH"""

        await super()._disconnect_node()

    @skipIf(
        settings.sth.status == "Epoxied",
        f"Flash test skipped because of status “{settings.sth.status}”",
    )
    def test__firmware_flash_disconnected(self):
        """Upload bootloader and application into STH

        Please note the additional underscore in the method name that makes
        sure this test case is executed before all other test cases.

        The text `disconnected` in the method name makes sure that the test
        framework does not initialize a connection.

        """

        try:
            hardware_version = Version(settings.sth.hardware_version)
        except (TypeError, ValueError) as error:
            raise ValueError(
                "Incorrect STH hardware version: "
                f"“{settings.sth.hardware_version}”"
            ) from error

        if not 1 <= hardware_version.major <= 2:
            raise ValueError(
                f"STH hardware version “{hardware_version}” "
                "is currently not supported"
            )

        chip = (
            "BGM113A256V2" if hardware_version.major <= 1 else "BGM123A256V2"
        )

        self._test_firmware_flash(
            flash_location=settings.sth.firmware.location.flash,
            programmmer_serial_number=(
                settings.sth.programming_board.serial_number
            ),
            chip=chip,
        )

    async def test_battery_voltage(self):
        """Test voltage of STH power source"""

        supply_voltage = await self.node.get_supply_voltage()
        expected_voltage = settings.sth.battery_voltage.average
        tolerance_voltage = settings.sth.battery_voltage.tolerance
        expected_minimum_voltage = expected_voltage - tolerance_voltage
        expected_maximum_voltage = expected_voltage + tolerance_voltage

        self.assertGreaterEqual(
            supply_voltage,
            expected_minimum_voltage,
            f"STH supply voltage of {supply_voltage:.3f} V is lower "
            "than expected minimum voltage of "
            f"{expected_minimum_voltage:.3f} V",
        )
        self.assertLessEqual(
            supply_voltage,
            expected_maximum_voltage,
            f"STH supply voltage of {supply_voltage:.3f} V is "
            "greater than expected maximum voltage of "
            f"{expected_minimum_voltage:.3f} V",
        )

    async def test_acceleration_single_value(self):
        """Test stationary acceleration value"""

        sensor = settings.acceleration_sensor()
        stream_data = await self.node.get_streaming_data_single()
        acceleration = convert_raw_to_g(
            stream_data.values[0], sensor.acceleration.maximum
        )

        # We expect a stationary acceleration between -g₀ and g₀
        # (g₀ = 9.807 m/s²)
        expected_acceleration = 0
        tolerance_acceleration = sensor.acceleration.tolerance
        expected_minimum_acceleration = (
            expected_acceleration - tolerance_acceleration
        )
        expected_maximum_acceleration = (
            expected_acceleration + tolerance_acceleration
        )

        self.assertGreaterEqual(
            acceleration,
            expected_minimum_acceleration,
            f"Measured acceleration {acceleration:.3f} g is lower "
            "than expected minimum acceleration "
            f"{expected_minimum_acceleration:.3f} g",
        )
        self.assertLessEqual(
            acceleration,
            expected_maximum_acceleration,
            f"Measured acceleration {acceleration:.3f} g is greater "
            "than expected maximum acceleration "
            f"{expected_maximum_acceleration:.3f} g",
        )

    async def test_acceleration_noise(self):
        """Test ratio of noise to maximal possible measurement value"""

        async def read_streaming_data():
            """Read streaming data of first channel"""
            stream_data = []
            seconds = 4
            async with self.node.open_data_stream(
                StreamingConfiguration(first=True)
            ) as stream:
                end_time = time() + seconds
                async for data, _ in stream:
                    stream_data.extend(data.values)
                    if time() > end_time:
                        break

            return stream_data

        acceleration = await read_streaming_data()

        cls = type(self)
        cls.ratio_noise_max = ratio_noise_max(acceleration)

        sensor = settings.acceleration_sensor()
        maximum_ratio_allowed = sensor.acceleration.ratio_noise_to_max_value
        self.assertLessEqual(
            cls.ratio_noise_max,  # pylint: disable=no-member
            maximum_ratio_allowed,
            (
                "The ratio noise to possible maximum measured value of "
                f"{cls.ratio_noise_max} dB "  # pylint: disable=no-member
                "is higher than the maximum allowed level of "
                f" {maximum_ratio_allowed} dB"
            ),
        )

    async def test_acceleration_self_test(self):
        """Execute self test of accelerometer"""

        async def read_voltages(dimension, reference_voltage) -> List[int]:
            """Read acceleration voltages in millivolts"""

            before = await self.node.get_acceleration_voltage(
                dimension, reference_voltage
            )

            await self.node.activate_acceleration_self_test(dimension)
            between = await self.node.get_acceleration_voltage(
                dimension, reference_voltage
            )

            await self.node.deactivate_acceleration_self_test(dimension)
            after = await self.node.get_acceleration_voltage(
                dimension, reference_voltage
            )

            return [round(value * 1000) for value in (before, between, after)]

        sensor = settings.acceleration_sensor()

        (
            voltage_before_test,
            voltage_at_test,
            voltage_after_test,
        ) = await read_voltages(
            sensor.self_test.dimension, sensor.reference_voltage
        )

        voltage_diff = voltage_at_test - voltage_before_test
        voltage_diff_abs = abs(voltage_diff)
        voltage_diff_before_after = abs(
            voltage_before_test - voltage_after_test
        )

        # - Voltage difference can be both positive or negative
        # - Voltage before and after the self test should be roughly the same

        voltage_diff_expected = sensor.self_test.voltage.difference
        voltage_diff_tolerance = sensor.self_test.voltage.tolerance

        voltage_diff_minimum = voltage_diff_expected - voltage_diff_tolerance
        voltage_diff_maximum = voltage_diff_expected + voltage_diff_tolerance

        self.assertLessEqual(
            voltage_diff_before_after,
            voltage_diff_tolerance,
            "Measured voltage difference between voltage before and after "
            f"test {voltage_diff_before_after:.0f} mV is larger than "
            f"tolerance of {voltage_diff_tolerance:.0f} mV",
        )

        possible_failure_reason = (
            "\n\nPossible Reason:\n\n• Acceleration sensor config value "
            f"“{settings.sth.acceleration_sensor.sensor}” is incorrect"
        )

        self.assertGreaterEqual(
            voltage_diff_abs,
            voltage_diff_minimum,
            f"Measured voltage difference of {voltage_diff_abs:.0f} mV is "
            "lower than expected minimum voltage difference of "
            f"{voltage_diff_minimum:.0f} mV{possible_failure_reason}",
        )
        self.assertLessEqual(
            voltage_diff_abs,
            voltage_diff_maximum,
            f"Measured voltage difference of {voltage_diff_abs:.0f} mV is "
            "greater than expected minimum voltage difference of "
            f"{voltage_diff_maximum:.0f} mV{possible_failure_reason}",
        )

    # pylint: disable=too-many-locals

    async def test_eeprom(self):
        """Test if reading and writing the EEPROM works"""

        cls = type(self)

        # ========
        # = Name =
        # ========

        name = (
            settings.sth.serial_number
            if settings.sth.status == "Epoxied"
            else convert_mac_base64(
                cls.bluetooth_mac  # pylint: disable=no-member
            )
        )
        cls.name = await self._test_name(name)

        # =========================
        # = Sleep & Advertisement =
        # =========================

        await self._test_eeprom_sleep_advertisement_times()

        # ================
        # = Product Data =
        # ================

        await self._test_eeprom_product_data(settings.sth)

        # ==============
        # = Statistics =
        # ==============

        await self._test_eeprom_statistics(
            settings.sth.production_date,
            settings.sth.batch_number,
        )

        # ================
        # = Acceleration =
        # ================

        sensor = settings.acceleration_sensor()
        acceleration_max = sensor.acceleration.maximum
        adc_max = ADC_MAX_VALUE
        acceleration_slope = acceleration_max / adc_max
        acceleration_offset = -(acceleration_max / 2)

        # pylint: disable=too-many-arguments, too-many-positional-arguments

        async def write_read_check(
            class_variable, write_routine, value, read_routine, axis, name
        ):
            await write_routine(value)
            setattr(cls, class_variable, await read_routine())
            read_value = getattr(cls, class_variable)
            self.assertAlmostEqual(
                value,
                read_value,
                msg=(
                    f"Written {axis} acceleration {name} "
                    f"“{acceleration_slope:.5f}” does not match read "
                    f"{axis} acceleration {name} "
                    f"“{read_value:.5f}”"
                ),
            )

        # pylint: enable=too-many-arguments, too-many-positional-arguments

        class_variables = (
            "acceleration_slope_x",
            "acceleration_slope_y",
            "acceleration_slope_z",
            "acceleration_offset_x",
            "acceleration_offset_y",
            "acceleration_offset_z",
        )
        write_routines = (
            self.node.eeprom.write_x_axis_acceleration_slope,
            self.node.eeprom.write_y_axis_acceleration_slope,
            self.node.eeprom.write_z_axis_acceleration_slope,
            self.node.eeprom.write_x_axis_acceleration_offset,
            self.node.eeprom.write_y_axis_acceleration_offset,
            self.node.eeprom.write_z_axis_acceleration_offset,
        )
        read_routines = (
            self.node.eeprom.read_x_axis_acceleration_slope,
            self.node.eeprom.read_y_axis_acceleration_slope,
            self.node.eeprom.read_z_axis_acceleration_slope,
            self.node.eeprom.read_x_axis_acceleration_offset,
            self.node.eeprom.read_y_axis_acceleration_offset,
            self.node.eeprom.read_z_axis_acceleration_offset,
        )
        names = chain(*(repeat("slope", 3), repeat("offset", 3)))
        values = chain(*(
            repeat(acceleration_slope, 3),
            repeat(acceleration_offset, 3),
        ))
        axes = list("xyz") * 2

        for (
            class_variable,
            write_routine,
            value,
            read_routine,
            axis,
            name,
        ) in zip(
            class_variables,
            write_routines,
            values,
            read_routines,
            axes,
            names,
        ):
            await write_read_check(
                class_variable,
                write_routine,
                value,
                read_routine,
                axis,
                name,
            )

        # =================
        # = EEPROM Status =
        # =================

        await self._test_eeprom_status()

        # =========
        # = Reset =
        # =========

        # We reset the STH and STU to make sure
        # - the name change takes place and we can connect to the STH
        #   using the new name
        # - the STH also takes the other changed EEPROM values (such as
        #   the changed advertisement times) into account.
        await self.node.reset()
        await self.stu.reset()

        try:
            async with self.stu.connect_sensor_node(
                cls.name  # pylint: disable=no-member
            ):
                pass  # Reconnected to STH
        except TimeoutError:
            self.fail(
                "Unable to reconnect to STH using updated name "
                f"“{cls.name}”"  # pylint: disable=no-member
            )

    # pylint: enable=too-many-locals


def main():
    """Run production test for Sensory Tool Holder (STH)"""

    unittest_main(
        testRunner=ExtendedTestRunner, module="icotronic.test.production.sth"
    )


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    main()
