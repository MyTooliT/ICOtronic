# Data Collection

The [ICOtronic package](https://pypi.org/project/icotronic) provides two different options to collect sensor data with the [ICOtronic system](https://mytoolit.com/icotronic):

1. Use the [API][] to write your own Python scripts: To learn more about this option, please take a look at the [API documentation][API].
2. Use the [`icon`](#icon-cli-tool) script to collect data: We will describe how to measure some basic data with this script in the text below

[API]: https://icotronic.readthedocs.io

---

**Note:** Since ICOn currently only provides very basic functionality for data collection you might be happier using one of the tools below. Both are currently based on an [older (deprecated) version of this Python package][ICOc]:

- [ICOgui](https://git.ift.tuwien.ac.at/lab/ift/icotronic/icogui): A closed source Electron application for Windows
- [ICOc](https://mytoolit.github.io/ICOc/#basic-usage): A text based UI for Windows

[ICOc]: https://github.com/mytoolit/ICOc

---

## Sensor Device Identifiers

To connect to a sensor device (SHA, STH, SMH) you need to know an identifier for the device, which can be one of the following:

- Bluetooth advertisement **name**: up to 8 characters, no special characters allowed
- Bluetooth **[MAC address](https://en.wikipedia.org/wiki/MAC_address)**: 8 Bytes, usually written in [hexadecimal format](https://en.wikipedia.org/wiki/Hexadecimal)
- **Device number**: starting with 0, up to the number of available sensor devices minus one (e.g. for 8 sensor devices, the maximum sensor device number will 7)

If you do not know any of the above identifiers for your device you can use the command

```sh
icon list
```

to show the available devices:

```
🤖 Name: Test-STH, Device Number: 0, MAC Address: 08-6B-D7-01-DE-81, RSSI: -51
```

In the example above, we see that one sensor device is available with the following identifiers:

- device number: `0`
- name: `Test-STH`
- MAC address: `08-6B-D7-01-DE-81`

**Note:** The last value “-51” of the example output is the current [received signal strength indication (RSSI)](https://en.wikipedia.org/wiki/Received_signal_strength_indication).

## Collecting Data

After you determined one of the identifiers (name, MAC address, device number) of your sensor device you can use the command:

```sh
icon measure
```

to collect measurement data. For example, to collect data from an STH with the name “Test-STH” for 10 seconds you can use the following command:

```sh
icon measure --name Test-STH --time 10
```

[HDF5]: https://www.hdfgroup.org/solutions/hdf5

After the measurement took place the command will print some information about the collected data, including the location of the [HDF5][] measurement file:

```
Sample Rate: 9523.81 Hz
Data Loss: 0.0 %
Filepath: Measurement_2025-05-14_15-11-25.hdf5
```

By default measurement files will be stored in the current working directory with

- a name starting with the text `Measurement`
- followed by a date/time-stamp,
- and the extension `.hdf5`.

## Measurement Data

---

**Note:** ICOn **assumes** that the sensor device always measures **acceleration data** in multiples of the [gravity of earth](https://en.wikipedia.org/wiki/Gravity_of_Earth), commonly referred as $g$ or $g_0$. While this is true for most of the sensor hardware (such as STHs), some sensor devices measure other values, e.g. force or temperature. Even in this case the measurement software will (incorrectly) [convert the data into multiples of $g$](https://github.com/MyTooliT/ICOtronic/blob/dc636ce2cda8f380aa0f031fc743062820eb3443/mytoolit/measurement/acceleration.py#L50-L51). We are **working on adding support for configuring the sensor type** in the firmware and the ICOtronic package to **fix this issue**.

---

To take a look at the measurement data you can use the tool [HDFView][]. Unfortunately you need to create a free account to download the program. If you do not want to register, then you can try if [one of the accounts listed at BugMeNot](http://bugmenot.com/view/hdfgroup.org) works. Another option is to download the application from [here](https://support.hdfgroup.org/ftp/HDF5/releases/HDF-JAVA/). Just click on the folder for the latest version of the application (`hdfview-…`) and afterwards on the folder `bin` to see a list of compressed binaries (`.zip` & `.tar.gz`) for the different supported operating systems.

[hdfview]: https://www.hdfgroup.org/downloads/hdfview/

The screenshot below shows a measurement file produced by ICOc:

![Main Window of HDFView](Documentation/Pictures/HDFView-File.png)

As you can see the table with the name `acceleration` stores the acceleration data. The screenshot above displays the metadata of the table. The most important meta attributes here are probably:

- `Start_Time`, which contains the start time of the measurement run in ISO format, and
- `Sensor_Range`, which specifies the range of the used acceleration sensor in multiples of earth’s gravitation (g₀ ≅ 9.81 m/s²).

After you double click on the acceleration table on the left, HDFView will show you the actual acceleration data:

<img src="Documentation/Pictures/HDFView-Table.png" alt="Acceleration Table in HDFView" width="500"/>

As you can infer from the `x` column above the table shows the acceleration measurement data (in multiples of g₀) for a single axis. The table below describes the meaning of the columns:

| Column    | Description                                                                              | Unit             |
| --------- | ---------------------------------------------------------------------------------------- | ---------------- |
| counter   | A cyclic counter value (0–255) sent with the acceleration data to recognize lost packets | –                |
| timestamp | The timestamp for the measured value in microseconds since the measurement start         | μs               |
| x         | Acceleration in the x direction as multiples of earth’s gravitation                      | g₀ (≅ 9.81 m/s²) |

Depending on your sensor and your settings the table might also contain columns for the `y` and/or `z` axis.

If you want you can also use HDFView to print a simple graph for your acceleration data. To do that:

1. Select the values for the the ordinate (e.g. click on the x column to select all acceleration data for the x axis)
2. Click on the graph icon in the top left corner
3. Choose the data for the abscissa (e.g. the timestamp column)
4. Click on the “OK” button

The screenshot below shows an example of such a graph:

![Acceleration Graph in HDFView](Documentation/Pictures/HDFView-Graph.png)

For a more advanced analysis of the data files you can use our collection of measurement utility software [ICOlyzer](https://github.com/MyTooliT/ICOlyzer).

### Adding Custom Metadata

Sometimes you also want to add additional data about a measurement. To do that you can also use [HDFView][]. Since the tool opens files in read-only mode by default you need to change the default file access mode to “Read/Write” first:

1. Open [HDFView][]
2. Click on “Tools” → “User Options”
3. Select “General Settings”
4. Under the text “Default File Access Mode” choose “Read/Write”
5. Close HDFView

Now you should be able to add and modify attributes. For example, to add a revolutions per minute (RPM) value of `15000` you can use the following steps:

1. Open the measurement file in [HDFView][]
2. Click on the table “acceleration” in the left part of the window
3. In the tab “Object Attribute Info” on the right, click on the button “Add attribute”
4. Check that “Object List” contains the value “/acceleration”
5. Enter the text “RPM” in the field “Name”
6. In the field “Value” enter the text “15000”
7. The “Datatype Class” should be set to “INTEGER”
8. For the size (in bits) choose a bit length that is large enough to store the value. In our example everything equal to or larger than 16 bits should work.
9. Optionally you can also check “Unsigned”, if you are sure that you only want to store positive values
10. Click the button “OK”

![HDFView: RPM Attribute](Documentation/Pictures/HDFView-RPM.png)

Sometimes you also want to add some general purpose data. For that you can use the “STRING” datatype class. For example, to store the text “hello world” in an attribute called “Comment” you can do the following

1. Repeat steps 1. – 4. from above
2. Choose “STRING” as “Datatype Class”
3. Under “Array Size” choose a length that is large enough to store the text such as “1000” (every size larger than or equal to 11 characters should work)
4. Click the button “OK”

![HDFView: Comment Attribute](Documentation/Pictures/HDFView-Comment.png)

If you want you can also add multiline text. Since you can not add newlines using <kbd>⏎</kbd> in HDFView directly, we recommend you open your favorite text editor to write the text and then copy and paste the text into the value field. HDFView will only show the last line of the pasted text. However, after you copy and paste the text into another program you will see that HDFView stored the text including the newlines.
