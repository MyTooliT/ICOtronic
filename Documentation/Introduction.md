---
title: ICOtronic Package Documentation
author: MyTooliT
description: Library and scripts for the ICOtronic system
---

# Introduction

ICOtronic is a

- [Python library](https://pypi.org/project/icotronic) (based on [`python-can`](https://pypi.org/project/python-can/)) and
- a collection of tools and scripts

for the [ICOtronic system](https://www.mytoolit.com/ICOtronic/). Currently the main purpose of the software is:

- **Data collection**
  - directly [via the API][API] or
  - the script [`icon`](#icon-cli-tool)
- **Testing** the functionality of
  - a [Stationary Transceiver Unit (STU)](#tutorials:section:stu) or
  - a sensor node, such as a
    - [Sensory Holder Assembly (SHA)/Sensory Tool Holder (STH)](#tutorials:section:sth) or
    - [Sensory Milling Head (SMH)](#tutorials:section:smh)

[API]: https://icotronic.readthedocs.io

The software reads data from the Stationary Transceiver Unit (STU) via CAN using the [MyTooliT protocol](https://mytoolit.github.io/Documentation/#mytoolit-communication-protocol). The STU itself reads from and writes data to the sensor nodes via Bluetooth.

## Requirements

### Hardware

In order to use the ICOtronic system you need at least:

- a [PCAN adapter](https://www.peak-system.com):

  ![PCAN Adapter](Documentation/Pictures/PCAN.jpg)

  including:

  - power injector, and
  - power supply unit (for the power injector):

    ![Power Injector](Documentation/Pictures/Power-Injector.jpg)

  > **Note:** Other [CAN adapters supported by python-can](https://python-can.readthedocs.io/en/stable/interfaces.html) should work as well. However, you need to update the [configuration](#changing-configuration-values) for the CAN connection accordingly.

- a [Stationary Transceiver Unit](https://www.mytoolit.com/ICOtronic/):

   <img src="https://cdn.bitrix24.de/b5488381/landing/5fa/5fa2ce04fd1326e07bf39866e44f4e61/IMG_6338_2x.jpg" alt="STU" width="400">

- a sensor node, such as a [Sensory Tool Holder](https://www.mytoolit.com/ICOtronic/):
  <img src="https://cdn.bitrix24.de/b5488381/landing/cbe/cbe07df56cea688299533819c1e8a8d3/IMG_6350_2x_2x.jpg" alt="Sensory Tool Holder" width="400">

#### Setup

1. Connect the power injector
   1. to the PCAN adapter, and
   2. the power supply unit.
2. Connect the USB connector of the PCAN adapter to your computer.
3. Make sure that your sensor node (SHA/STH/SMH) is connected to a power source. For an STH this usually means that you should check that the battery is (fully) charged.

### Software

#### Python

The ICOtronic package supports `3.10` and later. We recommend you use the 64-bit version of Python.

You can download Python [here](https://www.python.org/downloads). When you install the software, please do not forget to enable the checkbox **“Add Python to PATH”** in the setup window of the installer.

#### PCAN Driver

To communicate with the STU you need a driver that works with the PCAN adapter. The text below describes how to install/enable this driver on

- [Linux](#introduction:section:pcan-driver:linux),
- [macOS](#introduction:section:pcan-driver:macos), and
- [Windows](#introduction:section:pcan-driver:windows).

##### Linux {#introduction:section:pcan-driver:linux}

You need to make sure that your CAN adapter is available via the [SocketCAN](https://en.wikipedia.org/wiki/SocketCAN) interface.

The following steps describe one possible option to configure the CAN interface on ([Fedora](https://getfedora.org), [Ubuntu](https://ubuntu.com)) Linux **manually**.

1. Connect the CAN adapter to the computer that runs Linux (or alternatively the Linux VM)
2. Check the list of available interfaces:

   ```sh
   networkctl list
   ```

   The command output should list the CAN interface with the name `can0`

3. Configure the CAN interface with the following command:

   ```
   sudo ip link set can0 type can bitrate 1000000
   ```

4. Bring up the CAN interface

   ```
   sudo ip link set can0 up
   ```

You can also configure the CAN interface **automatically**. For that purpose please store the following text:

```ini
[Match]
Name=can*

[CAN]
BitRate=1000000
```

in a file called `/etc/systemd/network/can.network`. Afterwards enable `networkd` and reload the configuration with the commands:

```sh
sudo systemctl enable systemd-networkd
sudo systemctl restart systemd-networkd
# Note: The command `networkctl reload` only works in systemd 244 or newer
sudo networkctl reload || sudo systemctl reload systemd-networkd
```

You can check the status of the CAN connection with the command:

```sh
networkctl list
```

If everything works as expected, then the output of the command should look similar to the text below:

```
IDX LINK   TYPE     OPERATIONAL SETUP
  …
  7 can0   can      carrier     configured
```

**Sources**:

- [SocketCAN device on Ubuntu Core](https://askubuntu.com/questions/1082277/socketcan-device-on-ubuntu-core)
- [Question: How can I automatically bring up CAN interface using netplan?](https://github.com/linux-can/can-utils/issues/68#issuecomment-584505426)
- [networkd › systemd › Wiki › ubuntuusers](https://wiki.ubuntuusers.de/systemd/networkd/)

##### macOS {#introduction:section:pcan-driver:macos}

On macOS you can use the [PCBUSB](https://github.com/mac-can/PCBUSB-Library) library to add support for the PCAN adapter. For more information on how to install this library please take a look at the issue [“How to install the PCBUSB-Library on Mac”](https://github.com/mac-can/PCBUSB-Library/issues/10#issuecomment-1188682027).

##### Windows {#introduction:section:pcan-driver:windows}

You can find the download link for the PCAN Windows driver [here](https://www.peak-system.com/quick/DrvSetup). Please make sure that you include the “PCAN-Basic API” when you install the software.

#### Simplicity Commander (Optional)

For the [production tests](tutorials:section:production-tests) that require a firmware flash you need to **either** install

- [Simplicity Studio](https://www.silabs.com/products/development-tools/software/simplicity-studio) or
- [Simplicity Commander](https://www.silabs.com/developers/mcu-programming-options).

If you choose the first option, then please make sure to install the Simplicity Commander tool inside Simplicity Studio.

##### Linux

Please add the path to `commander` to the list `commands` → `path` → `linux` in the [configuration](#changing-configuration-values).

##### macOS

If you install Simplicity Studio or Simplicity Commander in the standard install path (`/Applications`) you do not need to change the config. If you put the application in a different directory, then please add the path to `commander` to the list `commands` → `path` → `mac` in the [configuration](#changing-configuration-values).

##### Windows

- If you installed Simplicity Studio (including Simplicity Studio) to the standard location, then you do not need to change the configuration.

- If you download Simplicity Commander directly, then the tests assume that you unzipped the files into the directory `C:\SiliconLabs\Simplicity Commander`.

- If you did not use any of the standard install path, then please add the path to `commander.exe` to the list `commands` → `path` → `windows` in the [configuration](#changing-configuration-values).

##### Additional Notes

- If you **do not want to change the config**, and Simplicity Commander (`commander`) is not part of the standard locations for your operating system, then please make sure that `commander` is accessible via the `PATH` environment variable.
- Please note, that you **do not need to install Simplicity Commander** if you just want to **collect data** with the ICOtronic library.

## Install

Please use the following command:

```sh
pip install icotronic
```

to install the [latest official version of the ICOtronic library from PyPi](https://pypi.org/project/icotronic). Afterwards you can use the various [scripts](#scripts:section:scripts) included in the package.

### Install the Package Using Windows Terminal

1. Install (Windows) [Terminal](https://aka.ms/terminal) if you have not done so already; On Windows 11 this application should be installed by default.
2. Open Terminal
3. Copy and paste the following text into the Terminal

   ```sh
   pip install icotronic
   ```

4. Press Return <kbd>⏎</kbd>
5. Wait until the install process finished successfully

### Install the Development Version of ICOtronic

**Note:** Please only use the command below, **if you know what you are doing**!

```sh
pip install 'git+https://github.com/MyTooliT/ICOtronic'
```

### Troubleshooting

#### Import Errors

If [one of the scripts](#scripts:section:scripts) fails with an error message that looks similar to the following text on Windows:

```
Traceback (most recent call last):
…
    from numexpr.interpreter import MAX_THREADS, use_vml, __BLOCK_SIZE1__
ImportError: DLL load failed while importing interpreter: The specified module could not be found.

DLL load failed while importing interpreter: The specified module could not be found.
```

then you probably need to install the [“Microsoft Visual C++ Redistributable package” ](https://docs.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist). You can download the latest version

- for the `x64` architecture, i.e. for AMD and Intel CPUs, [here](https://aka.ms/vs/17/release/vc_redist.x64.exe) and
- for the `ARM64` architecture [here](https://aka.ms/vs/17/release/vc_redist.arm64.exe).

#### Insufficient Rights

**If you do not have sufficient rights** to install the package you can also try to install the package in the user package folder:

```sh
pip install --user icotronic
```

#### Unable to Install in Editable Mode

If the ICOtronic install fails with the following error:

```
ERROR: Project …/ICOtronic has a 'pyproject.toml' and its build backend is missing the 'build_editable' hook.
Since it does not have a 'setup.py' nor a 'setup.cfg', it cannot be installed in editable mode.
Consider using a build backend that supports PEP 660.
```

then your version of [Setuptools](http://setuptools.pypa.io) needs to be updated before you install the ICOtronic package. You can use the following command to do that:

```sh
pip install -U pip setuptools
```

#### Unable to Locate HDF5 {#introduction:section:unable-to-locate-hdf5}

The installation of the ICOtronic package might fail with an error message that looks like this:

```
… implicit declaration of function 'H5close'
```

If you uses [Homebrew][] on an Apple Silicon based Mac you can use the [following commands to fix this problem](https://stackoverflow.com/questions/73029883/could-not-find-hdf5-installation-for-pytables-on-m1-mac):

[Homebrew]: https://brew.sh

```sh
pip uninstall -y tables
brew install hdf5 c-blosc2 lzo bzip2
export BLOSC_DIR=/opt/homebrew/opt/c-blosc
export BZIP2_DIR=/opt/homebrew/opt/bzip2
export LZO_DIR=/opt/homebrew/opt/lzo
export HDF5_DIR=/opt/homebrew/opt/hdf5
pip install --no-cache-dir tables
```

#### HDF5 Library Not Loaded

Some of the [ICOtronic scripts](#scripts:section:scripts) might fail with an error message that looks like this on macOS:

> `Library not loaded: /opt/homebrew/opt/hdf5/lib/libhdf5.….dylib`

In that case you might have installed an outdated cached version of [PyTables](https://www.pytables.org). You should be able to fix this issue using the same steps as described [above ](#introduction:section:unable-to-locate-hdf5).

#### Unable to open OpenBLAS library

If one of the [ICOtronic scripts](#scripts:section:scripts) fails with the error message:

> ImportError: libopenblas.so.0: cannot open shared object file: No such file or directory

on [Raspbian](http://www.raspbian.org) (or some other GNU/Linux version based on Debian) then you probably need to install the [OpenBLAS](http://www.openblas.net) library:

```sh
sudo apt-get install libopenblas-dev
```

#### Unknown Command

If `pip install` prints **warnings about the path** that look like this:

> The script … is installed in `'…\Scripts'` which is not on PATH.

then please add the text between the single quotes (without the quotes) to your [PATH environment variable](<https://en.wikipedia.org/wiki/PATH_(variable)>). Here `…\Scripts` is just a placeholder. Please use the value that `pip install` prints on your machine. If

- you used the [installer from the Python website](https://www.python.org/downloads) (and checked “Add Python to PATH”) or
- you used [winget](https://docs.microsoft.com/en-us/windows/package-manager/winget/)

to install Python, then the warning above should not appear. On the other hand, the **Python version from the [Microsoft Store](https://www.microsoft.com/en-us/store/apps/windows) might not add the `Scripts` directory** to your path.
