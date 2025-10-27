# Tutorials

## Changing Configuration Values

> **Note:** If you only use the `icon` command line tool, then you most probably do not need to change the configuration at all.

All configuration options are currently stored in [YAML](https://yaml.org) files (handled by the configuration library [Dynaconf][]). The [default values][] are stored inside the package itself. If you want to overwrite or extend these values you should create a user configuration file. To do that you can use the command:

```sh
icon config
```

which will open the the user configuration in your default text editor. You can then edit this file and save your changes to update the configuration. For a list of available options, please take a look at the [default configuration][default values].

Please make sure to not make any mistakes when you edit this file. Otherwise some parts of the ICOtronic library will not work correctly, printing an error message about the (first) incorrect configuration value. In that case the library will also try to open the user configuration file in your standard text editor so you can fix the problem.

[Dynaconf]: https://www.dynaconf.com
[default values]: https://github.com/MyTooliT/ICOtronic/blob/main/icotronic/config/config.yaml

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

The formula which can be used to calculate the sampling rate can be found in the general ICOtronic system documentation under the section [“Sampling Rate”](https://mytoolit.github.io/Documentation/#sampling-rate). Please be aware that the actual sample rate might be slightly lower, even if there is no data loss.

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

If the file does not exist yet, then it will be created and filled with the content of the [default user configuration](https://github.com/MyTooliT/ICOtronic/blob/main/icotronic/config/user.yaml). For more information on how to change the configuration, please take a look at the section [“Changing Configuration Values”](#changing-configuration-values).

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

#### Determining Data Loss

Depending on

- the hardware of the computer and
- the used sampling frequency

the ICOtronic library might not be able to keep up with the rate of measurement data that is collected by the STU and stored in the buffer of the CAN adapter. The result in this case will be a certain rate of data loss, since the CAN adapter will get rid of old data if it is not collected fast enough.

To minimize the chance of this kind of data loss you can use the command

```sh
icon dataloss
```

to determine the CPU usage and data loss for the current computer at certain sample rates.
