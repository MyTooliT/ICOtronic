"""Convert MAC address to Base64 text"""

# -- Imports ------------------------------------------------------------------

from argparse import ArgumentParser

from icotronic.cmdline.parse import mac_address
from icotronic.utility.naming import convert_mac_base64

# -- Main ---------------------------------------------------------------------


def main():
    """Convert MAC address specified via command line argument to Base64"""

    parser = ArgumentParser(
        description="Convert a MAC address to an 8 character Base64 text"
    )
    parser.add_argument(
        "mac",
        help="MAC address of STH e.g. 08:6b:d7:01:de:81",
        type=mac_address,
    )
    mac = parser.parse_args().mac

    name = convert_mac_base64(mac)
    print(name)


if __name__ == "__main__":
    main()
