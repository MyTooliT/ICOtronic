---
title: ICOtronic Package Documentation
author: MyTooliT
description: Library and scripts for the ICOtronic system
---

# Introduction

ICOtronic is a [Python library](https://pypi.org/project/icotronic) (based on [`python-can`](https://pypi.org/project/python-can/))
for the [ICOtronic system](https://www.mytoolit.com/ICOtronic/). The main purpose of the software is **data collection**:

- directly [via the API][API] or
- the script [`icon`](#icon-cli-tool)

[API]: https://icotronic.readthedocs.io

The software reads data from the Stationary Transceiver Unit (STU) via CAN using the [MyTooliT protocol](https://mytoolit.github.io/Documentation/#mytoolit-communication-protocol). The STU itself reads from and writes data to a sensor node via Bluetooth.


## Install

Please use the following command:

```sh
pip install icotronic
```

to install the [latest official version of the ICOtronic library from PyPi](https://pypi.org/project/icotronic).

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
