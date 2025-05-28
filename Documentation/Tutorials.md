# Tutorials

## Changing Configuration Values

> **Note:** If you only use the `icon` command line tool, then you most probably do not need to change the configuration at all.

All configuration options are currently stored in [YAML](https://yaml.org) files (handled by the configuration library [Dynaconf][]). The [default values][] are stored inside the package itself. If you want to overwrite or extend these values you should create a user configuration file. To do that you can use the command:

```sh
icon config
```

which will open the the user configuration in your default text editor. You can then edit this file and save your changes to update the configuration. For a list of available options, please take a look at the [default configuration][default values]. Please make sure to not make any mistakes when you edit this file. Otherwise (parts of) the ICOtronic commands will not work, printing an error message about the (first) incorrect configuration value.

[Dynaconf]: https://www.dynaconf.com
[default values]: https://github.com/MyTooliT/ICOtronic/blob/main/icotronic/config/config.yaml

### Adding the Path to Simplicity Commander on Linux

1. Open the user configuration file in your default text editor using the command line tool `icon`:

   ```sh
   icon config
   ```

2. Add the path to Simplicity commander (e.g. `/opt/Simplicity Commander/commander/`) to the list `commands` → `path` → `linux`:

   ```yaml
   commands:
     path:
       linux:
         - /opt/Simplicity Commander/commander/
   ```

   > **Note:** Keys (such as `commands`, `path` and `linux`) in the example above are case-insensitive in [Dynaconf][], e.g. it does not matter if you use `commands` or `COMMANDS` in the example above.

3. Store the modified configuration file

### Setting up the Test Environment

1. Open the user configuration in your default text editor:

   ```sh
   icon config
   ```

   If you never edited the configuration before, then the displayed text should be the same as in the file linked [here](https://github.com/MyTooliT/ICOtronic/blob/main/icotronic/config/user.yaml).

2. Change the **programming board serial number**, to the serial number of your programming board (shown on the bottom of the display):

   ```yaml
   # Use the programmer with serial number 440069950:
   programming board serial number: &programmer_serial 440069950
   ```

3. Change the production date to the one of your PCB in [ISO date format](https://en.wikipedia.org/wiki/ISO_8601):

   ```yaml
   # Use the production date “February the 1st of the year 3456”
   production date: &production_date 3456-02-01
   ```

4. Change the user name to the name of the person that runs the test:

   ```yaml
   # Use “Jane Doe” as name for the test operator
   user name: &username Jane Doe
   ```

5. Change the holder type (only relevant for the test report):

   ```yaml
   # Specify the holder type (the holder that contains the PCB)
   # as “D 10x130 HSK-A63”
   holder type: &holder_type D 10x130 HSK-A63
   ```

6. Change the holder name (Bluetooth advertisement name) to the one of your sensor node. If your are not sure about the name you can use the [`icon`](#icon-cli-tool) command line tool to determine the name. The STH and SMH tests use this value to connect to the node.

   ```yaml
   # Connect to the sensor node with the name “untested”
   holder name: &holder_name untested
   ```

7. Update the serial number of the sensor node. The STH and SMH tests change the sensor node Bluetooth advertisement name to this value, after the EEPROM (part of the) test was executed, **if the state value is set to `Epoxied`**.

   ```yaml
   # Use the value “tested” as sensor node name,
   # after the EEPROM test (succeeded)
   holder serial number: &holder_serial tested
   ```

8. Change the state value to

   - `Bare PCB`, if the **sensor node test** (SMH/STH test) should flash **the sensor node** or to
   - `Epoxied` if the test should not flash the sensor node.

   ```yaml
   # Do not flash the chip in the SMH/STH test
   state: &state Epoxied
   ```

## ICOn CLI Tool

### Help

To show the available subcommands and options of `icon` you can use the option `-h` or `--help`:

```sh
icon -h
```

To show the available options for a certain subcommand add the subcommand before the option. For example, to show the help text for the subcommand `measure` you can use the following command:

```sh
icon measure -h
```

### Listing Available Sensor Nodes

To print a list of all available sensor nodes, including their identifiers (name, MAC address, node number), please use the subcommand `list`:

```sh
icon list
```

### Collecting Measurement Data

To collect and store measurement data from an STH you can uses the subcommand `measure`:

```sh
icon measure
```

By default the command will collect streaming data for 10 seconds for the first measurement channel and store the data in a file starting with the name `Measurement` and the extension `.hdf5` in the current working directory.

#### Specifying the Sensor Hardware

The `measure` subcommand requires that you specify one of the identifiers of a sensor node.

To connect to a sensor node by **name** use the option `-n` or `--name`. For example, the command below collects data from the sensor node with the name `Test-STH`:

```sh
icon measure -n 'Test-STH'
```

You can also use the MAC address to connect to a certain sensor node with the option `-m` or `--mac-address`:

```sh
icon measure -m '08-6B-D7-01-DE-81'
```

To connect using the node number use the option `-d` or `--node-number`:

```sh
icon measure -d 0
```

#### Changing the Run Time

To change the run time of the measurement you can use the option `-t`, which takes the runtime in seconds as argument. The command

```sh
icon measure -t 300
```

for example, changes the runtime to 300 seconds (5 minutes).

#### Channel Selection

To enable the measurement for the first (“x”) channel and second (“y”) measurement channel for

- an “older” STH (Firmware `2.x`, `BGM113` chip) or
- a “newer” STH (Firmware `3.x`, `BGM121` chip)

you can use the following command:

```sh
icon measure -1 1 -2 2 -3 0
```

Here:

- `0` indicates that you want to disable the specified measurement channel, while
- using the same number for the measurement channel (option) and the sensor/hardware channel (argument for the option) specifies that you want to use the specified channel.

Since the default value

- for the option `-1` is already `1`, and
- for the option `-3` is already `0`

you can also leave out these options to arrive at the shorter command:

```
icon measure -2 2
```

> **Note:** Due to a problem in the current firmware the amount of **paket loss is much higher**, if you
>
> - use the standard ADC configuration values, and
> - enable data transmission for **exactly 2 (channels)**.
>
> We strongly recommend you **use either one or three channels**.

For newer STH versions (Firmware `3.x`, `BGM121` chip) or SMHs (Sensory Milling Heads) you can also change the hardware/sensor channel for the first, second and third measurement channel. For example, to select

- hardware channel 8 for the first measurement channel
- hardware channel 1 for the second measurement channel, and
- hardware channel 3 for the third measurement channel

you can use the following command:

```sh
icon measure -1 8 -2 1 -3 3
```

If you just want to enable/set a measurement channel and use the hardware channel with the same number you can also just leave the argument for the specific measurement channel empty. For example, to use

- hardware channel 1 for measurement channel 1,
- hardware channel 2 for measurement channel 2, and
- hardware channel 3 for measurement channel 3

you can use the following command:

```sh
icon measure -1 -2 -3
```

or even shorter, since the default value for measurement channel 1 is hardware channel 1:

```
icon measure -2 -3
```

#### Changing the Reference Voltage

For certain sensor nodes you have to change the reference voltage to retrieve a proper measurement value. For example, STHs that use a ± 40 g acceleration sensor ([ADXL356](https://www.analog.com/en/products/adxl356.html)) require a reference voltage of 1.8 V instead of the usual supply voltage (`VDD`) of 3.3 V. To select the correct reference voltage for these nodes at startup use the option `-v 1.8`:

```sh
icon measure -v 1.8
```

#### Changing the Sampling Rate

You can change the sampling rate by modifying the parameters of the ADC (analog digital converter). There are 3 parameters which influence the sampling rate.

- **Prescaler**: Prescaler used by the ADC to get the sample points (`-s`, `--prescaler`)
- **Acquisition Time**: Time the ADC holds a value to get a sampling point (`-a`, `--acquisition`)
- **Oversampling Rate**: Oversampling rate of the ADC (`-o`, `--oversampling`)

The formula which can be used to calculate the sampling rate can be found in the [documentation of the CAN commands](https://mytoolit.github.io/Documentation/#sampling-rate). Please be aware that the actual sample rate might be slightly lower, even if there is no data loss.

For example, to use a sampling rate of about 2381 Hz you can use the following command:

```sh
icon measure --prescaler 2 --acquisition 8 --oversampling 256
```

### Renaming a Sensor Node {#tutorials:section:sth-renaming}

To change the name of a sensor you can use the subcommand `rename`. For example, to change the name of the sensor node with the Bluetooth MAC address `08-6B-D7-01-DE-81` to `Test-STH` use the following command:

```sh
icon rename -m 08-6B-D7-01-DE-81 Test-STH
```

For more information about the command you can use the option `-h`/`--help`:

```sh
icon rename -h
```

### Opening the User Configuration

To open the user configuration file, you can use the subcommand `config`:

```sh
icon config
```

If the file does not exist yet, then it will be created and filled with the content of the [default user configuration](https://github.com/MyTooliT/ICOtronic/blob/main/icotronic/config/user.yaml). For more information on how to change the configuration, please take a look [here](#changing-configuration-values).

### STU Commands

To list all available STU subcommands, please use the option `-h` (or `--help`):

```sh
icon stu -h
```

#### Enable STU OTA Mode

To enable the Bluetooth advertising of the STU and hence the “over the air” firmware update, please run the following command:

```sh
icon stu ota
```

#### Retrieve the Bluetooth STU MAC Address

To retrieve the STU Bluetooth address you can use the following command:

```sh
icon stu mac
```

#### Reset STU

To reset the STU please use the following command:

```sh
icon stu reset
```

## Production Tests {#tutorials:section:production-tests}

This tutorial lists the usual steps to test a sensory holder assembly or a sensory tool holder.

### General {#tutorials:section:general}

To run the production tests for one of the ICOtronic nodes, please execute one of the following commands:

| Node                                                     | Command    |
| -------------------------------------------------------- | ---------- |
| Stationary Transceiver Unit (STU)                        | `test-stu` |
| Sensory Holder Assembly (SHA), Sensory Tool Holder (STH) | `test-sth` |
| Sensory Milling Head (SMH)                               | `test-smh` |

For a list of available command line options, please use the option `-h` after one of the commands e.g.:

```sh
test-sth -h
```

#### Specific Tests

To only run a single test you need the specify its name. For example, to run the test `test__firmware_flash` of the STU you can use the following command:

```sh
test-stu TestSTU.test__firmware_flash
```

You can also run specific tests using pattern matching. To do that use the command line option `-k`. For example, to run the firmware flash and the connection test of the STH test you can use the command:

```sh
test-sth -k flash -k connection
```

which executes all tests that contain the text `flash` or `connection`.

### STH {#tutorials:section:sth}

The text below gives you a more detailed step-by-step guide on how to run the tests of the STH.

1. > **Note:** You can **skip this step, if you do not want to run the flash test**. To skip the flash test, please set `sth` → `status` in the [configuration](#changing-configuration-values) to `Epoxied`.

   Please create a directory called `Firmware` in the current user’s `Documents` directory (`~/Documents`).

   > **Note:** To open the user’s home directory on Windows you can use the following command in (Windows) Terminal:
   >
   > ```sh
   > ii ~/Documents
   > ```

   Then put the [current version of the STH firmware](https://github.com/MyTooliT/STH/releases/download/2.1.10/manufacturingImageSthv2.1.10.hex) into this directory. Afterwards the directory and file structure should look like this:

   ```
   ~
   └── Documents
           └── Firmware
                   └── manufacturingImageSthv2.1.10.hex
   ```

   As alternative to the steps above you can also change the variable `sth` → `firmware` → `location` → `flash` in the [configuration](#changing-configuration-values) to point to the firmware that should be used for the flash test.

2. Make sure that [the configuration values](#changing-configuration-values) are set correctly. You probably need to change at least the following variables:

   - **Name**: Please change the Bluetooth advertisement name (`sth` → `name` ) to the name of the STH you want to test.

   - **Serial Number of Programming Board**: Please make sure, that the variable `sth` → `programming board` → `serial number` contains the serial number of the programming board connected to the STH. This serial number should be displayed on the bottom right of the LCD on the programming board.

3. Please open your favorite Terminal application and execute, the STH test using the command `test-sth`. For more information about this command, please take a look at the section [“General”](#tutorials:section:general) above.

   Please note, that the test will rename the tested STH

   - to a [**Base64 encoded version of the Bluetooth MAC address**](#mac-address-conversion), if `sth` → `status` is set to `Bare PCB`, or

   - to the **serial number** (`sth` → `programming board` → `serial number`), if you set the status to `Epoxied`.

### SMH {#tutorials:section:smh}

The preparation steps for the SMH test are very similar to the ones of the [STH test](#tutorials:section:sth).

1. Please make sure that the config value that stores the SMH firmware filepath (`smh` → `firmware` → `location` → `flash`) points to the correct firmware. If you have not downloaded a firmware image for the SMH you can do so [here](https://github.com/MyTooliT/STH/releases).

2. Check that the [configuration values](#changing-configuration-values) like SMH name (`smh` → `name`) and programming board serial number (`smh` → `programming board` → `serial number`) are set correctly.

3. Please execute the test using the following command:

   ```sh
   test-smh
   ```

### STU {#tutorials:section:stu}

The following description shows you how to run the STU tests.

1. > **Note:** You can **skip this step, if you do not want to run the flash test**.

   Please take a look at step 1 of the description for the [STH test](#tutorials:section:sth) and replace every occurrence of STH (or `sth`) with STU (or `stu`).

   > **Note:** The STU test always uploads the flash file to the board, i.e. the setting `stu` → `status` is **not** read/used by the STU tests.

   In the end of this step the directory structure should look like this:

   ```
   ~
   └── Documents
          └── Firmware
                 └── manufacturingImageStuv2.1.10.hex
   ```

   You can find the current version of the STU firmware [here](https://github.com/MyTooliT/STU/releases).

2. Please take a look at the section [“General”](#tutorials:section:general) to find out how to execute the production tests for the STU. If you want to run the connection and EEPROM test (aka **all tests except the flash test**, i.e. the EEPROM and connection test), then please execute the following command:

   ```sh
   test-stu -k eeprom -k connection
   ```

### Firmware Versions

The (non-exhaustive) table below shows the compatible firmware for a certain node. The production tests assume that you use **firmware that includes the bootloader**.

| Node | Hardware Version | Microcontroller | Firmware                                                                                                                                                                 |
| ---- | ---------------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| STH  | `1.3`            | BGM113          | • [Version 2.1.10](https://github.com/MyTooliT/STH/releases/tag/2.1.10)                                                                                                  |
| STH  | `2.2`            | BGM123          | • [Aladdin](https://github.com/MyTooliT/STH/releases/tag/Aladdin)                                                                                                        |
| SMH  | `2.1`            | BGM121          | • [Version 3.0.0](https://github.com/MyTooliT/STH/releases/tag/3.0.0) <br/>• [Version E3016 Beta](<https://github.com/MyTooliT/STH/releases/tag/E3016_BETA(11_Sensors)>) |
