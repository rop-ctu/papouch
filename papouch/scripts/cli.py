#!/usr/bin/env python
#
# name: quido-cmd
# auth: Libor Wanger <libor.wagner@cvut.cz>
# date: January 29, 2018
# desc: Command line interface for Papouch Quido

import argparse
import logging
import sys
from typing import List
from papouch import Quido
from papouch.quido import as_bytes

log = logging.getLogger("quido-cli")


def parse_cmdl_arguments():
    parser = argparse.ArgumentParser(description="Control Papouch Quido from the command line.")

    # Commands as subparsers
    subparsers = parser.add_subparsers(dest="command", required=True, help="Commands")

    # seto <ch>...
    parser_seto = subparsers.add_parser("seto", help="Set output channels")
    parser_seto.add_argument("channels", metavar="ch", type=str, nargs="+", help="Channels to set")

    # geto <ch>...
    parser_geto = subparsers.add_parser("geto", help="Get output channels")
    parser_geto.add_argument("channels", metavar="ch", type=str, nargs="+", help="Channels to get")

    # geti <ch>...
    parser_geti = subparsers.add_parser("geti", help="Get input channels")
    parser_geti.add_argument("channels", metavar="ch", type=str, nargs="+", help="Channels to get input from")

    # info
    subparsers.add_parser("info", help="Get device information")

    # monitor <ch>
    parser_monitor = subparsers.add_parser("monitor", help="Monitor a specific channel")
    parser_monitor.add_argument("channel", metavar="ch", type=str, help="Channel to monitor")

    # <inst> [<data>] [<adr>]
    parser_inst = subparsers.add_parser("inst", help="Send an arbitrary command")
    parser_inst.add_argument("instruction", metavar="inst", type=str, help="Instruction to send")
    parser_inst.add_argument("data", metavar="data", type=str, nargs="?", help="Additional data for instruction")
    parser_inst.add_argument("address", metavar="adr", type=str, nargs="?", help="Device address (if necessary)")

    # Options
    parser.add_argument("--debug", action="store_true", help="Debug mode")
    parser.add_argument("--conn", type=str, default="usb:/dev/ttyUSB0", help="Connection string")

    args = parser.parse_args()
    return args


def main():
    args = parse_cmdl_arguments()

    if args.debug:
        logging.basicConfig(level='DEBUG')
    else:
        logging.basicConfig(level='INFO')

    log.debug("Command line arguments: \n    %s", str(args))
    conn = args.conn.split(':')

    # initialize quido
    q = Quido()

    # parse the conn argument
    if conn[0] == 'eth':
        ip = conn[1]
        if len(conn) > 2:
            pass
        else:
            q.connect_tcp(ip)
    if conn[0] == 'usb':
        dev = conn[1]
        if len(conn) > 2:
            pass
        else:
            q.connect_usb(dev)
    else:
        log.error("No valid connection method {args.conn}")
        sys.exit(1)

    # process commands
    if args.command == "seto":
        cmd_seto(q, args.channels)
    elif args.command == "geto":
        for n in args.channels:
            state = q.get_output(int(n))
            log.info("Output {} is {}".format(n, 'HIGH' if state else 'LOW'))
    elif args.command == "geti":
        for n in args.channels:
            state = q.get_input(int(n))
            log.info("Input {} is {}".format(n, 'HIGH' if state else 'LOW'))
    elif args.command == "monitor":
        cmd_monitor(q, args.channels)
    elif args.command == "info":
        cmd_info(q)
    else:
        inst = args.instruction
        data = b'' if args.data is None else args.data
        adr  = b'$' if args.address is None else args.address
        log.info(q.cmd(inst, as_bytes(data)))

def cmd_info(q):
    name = q.get_name()
    print("Name:           ", name[0])
    print("Version:        ", name[1])
    print("Temperature(1): ", q.get_temperature(1), 'C')

def cmd_monitor(q, channel: str):
    try:
        while True:
            val = q.wait_for_edge(int(channel))
            log.info(f"{channel}: {'H' if val else 'L'}")
    except KeyboardInterrupt:
        print("Bye!")
    except Exception as e:
        print(str(e))


def cmd_seto(q, channels: List[str]):

    for cmd in channels:
        n = int(cmd[:-1])
        a = cmd[-1]

        if a in ['H', 'h']:
            q.set_output(n, 1)
        elif a in ['L', 'l']:
            q.set_output(n, 0)
        elif a in ['T', 't']:
            q.set_output(n, not q.get_output(n))

        state = q.get_output(int(n))
        log.info("Output {} is {}".format(n, 'HIGH' if state else 'LOW'))


if __name__ == "__main__":
    main()
