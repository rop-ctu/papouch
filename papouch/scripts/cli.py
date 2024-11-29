#!/usr/bin/env python
#
# name: quido-cmd
# auth: Libor Wanger <libor.wagner@cvut.cz>
# date: January 29, 2018
# desc: Command line interface for Papouch Quido

import argparse
import argparse
import logging
from papouch import Quido
from papouch.scripts.test import parse_cmdl_arguments


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

    conn = opt['--conn'].split(':')

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
        pass

    # process commands
    if opt['seto']:
        cmd_seto(q, opt)
    elif opt['geto']:
        for n in opt['<ch>']:
            state = q.get_output(int(n))
            print("Output {} is {}".format(n, 'HIGH' if state else 'LOW'))
    elif opt['geti']:
        for n in opt['<ch>']:
            state = q.get_input(int(n))
            print("Input {} is {}".format(n, 'HIGH' if state else 'LOW'))
    elif opt['monitor']:
        cmd_monitor(q, opt)
    else:
        inst = opt['<inst>']
        data = '' if opt['<data>'] is None else opt['<data>']
        adr  = '$' if opt['<adr>'] is None else opt['<adr>']
        print q.cmd(inst, data)


def cmd_monitor(q, opt):
    try:
        while True:
            val = q.wait_for_edge(int(opt["<ch>"][0]))
            print opt["<ch>"][0], ":", 'H' if val else 'L'
    except KeyboardInterrupt:
        print("Bye!")
    except Exception as e:
        print(str(e))


def cmd_seto(q, opt):

    for cmd in opt['<ch>']:
        n = int(cmd[:-1])
        a = cmd[-1]

        if a in ['H', 'h']:
            q.set_output(n, 1)
        elif a in ['L', 'l']:
            q.set_output(n, 0)
        elif a in ['T', 't']:
            q.set_output(n, not q.get_output(n))

        state = q.get_output(int(n))
        print("Output {} is {}".format(n, 'HIGH' if state else 'LOW'))


if __name__ == "__main__":
    main()
