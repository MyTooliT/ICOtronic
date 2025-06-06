# Scripts {#scripts:section:scripts}

After you installed the ICOtronic package various helper scripts are available:

- [`convert-base64-mac`](#mac-address-conversion): Utility to convert a Base64 encoded 8 character text into a Bluetooth MAC address
- [`convert-mac-base64`](#mac-address-conversion): Convert Bluetooth MAC address into a (Base64) encoded 8 character string
- [`check-eeprom`](#eeprom-check): Write a byte value into the cells of an EEPROM page an check how many of the values are read incorrectly after an reset
- [`icon`](#section:scripts:icon): Controller software for the ICOtronic system
- [`test-smh`](#section:scripts:test-smh): Test code for the SMH
- [`test-sth`](#section:scripts:test-sth): Test code for the STH/SHA
- [`test-stu`](#section:scripts:test-stu): Test code for the STU

## EEPROM Check

The script `check-eeprom` connects to an STH using its MAC address. Afterwards it writes a given byte value (default: `10`) into all the cells of an EEPROM page. It then resets the STH, connects again and shows the amount of incorrect EEPROM bytes. It repeats the last steps 5 times before it prints all values in the EEPROM page.

The command below shows how to execute the EEPROM check for the STH with MAC address `08:6b:d7:01:de:81`:

```sh
check-eeprom 08:6b:d7:01:de:81
```

You can specify the value that should be written into the EEPROM cells using the option `--value`:

```sh
check-eeprom 08:6b:d7:01:de:81 --value 42
```

## ICOn {#section:scripts:icon}

The command ICOn provides various subcommands to work with the ICOtronic system. For more information, please take a look at the [tutorial section about the tool](#icon-cli-tool).

## MAC Address Conversion

The utility `convert-mac-base64` returns the Base64 encoded version of a MAC address. We use the encoded addresses as unique Bluetooth advertisement name for the STH (or SHA). Unfortunately we can not use the MAC address directly because the maximum length of the name is limited to 8 characters. To decode the Base64 name back into a Bluetooth address you can use the script `convert-base64-mac`.

### Examples

```sh
# Convert a MAC address into an 8 character name
convert-mac-base64 08:6b:d7:01:de:81
#> CGvXAd6B

# Convert the Base64 encoded name back into a MAC address
convert-base64-mac CGvXAd6B
#> 08:6b:d7:01:de:81
```

## Test-STH {#section:scripts:test-sth}

The command `test-sth` executes the tests for the STH ([`sth.py`][]). All command line arguments of the wrapper will be forwarded to [`sth.py`][].

[`sth.py`]: https://github.com/MyTooliT/ICOtronic/tree/main/icotronic/test/production/sth.py

## Test-STU {#section:scripts:test-stu}

The command `test-stu` is a wrapper that executes the tests for the STU ([`stu.py`][]). All command line arguments of the wrapper will be forwarded to [`stu.py`][].

[`stu.py`]: https://github.com/MyTooliT/ICOtronic/tree/main/icotronic/test/production/stu.py

## Test-SMH {#section:scripts:test-smh}

The command `test-smh` is a wrapper that executes the tests for the SMH ([`smh.py`][]). All command line arguments of the wrapper will be forwarded to [`smh.py`][].

[`smh.py`]: https://github.com/MyTooliT/ICOtronic/tree/main/icotronic/test/production/smh.py
