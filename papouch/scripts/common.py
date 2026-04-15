import argparse

from papouch.quido import Quido


def add_connection_arguments(parser: argparse.ArgumentParser):

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--eth", type=str, help="Connecto to Ethernet device (--eth 192.168.1.2)"
    )
    group.add_argument(
        "--usb", type=str, help="Connecto to USB device (--usb /dev/ttyUSB0)"
    )

    # Define common options
    parser.add_argument(
        "-p", "--port", type=int, default=1001, help="Port number [default: 1001]"
    )
    parser.add_argument(
        "-b",
        "--baud",
        type=int,
        default=115200,
        help="Baud rate for USB [default: 115200]",
    )


def add_logging_arguments(parser: argparse.ArgumentParser):
    parser.add_argument("--debug", action="store_true", help="Enable debugging")


def create_quido(args: argparse.Namespace) -> Quido:

    q = Quido()
    if args.eth is not None:
        tcp_ip = args.eth
        tcp_port = int(args.port)
        q.connect_tcp(tcp_ip, tcp_port)
    elif args.usb is not None:
        dev = args.usb
        baud = args.baud
        q.connect_usb(dev, baud)

    return q
