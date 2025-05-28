"""Test code for a single node in the ICOtronic system

The code below contains shared code for:

- SHA/STH
- SMH
- STU
"""

# -- Imports ------------------------------------------------------------------

from asyncio import get_running_loop, sleep
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import List, Union
from unittest import IsolatedAsyncioTestCase

from dynaconf.utils.boxing import DynaBox
from semantic_version import Version

from icotronic.can.connection import Connection
from icotronic.can.node.sth import STH
from icotronic.can.status import State
from icotronic.cmdline.commander import Commander
from icotronic.config import settings
from icotronic.can.node.eeprom.status import EEPROMStatus
from icotronic.report.report import Report
from icotronic import __version__

# -- Class --------------------------------------------------------------------


# Use inner test class so we do not execute test methods of base class in
# addition to the test method of the super class.
# Source: https://stackoverflow.com/questions/1323455


# pylint: disable=too-few-public-methods
class BaseTestCases:
    """Collection of base test classes"""

    class TestNode(IsolatedAsyncioTestCase):
        """This class contains shared test code for STH and STU

        You are not supposed to use this class directly. Instead use it as base
        class for your test class.

        Every subclass of this class must set the attribute `node` to an object
        of the correct class of (`can.node`).

        Please note, that this class only connects to the STU. If you also want
        to connect to a sensor node, please overwrite the method `_connect`.

        To add additional test attributes shown in the standard output and
        optionally the PDF, add them as **class** variables to the subclass.
        Then use the **class** method `add_attribute` in the method
        `setUpClass` and use a format string where you reference the class
        variable as value argument. Please do not forget to call `setUpClass`
        of the superclass before you do that.

        The various `_test` methods in this class can be used to run certain
        tests for a node as part of a test method (i.e. a method that starts
        with the string `test`).

        """

        batch_number: int
        eeprom_status: EEPROMStatus
        firmware_version: Version
        gtin: int
        hardware_version: Version
        oem_data: str
        operating_time: int
        power_off_cycles: int
        power_on_cycles: int
        production_date: date
        product_name: str
        release_name: str
        serial_number: str
        under_voltage_counter: int
        watchdog_reset_counter: int

        possible_attributes: List[SimpleNamespace] = []

        @classmethod
        def setUpClass(cls):
            """Set up data for whole test"""

            # Add basic test attributes that all nodes share
            cls.add_attribute(
                "EEPROM Status", "{cls.eeprom_status}", pdf=False
            )
            cls.add_attribute("Name", "{cls.name}")
            cls.add_attribute("Status", "{cls.status}")
            cls.add_attribute(
                "Production Date", "{cls.production_date}", pdf=False
            )
            cls.add_attribute("GTIN", "{cls.gtin}", pdf=False)
            cls.add_attribute("Product Name", "{cls.product_name}", pdf=False)
            cls.add_attribute("Batch Number", "{cls.batch_number}", pdf=False)
            cls.add_attribute("Bluetooth Address", "{cls.bluetooth_mac}")
            cls.add_attribute("RSSI", "{cls.bluetooth_rssi} dBm")
            cls.add_attribute("Hardware Version", "{cls.hardware_version}")
            cls.add_attribute("Firmware Version", "{cls.firmware_version}")
            cls.add_attribute("Release Name", "{cls.release_name}", pdf=False)
            cls.add_attribute("OEM Data", "{cls.oem_data}", pdf=False)
            cls.add_attribute(
                "Power On Cycles", "{cls.power_on_cycles}", pdf=False
            )
            cls.add_attribute(
                "Power Off Cycles", "{cls.power_off_cycles}", pdf=False
            )
            cls.add_attribute(
                "Under Voltage Counter",
                "{cls.under_voltage_counter}",
                pdf=False,
            )
            cls.add_attribute(
                "Watchdog Reset Counter",
                "{cls.watchdog_reset_counter}",
                pdf=False,
            )
            cls.add_attribute(
                "Operating Time", "{cls.operating_time} s", pdf=False
            )

            # Add a basic PDF report
            # Subclasses should overwrite this attribute, if you want to change
            # the default arguments of the report class
            cls.report = Report()

            # We store attributes related to the connection, such as MAC
            # address only once. To do that we set `read_attributes` to true
            # after the test class gathered the relevant data.
            cls.read_attributes = False

        @classmethod
        def tearDownClass(cls):
            """Print attributes of tested STH after all test cases"""

            cls.__output_general_data()
            cls.__output_node_data()
            cls.report.build()

        @classmethod
        def __output_general_data(cls):
            """Print general information and add it to PDF report"""

            now = datetime.now()

            attributes = [
                SimpleNamespace(
                    description="ICOtronic Version",
                    value=__version__,
                    pdf=True,
                ),
                SimpleNamespace(
                    description="Date",
                    value=now.strftime("%Y-%m-%d"),
                    pdf=True,
                ),
                SimpleNamespace(
                    description="Time",
                    value=now.strftime("%H:%M:%S"),
                    pdf=True,
                ),
                SimpleNamespace(
                    description="Operator",
                    value=settings.operator.name,
                    pdf=True,
                ),
            ]

            cls.__output_data(attributes, node_data=False)

        @classmethod
        def __output_node_data(cls):
            """Print node information and add it to PDF report"""

            attributes = []
            for attribute in cls.possible_attributes:
                try:
                    attribute.value = str(attribute.value).format(cls=cls)
                    attributes.append(attribute)
                except (AttributeError, IndexError):
                    pass

            cls.__output_data(attributes)

        @classmethod
        def __output_data(cls, attributes, node_data=True):
            """Output data to standard output and PDF report

            Parameters
            ----------

            attributes:
                An iterable that stores simple name space objects created via
                ``create_attribute``

            node_data:
                Specifies if this method outputs node specific or general data
            """

            # Only output something, if there is at least one attribute
            if not attributes:
                return

            max_length_description = max(
                (len(attribute.description) for attribute in attributes)
            )
            max_length_value = max(
                (len(attribute.value) for attribute in attributes)
            )

            # Print attributes to standard output
            print("\n")
            header = "Attributes" if node_data else "General"
            print(header)
            print("—" * len(header))

            for attribute in attributes:
                print(
                    f"{attribute.description:{max_length_description}} "
                    + f"{attribute.value:>{max_length_value}}"
                )

            # Add attributes to PDF
            attributes_pdf = [
                attribute for attribute in attributes if attribute.pdf
            ]
            for attribute in attributes_pdf:
                cls.report.add_attribute(
                    attribute.description, attribute.value, node_data
                )

        @classmethod
        def add_attribute(
            cls, name: str, value: object, pdf: bool = True
        ) -> None:
            """Add a test attribute

            Parameters
            ----------

            name:
                The description (name) of the attribute

            value:
                The value of the attribute

            pdf:
                True if the attribute should be added to the PDF report

            """

            cls.possible_attributes.append(
                SimpleNamespace(description=name, value=str(value), pdf=pdf)
            )

        async def asyncSetUp(self):
            """Set up hardware before a single test case"""

            # Disable debug mode (set by IsolatedAsyncioTestCase) to improve
            # runtime of code: https://github.com/python/cpython/issues/82789
            get_running_loop().set_debug(False)

            # All tests methods that contain the text `disconnected` do not
            # initialize a Bluetooth connection
            if self._testMethodName.find("disconnected") >= 0:
                return

            await self._connect()

            cls = type(self)
            # Only read node specific data once, even if we run multiple tests
            if not cls.read_attributes:
                cls.bluetooth_mac = await self.node.get_mac_address()
                cls.firmware_version = await self.node.get_firmware_version()
                cls.release_name = await self.node.get_firmware_release_name()
                cls.read_attributes = True

        async def asyncTearDown(self):
            """Clean up after single test case"""

            # All tests methods that contain the text `disconnected` do not
            # initialize a Bluetooth connection
            if self._testMethodName.find("disconnected") >= 0:
                return

            await self._disconnect()

        def run(self, result=None):
            """Execute a single test

            We override this method to store data about the test outcome.
            """

            super().run(result)
            type(self).report.add_test_result(self.shortDescription(), result)

        async def _connect(self):
            """Create a connection to the STU"""

            # pylint: disable=attribute-defined-outside-init
            self.connection = Connection()
            # pylint: disable=unnecessary-dunder-call
            self.node = await self.connection.__aenter__()
            # pylint: enable=unnecessary-dunder-call
            # pylint: enable=attribute-defined-outside-init
            await self.node.reset()
            # Wait for reset to take place
            await sleep(2)

        async def _disconnect(self):
            """Tear down connection to STU"""

            await self.connection.__aexit__(None, None, None)

        async def test_connection(self):
            """Check connection to node"""

            # The sensor nodes need a little more time to switch from the
            # “Startup” to the “Operating” state
            await sleep(1)

            # Just send a request for the state and check, if the result
            # matches our expectations.
            state = await self.node.get_state()

            expected_state = State(
                mode="Get", location="Application", state="Operating"
            )

            self.assertEqual(
                expected_state,
                state,
                f"Expected state “{expected_state}” does not match "
                f"received state “{state}”",
            )

        def _test_firmware_flash(
            self,
            flash_location: Union[str, Path],
            programmmer_serial_number: int,
            chip: str,
        ):
            """Upload bootloader and application into node

            Parameters
            ----------

            flash_location:
                The location of the flash image

            programmer_serial_number:
                The serial number of the programming board

            chip:
                The name of the chip that should be flashed

            """

            image_filepath = Path(flash_location).expanduser().resolve()
            self.assertTrue(
                image_filepath.is_file(),
                f"Firmware file {image_filepath} does not exist",
            )

            commander = Commander(
                serial_number=programmmer_serial_number, chip=chip
            )

            commander.upload_flash(image_filepath)

        async def _test_eeprom_product_data(self, config: DynaBox) -> None:
            """Test if reading and writing the product data EEPROM page works

            Parameters
            ----------

            config
                A configuration object that stores the various product data
                attributes

            """

            cls = type(self)

            node = self.node

            # ========
            # = GTIN =
            # ========

            gtin = config.gtin
            await node.eeprom.write_gtin(gtin)
            cls.gtin = await node.eeprom.read_gtin()
            self.assertEqual(
                gtin,
                cls.gtin,
                f"Written GTIN “{gtin}” does not match read GTIN “{cls.gtin}”",
            )

            # ====================
            # = Hardware Version =
            # ====================

            hardware_version = config.hardware_version
            await node.eeprom.write_hardware_version(hardware_version)
            cls.hardware_version = await node.eeprom.read_hardware_version()
            self.assertEqual(
                hardware_version,
                f"{cls.hardware_version}",
                f"Written hardware version “{hardware_version}” does not "
                + f"match read hardware version “{cls.hardware_version}”",
            )

            # ====================
            # = Firmware Version =
            # ====================

            await node.eeprom.write_firmware_version(cls.firmware_version)
            firmware_version = await node.eeprom.read_firmware_version()
            self.assertEqual(
                f"{cls.firmware_version}",
                f"{firmware_version}",
                f"Written firmware version “{cls.firmware_version}” does not "
                + f"match read firmware version “{firmware_version}”",
            )

            # ================
            # = Release Name =
            # ================

            # Originally we assumed that this value would be set by the
            # firmware itself. However, according to tests with an empty EEPROM
            # this is not the case.
            release_name = config.firmware.release_name
            await node.eeprom.write_release_name(release_name)
            cls.release_name = await node.eeprom.read_release_name()
            self.assertEqual(
                release_name,
                cls.release_name,
                f"Written firmware release name “{release_name}” does not "
                + f"match read firmware release name “{cls.release_name}”",
            )

            # =================
            # = Serial Number =
            # =================

            serial_number = config.serial_number
            await node.eeprom.write_serial_number(serial_number)
            cls.serial_number = await node.eeprom.read_serial_number()
            self.assertEqual(
                serial_number,
                cls.serial_number,
                f"Written serial number “{serial_number}” does not "
                + f"match read serial number “{cls.serial_number}”",
            )

            # ================
            # = Product Name =
            # ================

            product_name = config.product_name
            await node.eeprom.write_product_name(product_name)
            cls.product_name = await node.eeprom.read_product_name()
            self.assertEqual(
                product_name,
                cls.product_name,
                f"Written product name “{product_name}” does not "
                + f"match read product name “{cls.product_name}”",
            )

            # ============
            # = OEM Data =
            # ============

            oem_data = config.oem_data
            await node.eeprom.write_oem_data(oem_data)
            oem_data_list = await node.eeprom.read_oem_data()
            self.assertListEqual(
                oem_data,
                oem_data_list,
                f"Written OEM data “{oem_data}” does not "
                + f"match read OEM data “{oem_data_list}”",
            )
            # We currently store the data in text format, to improve the
            # readability of null bytes in the shell. Please notice, that this
            # will not always work (depending on the binary data stored in
            # EEPROM region).
            cls.oem_data = "".join(map(chr, oem_data_list)).replace("\x00", "")

        async def _test_eeprom_statistics(
            self, production_date: date, batch_number: int
        ) -> None:
            """Test if reading and writing the statistics EEPROM page works

            For this purpose this method writes (default) values into the
            EEPROM, reads them and then checks if the written and read values
            are equal.

            Parameters
            ----------

            production_date:
                The production date of the node

            batch_number:
                The batch number of the node

            """

            cls = type(self)
            node = self.node

            # =======================
            # = Power On/Off Cycles =
            # =======================

            power_on_cycles = 0
            await node.eeprom.write_power_on_cycles(power_on_cycles)
            cls.power_on_cycles = await node.eeprom.read_power_on_cycles()
            self.assertEqual(
                power_on_cycles,
                cls.power_on_cycles,
                f"Written power on cycle value “{power_on_cycles}” "
                + "does not match read power on cycle value "
                + f"“{cls.power_on_cycles}”",
            )

            power_off_cycles = 0
            await node.eeprom.write_power_off_cycles(power_off_cycles)
            cls.power_off_cycles = await node.eeprom.read_power_off_cycles()
            self.assertEqual(
                power_off_cycles,
                cls.power_off_cycles,
                f"Written power off cycle value “{power_off_cycles}” "
                + "does not match read power off cycle value "
                + f"“{cls.power_off_cycles}”",
            )

            # ==================
            # = Operating Time =
            # ==================

            operating_time = 0
            await node.eeprom.write_operating_time(operating_time)
            cls.operating_time = await node.eeprom.read_operating_time()
            self.assertEqual(
                operating_time,
                cls.operating_time,
                f"Written operating time “{operating_time}” "
                + "does not match read operating time “{cls.operating_time}”",
            )

            # =========================
            # = Under Voltage Counter =
            # =========================

            under_voltage_counter = 0
            await node.eeprom.write_under_voltage_counter(
                under_voltage_counter
            )
            cls.under_voltage_counter = (
                await node.eeprom.read_under_voltage_counter()
            )
            self.assertEqual(
                under_voltage_counter,
                cls.under_voltage_counter,
                "Written under voltage counter value"
                f" “{under_voltage_counter}” "
                + "does not match read under voltage counter value "
                + f"“{cls.under_voltage_counter}”",
            )

            # ==========================
            # = Watchdog Reset Counter =
            # ==========================

            watchdog_reset_counter = 0
            await node.eeprom.write_watchdog_reset_counter(
                watchdog_reset_counter
            )
            cls.watchdog_reset_counter = (
                await node.eeprom.read_watchdog_reset_counter()
            )
            self.assertEqual(
                watchdog_reset_counter,
                cls.watchdog_reset_counter,
                "Written watchdog reset counter value"
                f" “{watchdog_reset_counter} does not match read watchdog"
                f" reset counter value “{cls.watchdog_reset_counter}”",
            )

            # ===================
            # = Production Date =
            # ===================

            await node.eeprom.write_production_date(production_date)
            cls.production_date = await node.eeprom.read_production_date()
            self.assertEqual(
                production_date,
                cls.production_date,
                f"Written production date “{production_date}” does not match "
                + f"read production date “{cls.production_date}”",
            )

            # ================
            # = Batch Number =
            # ================

            await node.eeprom.write_batch_number(batch_number)
            cls.batch_number = await node.eeprom.read_batch_number()
            self.assertEqual(
                batch_number,
                cls.batch_number,
                f"Written batch “{batch_number}” does not match "
                + f"read batch number “{cls.batch_number}”",
            )

        async def _test_eeprom_status(self) -> None:
            """Test if reading and writing the EEPROM status byte works"""

            cls = type(self)
            node = self.node

            # =================
            # = EEPROM Status =
            # =================

            await node.eeprom.write_status("Initialized")
            cls.eeprom_status = await node.eeprom.read_status()
            self.assertTrue(
                cls.eeprom_status.is_initialized(),
                "Setting EEPROM status to “Initialized” failed. "
                "EEPROM status byte currently stores the value "
                f"“{cls.eeprom_status}”",
            )

    class TestSensorNode(TestNode):
        """This class contains support code for sensor node (SMH & STH)

        You are not supposed to use this class directly, but instead use it as
        superclass for your test class. For more information, please take a
        look at the documentation of `TestNode`.

        """

        @classmethod
        def setUpClass(cls):
            """Set up data for whole test"""

            super().setUpClass()

            cls.add_attribute("Serial Number", "{cls.serial_number}", pdf=True)
            cls.add_attribute(
                "Ratio Noise Maximum", "{cls.ratio_noise_max:.3f} dB"
            )
            cls.add_attribute(
                "Sleep Time 1", "{cls.sleep_time_1} ms", pdf=False
            )
            cls.add_attribute(
                "Advertisement Time 1",
                "{cls.advertisement_time_1} ms",
                pdf=False,
            )
            cls.add_attribute(
                "Sleep Time 2", "{cls.sleep_time_2} ms", pdf=False
            )
            cls.add_attribute(
                "Advertisement Time 2",
                "{cls.advertisement_time_2} ms",
                pdf=False,
            )

        async def _connect_node(self, name: str) -> None:
            """Create a connection to the node with the specified name

            Parameters
            ----------

            name:
                The (Bluetooth advertisement) name of the sensor node

            """

            await super()._connect()  # Connect to STU
            stu = self.node

            # pylint: disable=attribute-defined-outside-init
            self.sensor_node_connection = stu.connect_sensor_node(name, STH)
            # New node is sensor node
            # pylint: disable=unnecessary-dunder-call
            self.node = await self.sensor_node_connection.__aenter__()
            # pylint: enable=unnecessary-dunder-call
            self.stu = stu

        async def _disconnect_node(self) -> None:
            """Disconnect from sensor node and STU"""

            await self.sensor_node_connection.__aexit__(None, None, None)
            await super()._disconnect()  # Disconnect from STU

        async def _test_name(self, name: str) -> str:
            """Check if writing and reading the name of a sensor node works

            Parameters
            ----------

            name:
                The text that should be used as name for the sensor node

            Returns
            -------

            Read back name

            """

            node = self.node
            await node.eeprom.write_name(name)
            read_name = await node.eeprom.read_name()

            self.assertEqual(
                name,
                read_name,
                f"Written name “{name}” does not match read name"
                f" “{read_name}”",
            )

            return read_name

        async def _test_eeprom_sleep_advertisement_times(self):
            """Test if reading and writing sleep/advertisement times works"""

            async def read_write_time(
                read_function,
                write_function,
                variable,
                description,
                milliseconds,
            ):
                await write_function(milliseconds)
                milliseconds_read = round(await read_function())
                setattr(type(self), variable, milliseconds_read)
                self.assertEqual(
                    milliseconds_read,
                    milliseconds,
                    f"{description} {milliseconds_read} ms does not match "
                    f" written value of {milliseconds} ms",
                )

            await read_write_time(
                read_function=self.node.eeprom.read_sleep_time_1,
                write_function=self.node.eeprom.write_sleep_time_1,
                variable="sleep_time_1",
                description="Sleep Time 1",
                milliseconds=settings.sensor_node.bluetooth.sleep_time_1,
            )

            await read_write_time(
                read_function=self.node.eeprom.read_advertisement_time_1,
                write_function=self.node.eeprom.write_advertisement_time_1,
                variable="advertisement_time_1",
                description="Advertisement Time 1",
                milliseconds=(
                    settings.sensor_node.bluetooth.advertisement_time_1
                ),
            )

            await read_write_time(
                read_function=self.node.eeprom.read_sleep_time_2,
                write_function=self.node.eeprom.write_sleep_time_2,
                variable="sleep_time_2",
                description="Sleep Time 2",
                milliseconds=settings.sensor_node.bluetooth.sleep_time_2,
            )

            await read_write_time(
                read_function=self.node.eeprom.read_advertisement_time_2,
                write_function=self.node.eeprom.write_advertisement_time_2,
                variable="advertisement_time_2",
                description="Advertisement Time 2",
                milliseconds=(
                    settings.sensor_node.bluetooth.advertisement_time_2
                ),
            )


# pylint: enable=too-few-public-methods
