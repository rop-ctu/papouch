"""Network discovery utility for Papouch Quido devices.

Developer notes:
- This tool uses Linux AF_PACKET raw sockets to send one broadcast frame per
  interface. This avoids relying on kernel routing heuristics for regular UDP
  broadcast and gives deterministic per-interface discovery.
- Packet headers are built manually (Ethernet + IPv4 + UDP) because AF_PACKET
  expects complete L2/L3/L4 framing.
- Receiving uses a deadline with select(), not socket timeout alone. On busy
  interfaces, unrelated traffic can keep recvfrom() unblocked forever.
- This implementation is Linux-specific and requires raw-socket privileges
  (root or CAP_NET_RAW).
"""

from typing import List
from dataclasses import dataclass
import socket
import struct
import fcntl
import time
import select
import argparse


PORT = 30718
PAYLOAD = b"\x00\x01\x00\xf6"
DEFAULT_TIMEOUT = 3.0

ETH_P_ALL = 0x0003
ETH_P_IP = 0x0800

# ---- helpers ----


def get_iface_mac(iface):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    info = fcntl.ioctl(
        s.fileno(),
        0x8927,  # SIOCGIFHWADDR
        struct.pack("256s", iface.encode("utf-8")),
    )
    return info[18:24]


def get_iface_ip(iface):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    info = fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack("256s", iface.encode("utf-8")),
    )
    return socket.inet_ntoa(info[20:24])


def checksum(data):
    """Return IPv4 header checksum for bytes payload."""
    if len(data) % 2:
        data += b"\x00"
    s = sum(struct.unpack("!%dH" % (len(data) // 2), data))
    s = (s >> 16) + (s & 0xFFFF)
    s += s >> 16
    return ~s & 0xFFFF


# ---- build headers ----


def build_ip(src_ip, dst_ip, payload_len):
    """Build minimal IPv4 header for UDP payload."""
    ver_ihl = 0x45
    tos = 0
    total_len = 20 + 8 + payload_len
    ident = 0
    flags_frag = 0
    ttl = 64
    proto = socket.IPPROTO_UDP
    chksum = 0

    src = socket.inet_aton(src_ip)
    dst = socket.inet_aton(dst_ip)

    header = struct.pack(
        "!BBHHHBBH4s4s",
        ver_ihl,
        tos,
        total_len,
        ident,
        flags_frag,
        ttl,
        proto,
        chksum,
        src,
        dst,
    )

    chksum = checksum(header)

    return struct.pack(
        "!BBHHHBBH4s4s",
        ver_ihl,
        tos,
        total_len,
        ident,
        flags_frag,
        ttl,
        proto,
        chksum,
        src,
        dst,
    )


def build_udp(src_port, dst_port, payload):
    """Build UDP header with zero checksum."""
    length = 8 + len(payload)
    return struct.pack("!HHHH", src_port, dst_port, length, 0)


@dataclass
class Iface:
    name: str
    ip: str | None
    mac: bytes


def get_iface_info(iface: str) -> Iface:

    # IP
    try:
        ip = get_iface_ip(iface)
    except OSError:
        ip = None

    # MAC
    mac = get_iface_mac(iface)

    return Iface(iface, ip, mac)


def list_active_ifaces() -> List[Iface]:
    """Return non-loopback interfaces with MAC and best-effort IPv4."""
    result = []
    for _, iface in socket.if_nameindex():
        if iface == "lo":
            continue

        try:
            result.append(get_iface_info(iface))
        except Exception:
            continue

    return result


def run_discovery_on(iface: Iface, timeout: float = DEFAULT_TIMEOUT):
    """Send discovery packet on one interface and print matching replies."""
    src_mac = iface.mac
    src_ip = iface.ip

    dst_mac = b"\xff\xff\xff\xff\xff\xff"
    dst_ip = "255.255.255.255"

    eth_header = struct.pack("!6s6sH", dst_mac, src_mac, ETH_P_IP)
    ip_header = build_ip(src_ip, dst_ip, len(PAYLOAD))
    udp_header = build_udp(PORT, PORT, PAYLOAD)

    packet = eth_header + ip_header + udp_header + PAYLOAD

    # AF_PACKET captures link-layer frames on a single interface.
    sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(ETH_P_ALL))
    sock.bind((iface.name, 0))

    sock.send(packet)

    deadline = time.monotonic() + timeout
    found = 0

    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break

        readable, _, _ = select.select([sock], [], [], remaining)
        if not readable:
            break

        pkt, _ = sock.recvfrom(65535)

        # Ethernet header starts at byte 0, EtherType at bytes 12..13.
        eth_proto = struct.unpack("!H", pkt[12:14])[0]
        if eth_proto != ETH_P_IP:
            continue

        # IPv4 header follows Ethernet at offset 14.
        ip_header = pkt[14:34]
        proto = ip_header[9]
        if proto != 17:  # UDP
            continue

        src_ip = socket.inet_ntoa(ip_header[12:16])

        # UDP header follows minimal 20-byte IPv4 header.
        udp_header = pkt[34:42]
        src_port = struct.unpack("!H", udp_header[0:2])[0]

        # Papouch discovery replies are expected from UDP port 30718.
        if src_port != PORT:
            continue

        # --- Payload ---
        src_mac = pkt[6:12]

        found += 1
        print(f"{found:02d} mac: {':'.join(f'{b:02x}' for b in src_mac)} ip: {src_ip}")

    print(f"Found {found} devices")

    sock.close()


# ---- main ----


def parse_cmdl_arguments():
    parser = argparse.ArgumentParser(
        "quido-list",
        description="Discover Papouch Quido devices by UDP broadcast on network interfaces.",
        epilog=(
            "Note: discovery uses Linux raw sockets (AF_PACKET). "
            "Run as root or grant CAP_NET_RAW (for example via sudo)."
        ),
    )
    parser.add_argument(
        "-i",
        "--interface",
        type=str,
        help="Limit discovery to one network interface (for example: eno1)",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=f"Discovery timeout in seconds [default: {DEFAULT_TIMEOUT}]",
    )

    args = parser.parse_args()
    return args


def main():
    args = parse_cmdl_arguments()
    ifaces = list_active_ifaces()

    if args.interface:
        ifaces = [iface for iface in ifaces if iface.name == args.interface]
        if not ifaces:
            print(f"Interface '{args.interface}' not found or not active")
            return

    for iface in ifaces:
        print(f"Running discovery on iface = {iface}")

        if iface.ip is None:
            print("IP is not set")
            continue

        try:
            run_discovery_on(iface, timeout=args.timeout)
        except Exception as e:
            print(f"Failed {e}")


if __name__ == "__main__":
    main()
