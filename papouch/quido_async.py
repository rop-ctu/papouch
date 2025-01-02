
import asyncio
import logging
from typing import Any
import serial
import serial_asyncio


log = logging.getLogger()

class QuidoError(Exception):
    def __init__(self, message):
        super().__init__(message)


class QuidoUSB():

    def __init__(self, port, baud=115200, timeout=5):
        self.port = port
        self.baudrate = baud
        self.timeout = timeout
        self.reader = None
        self.writer = None
        self.queue = asyncio.Queue()
        self.expecting_response = asyncio.Event()
        self.input_change_cb = None

    async def connect(self):
        try:
            self.reader, self.writer = await serial_asyncio.open_serial_connection(
                url=self.port,
                baudrate=self.baudrate
            )
        except Exception as e:
            raise QuidoError(f"Unable to connect: {str(e)}")

        asyncio.create_task(self._recv())

    async def _recv(self):
        if self.reader is None:
            raise QuidoError("No active connection")

        log.debug("Recv task is started")
        while True:
            try:
                recv = await self.reader.readuntil(b'\r')
                log.debug("Serial read:  %s", recv) # double space is intentional to align with serial write
                recv = recv.decode().strip()

                if self.expecting_response.is_set():
                    await self.queue.put(recv)
                    self.expecting_response.clear()
                else:
                    self.process_unsolicited_msg(recv)

            except asyncio.CancelledError:
                break
            except Exception as e:
                raise QuidoError(f"Failed to read from serial: {e}")

    def process_unsolicited_msg(self, msg):
        log.debug("Unsolicited:  %s", msg) # double space is intentional to align with serial write
        pass

    async def _cmd(self, inst, data=b'', adr=b'$'):
        if not self.writer:
            raise QuidoError("No active connection")

        msg = b'*B' + adr + inst + data + b'\r'
        log.debug("Serial write: %s", msg)

        self.writer.write(msg)
        await self.writer.drain()

        self.expecting_response.set()
        try:
            resp = await asyncio.wait_for(self.queue.get(), timeout=self.timeout)
            return resp
        except asyncio.TimeoutError:
            raise QuidoError(f"Timeout while executing '{msg}'")
        except Exception as e:
            raise QuidoError(f"Exception while executing '{msg}': {e}")
        finally:
            self.expecting_response.clear()

    async def close(self):
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()

    def check_reponse(self, resp, adr=b'$'):
        if adr == b'$':
            return len(resp) > 3 and resp[3] == '0'
        else:
            return len(resp) > 3 and resp[3] == '0' and resp[2] == adr

    async def reset(self, adr=b'$'):
        inst = b'RE'
        recv = await self._cmd(inst, adr=adr)

        if self.check_reponse(recv, adr):
            return True
        else:
            log.error("Unable reset, response: %s", recv)
            return None

    async def get_name(self, adr=b'$'):
        inst = b'?'
        recv = await self._cmd(inst, adr=adr)

        if self.check_reponse(recv, adr):
            return [v.strip() for v in recv[4:-1].split(';')]
        else:
            log.error("Unable to read name, response: %s", recv)
            return None

    async def get_temperature(self, n, adr=b'$'):
        inst = b'TR'
        data = as_bytes(n)
        recv = await self._cmd(inst, data, adr=adr)

        if self.check_reponse(recv, adr):
            return float(recv[4:-2])
        else:
            log.error("Unable to read temperature, response: %s", recv)
            return None

    async def set_output(self, n, state, duration=None, adr=b'$'):
        if duration is None:
            inst = b'OS'
            data = as_bytes(n) + b'H' if state else as_bytes(n) + b'L'
        else:
            inst = b'OT'
            data = as_bytes(n) + b'H' if state else as_bytes(n) + b'L'
            data += as_bytes(int(duration*2))
        recv = await self._cmd(inst, data, adr=adr)

        if self.check_reponse(recv, adr):
            return True
        else:
            log.error("Unable to set output, response: %s", recv)
            return False

    async def get_output(self, n, adr=b'$'):
        inst = b'OR'
        data = as_bytes(n)
        recv = await self._cmd(inst, data, adr=adr)

        if self.check_reponse(recv, adr):
            return True if recv[4] == 'H' else False
        else:
            log.error("Unable to get output, response: %s", recv)
            return False

    async def get_input(self, n, adr=b'$'):
        inst = b'IR'
        data = as_bytes(n)
        recv = await self._cmd(inst, data, adr=adr)

        if self.check_reponse(recv, adr):
            return True if recv[4] == 'H' else False
        else:
            log.error("Unable to get input, response: %s", recv)
            return False


def as_bytes(val: Any):
    return str(val).encode()
