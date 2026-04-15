from typing import Optional


class QuidoError(Exception):
    def __init__(self, message: str, recv: Optional[bytes] = None):
        super().__init__()
        self._msg = message
        self._recv = recv

    def __str__(self):
        return self._msg + (", data: " + repr(self._recv)) if self._recv else ""

