from dataclasses import dataclass

import logging
from typing import Any, List, Optional
import requests
import socket
import serial

from papouch.error import QuidoError

log = logging.getLogger()


@dataclass
class QuidoInfo:
    name: str

# b'0\r*B10Quido ETH 4/4; v0254.03.35; f66 97; t1\r'


class Quido(object):

    def __init__(self):
        self.connection = 'none'

    def connect_tcp(self, ip:str, port:int=1001):
        self.connection = 'tcp'
        self.tcp_ip = ip
        self.tcp_port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.tcp_ip, self.tcp_port))
        self.cmd = self.__cmd_tcp
        self.recv = self.__recv_tcp
        self.cmd(b'IS', b'0') # disable sending changes
        log.debug("Connected to tcp ip: %s port: %s", self.tcp_ip, self.tcp_port)

    def __cmd_tcp(self, inst:bytes, data:bytes=b'', adr:bytes=b'$', buff:int=1000) -> bytes:
        msg = b'*B' + adr + inst + data + b'\r'
        self.socket.send(msg)
        log.debug("Cmd send: %s", msg)
        recv = self.__recv_tcp(buff)
        log.debug("Cmd recv: %s", recv)
        return recv

    def __recv_tcp(self, buff:int=1000) -> bytes:
        recv = self.socket.recv(buff)
        log.debug("Cmd recv: %s", recv)
        return recv

    def connect_usb(self, dev:str, baud:int=115200):
        self.connection = 'serial'
        self.dev = dev
        self.baud = baud
        self.ser = serial.Serial(self.dev, self.baud)
        self.cmd = self.__cmd_serial
        self.recv = self.__recv_serial
        log.debug("Connected to serial dev: %s baud: %d", self.dev, self.baud)

    def __cmd_serial(self, inst:bytes, data:bytes=b'', adr:bytes=b'$', buff:int=1000) -> bytes:
        msg = b'*B' + adr + inst + data + b'\r'
        self.ser.write(msg)
        self.ser.flush()
        log.debug("Serial write: %s", msg)
        recv = self.__recv_serial()
        return recv

    def __recv_serial(self, buff=None) -> bytes:
        recv = read_util(self.ser)
        log.debug("Serial read: %s", recv)
        return recv

    def check_reponse(self, resp) -> bool:
        return len(resp) > 3 and resp[3:4] == b'0'

    def reset(self) -> bool:
        inst = b'RE'
        recv = self.cmd(inst)

        if self.check_reponse(recv):
            return True
        else:
            raise QuidoError("Unable to reset", recv)

    def get_name(self) -> List[str]:
        inst = b'?'
        recv = self.cmd(inst)

        if self.check_reponse(recv):
            text = recv[4:-1].decode('utf-8')
            return [v.strip() for v in text.split(';')]
        else:
            raise QuidoError("Unable to read name", recv)

    def get_temperature(self, n=1) -> float:
        inst = b'TR'
        data = as_bytes(n)
        recv = self.cmd(inst, data)

        if self.check_reponse(recv):
            return float(recv[4:-2])
        else:
            raise QuidoError("Failed to read temperature", recv)

    def set_output(self, n:int, state:bool, duration:Optional[int]=None) -> bool:
        if duration is None:
            inst = b'OS'
            data = as_bytes(n) + b'H' if state else as_bytes(n) + b'L'
        else:
            inst = b'OT'
            data = as_bytes(n) + b'H' if state else as_bytes(n) + b'L'
            data += as_bytes(int(duration*2))
        recv = self.cmd(inst, data)

        if self.check_reponse(recv):
            return True
        else:
            raise QuidoError("Failed to set output", recv)

    def get_output(self, n:int) -> bool:
        inst = b'OR'
        data = as_bytes(n)
        recv = self.cmd(inst, data)

        if self.check_reponse(recv):
            return True if recv[4] == 'H' else False
        else:
            raise QuidoError("Failed to get output", recv)

    def get_input(self, n:int) -> bool:
        inst = b'IR'
        data = as_bytes(n)
        recv = self.cmd(inst, data)

        if self.check_reponse(recv):
            return True if recv[4] == 'H' else False
        else:
            raise QuidoError("Failed to get input", recv)

    def wait_for_edge(self, n: int, timeout:float=None) -> bool:
        v0 = self.get_input(n)
        v1 = v0

        recv = self.cmd(b'IS', b'1')
        if not self.check_reponse(recv):
            raise QuidoError("IS1 command failed", recv)

        while v1 == v0:
            recv = self.recv()

            if self.check_reponse(recv):
                raise QuidoError("Wrong reply", recv)
            else:
                v1 = get_val_is(recv, n)

        recv = self.cmd(b'IS', b'0')
        if not self.check_reponse(recv):
            raise QuidoError("IS0 command failed", recv)

        return v1


def get_val_is(recv, n:int) -> bool:
    recv = recv[5:]
    return True if recv[n-1] == 'H' else False


def read_util(ser, eol:bytes = b'\r') -> bytes:
    buffer = bytearray()
    while True:
        one_byte = ser.read(1)
        if one_byte == eol:
            return bytes(buffer)
        else:
            buffer.extend(one_byte)


def as_bytes(val: Any) -> bytes:
    return str(val).encode()
