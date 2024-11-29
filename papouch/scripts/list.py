import argparse
import socket
import struct


def parse_cmdl_arguments():
    parser = argparse.ArgumentParser("quido-list")

    args = parser.parse_args()
    return args


def main():
    _ = parse_cmdl_arguments()

    UDP_IP = '<broadcast>'
    UDP_PORT = 30718
    HEX = 0x000100F6
    PAYLOAD = struct.pack("!L", HEX)
    comsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    comsocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    comsocket.sendto(PAYLOAD, (UDP_IP, UDP_PORT))
    comsocket.settimeout(2)

    found = 0
    while True:
        try:
            data, wherefrom = comsocket.recvfrom(1024, 0)
        except socket.timeout:
            break
        found += 1
        print("{:02d} mac:".format(found), show_mac(data[-6:]), "ip:", wherefrom[0])

    print("Found {} devices.".format(found))
    comsocket.close()


def show_mac(mac) -> str:
    s = '-'.join('{:02X}'.format(a) for a in mac)
    return s
