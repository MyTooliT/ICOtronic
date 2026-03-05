# ICOtronic Package Documentation

ICOtronic is a [Python library](https://pypi.org/project/icotronic) (based on [`python-can`](https://pypi.org/project/python-can/))
for the [ICOtronic system](https://www.mytoolit.com/ICOtronic/). The main purpose of the software is **data collection**:

- directly via the API or
- the script `icon`.

The software reads data from a Stationary Transceiver Unit (STU) via CAN using the [MyTooliT protocol](https://mytoolit.github.io/Documentation/#mytoolit-communication-protocol). The STU itself reads from and writes data to a sensor node via Bluetooth.

```{toctree}
usage
api
examples
```
