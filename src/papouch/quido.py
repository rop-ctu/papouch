
import logging
import requests
import socket

log = logging.getLogger()


class Quido(object):

    def __init__(self):
        pass

    def connect_tcp(self, ip, port):
        self.tcp_ip = ip
        self.tcp_port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.tcp_ip, self.tcp_port))
        self.cmd = self.__cmd_tcp

    def check_reponse(self, resp):
        return len(resp) > 3 and resp[3] == '0'

    def __cmd_tcp(self, inst, data='', adr='$', buff=1000):
        msg = '*B' + adr + inst + data + '\r'
        self.socket.send(msg)
        log.debug("Cmd send: %s", msg)
        recv = self.socket.recv(buff)
        log.debug("Cmd recv: %s", recv)
        return recv

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
            return 1 if recv[4] == 'H' else 0
        else:
            log.error("Unable to get output, response: %s", recv)
            return False

    def get_input(self, n):
        inst = 'IR'
        data = str(n)
        recv = self.cmd(inst, data)

        if self.check_reponse(recv):
            return 1 if recv[4] == 'H' else 0
        else:
            log.error("Unable to get input, response: %s", recv)
            return False


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
