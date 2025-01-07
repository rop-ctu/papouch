
import asyncio
import logging
from typing import Any, Awaitable, Callable, List, Optional
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
        self._input_change_cb: Optional[Callable[[List[bool]], Awaitable[Any]]] = None

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
                    await self._process_unsolicited_msg(recv)

            except asyncio.CancelledError:
                break
            except Exception as e:
                raise QuidoError(f"Failed to read from serial: {e}")

    async def _process_unsolicited_msg(self, msg: str) -> bool:
        if (len(msg) >= 3 and msg[:2] == "*B" and msg[3] == "D" and self._input_change_cb is not None):
            inputs = [True if v == "H" else False for v in msg[5:].replace(" ", "")]
            log.debug("Input change notification:  %s", str(inputs))
            await self._input_change_cb(inputs)
            return True
        return False

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

    async def get_temperature(self, n=1, adr=b'$'):
        inst = b'TR'
        data = as_bytes(n)
        recv = await self._cmd(inst, data, adr=adr)

        if self.check_reponse(recv, adr):
            return float(recv[4:-2])
        else:
            log.error("Unable to read temperature, response: %s", recv)
            return None

    async def set_output(self, n, state, duration=None, adr=b'$') -> bool:
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

    async def get_output(self, n, adr=b'$') -> bool:
        inst = b'OR'
        data = as_bytes(n)
        recv = await self._cmd(inst, data, adr=adr)

        if self.check_reponse(recv, adr):
            return True if recv[4] == 'H' else False
        else:
            log.error("Unable to get output, response: %s", recv)
            return False

    async def get_input(self, n, adr=b'$') -> bool:
        inst = b'IR'
        data = as_bytes(n)
        recv = await self._cmd(inst, data, adr=adr)

        if self.check_reponse(recv, adr):
            return True if recv[4] == 'H' else False
        else:
            log.error("Unable to get input, response: %s", recv)
            return False

    async def set_change_reporting(self, enabled: bool, adr=b'$') -> bool:
        value = b'1' if enabled else b'0'
        recv = await self._cmd(b'IS', value, adr=adr)
        if self.check_reponse(recv, adr):
            return True
        else:
            log.error("Failed to set change reporting, response: %s", recv)
            return False

    def set_input_change_cb(self, cb: Callable[[List[bool]], None]):
        if self._input_change_cb is not None:
            raise QuidoError("Input change handler already set")
        self._input_change_cb = cb

    def clear_input_change_cb(self):
        self._input_change_cb = None


def parse_automatic_reply(recv, n):
    recv = recv[5:]
    return True if recv[n-1] == 'H' else False

def as_bytes(val: Any):
    return str(val).encode()
