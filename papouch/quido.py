
import logging
import requests
import socket
import serial
import io
import time

log = logging.getLogger()

class PapouchError(Exception):

    def __init__(self, msg='', recv=None):
        self.msg = msg
        self.recv = recv

    def __str__(self):
        return repr(self.msg + ": " + self.recv)


class Quido(object):

    def __init__(self):
        self.connection = 'none'

    def connect_tcp(self, ip, port=1001):
        self.connection = 'tcp'
        self.tcp_ip = ip
        self.tcp_port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.tcp_ip, self.tcp_port))
        self.cmd = self.__cmd_tcp
        self.recv = self.__recv_tcp
        self.cmd('IS', '0') # disable sending changes
        log.debug("Connected to tcp ip: %s port: %s", self.tcp_ip, self.tcp_port)

    def __cmd_tcp(self, inst, data='', adr='$', buff=1000):
        msg = '*B' + adr + inst + data + '\r'
        self.socket.send(msg)
        log.debug("Cmd send: %s", msg)
        recv = self.__recv_tcp(buff)
        log.debug("Cmd recv: %s", recv)
        return recv

    def __recv_tcp(self, buff):
        recv = self.socket.recv(buff)
        log.debug("Cmd recv: %s", recv)
        return recv

    def connect_usb(self, dev, baud=115200):
        self.connection = 'serial'
        self.dev = dev
        self.baud = baud
        self.ser = serial.Serial(self.dev, self.baud)
        self.cmd = self.__cmd_serial
        self.recv = self.__recv_serial
        log.debug("Cennected to serial dev: %s baud: %d", self.dev, self.baud)

    def __cmd_serial(self, inst, data='', adr='$', buff=1000):
        msg = b'*B' + adr + inst + data + '\r'
        self.ser.write(msg)
        self.ser.flush()
        log.debug("Serial write: %s", msg)
        recv = self.__recv_serial()
        return recv

    def __recv_serial(self, buff=None):
        recv = read_util(self.ser)
        log.debug("Serial read: %s", recv)
        return recv

    def check_reponse(self, resp):
        return len(resp) > 3 and resp[3] == '0'

    def reset(self):
        inst = 'RE'
        recv = self.cmd(inst)

        if self.check_reponse(recv):
            return True
        else:
            log.error("Unable reset, response: %s", recv)
            return None

    def get_name(self):
        inst = '?'
        recv = self.cmd(inst)

        if self.check_reponse(recv):
            return [v.strip() for v in recv[4:-1].split(';')]
        else:
            log.error("Unable to read name, response: %s", recv)
            return None

    def get_temperature(self, n):
        inst = 'TR'
        data = str(n)
        recv = self.cmd(inst, data)

        if self.check_reponse(recv):
            return float(recv[4:-2])
        else:
            log.error("Unable to read temperature, response: %s", recv)
            return None

    def set_output(self, n, state, duration=None):
        if duration is None:
            inst = 'OS'
            data = str(n) + 'H' if state else str(n) + 'L'
        else:
            inst = 'OT'
            data = str(n) + 'H' if state else str(n) + 'L'
            data += str(int(duration*2))
        recv = self.cmd(inst, data)

        if self.check_reponse(recv):
            return True
        else:
            log.error("Unable to set output, response: %s", recv)
            return False

    def get_output(self, n):
        inst = 'OR'
        data = str(n)
        recv = self.cmd(inst, data)

        if self.check_reponse(recv):
            return True if recv[4] == 'H' else False
        else:
            log.error("Unable to get output, response: %s", recv)
            return False

    def get_input(self, n):
        inst = 'IR'
        data = str(n)
        recv = self.cmd(inst, data)

        if self.check_reponse(recv):
            return True if recv[4] == 'H' else False
        else:
            log.error("Unable to get input, response: %s", recv)
            return False

    def wait_for_edge(self, n, timeout=None):
        v0 = self.get_input(n)
        v1 = v0

        recv = self.cmd('IS', '1')
        if not self.check_reponse(recv):
            raise PapouchError("IS1 command failed", recv)

        while v1 == v0:
            recv = self.recv()

            if self.check_reponse(recv):
                raise PapouchError("Wrong reply", recv)
            else:
                v1 = get_val_is(recv, n)

        recv = self.cmd('IS', '0')
        if not self.check_reponse(recv):
            raise PapouchError("IS0 command failed", recv)

        return v1


def get_val_is(recv, n):
    recv = recv[5:]
    return True if recv[n-1] == 'H' else False


def read_util(ser, eol=b'\r'):
    buffer = ""
    while True:
        oneByte = ser.read(1)
        if oneByte == eol:
            return buffer
        else:
            buffer += oneByte.decode("ascii")


class QuidoWeb(object):

    HIGH = 's'
    LOW = 'r'
    TOGGLE = 'i'
    ALLHIGH = 'S'
    ALLLOW = 'R'

    def __init__(self, ip):
        """Initialize Quido module

        Arguments:
          ip    IP address of the module


        """
        self.ip = ip

    def set_output(self, n, state, duration=None):
        """
        """
        if state is True:
            action = 's'
        elif state is False:
            action = 'r'
        else:
            action = state

        cmd = "http://{}/set.xml?type={}&id={}".format(self.ip, action, n)

        # Call GET request
        r = requests.get(cmd)
