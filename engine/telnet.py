"""
Minimal Telnet protocol handler.

Only handles:
- IAC WILL/WONT/DO/DONT option negotiation (consumed silently)
- IAC WILL ECHO / IAC DO NAWS on connect
- Stripping IAC sequences from the byte stream
- Delivering complete UTF-8 lines via async generator
"""
from __future__ import annotations
import asyncio

# Telnet constants
IAC  = 255
WILL = 251
WONT = 252
DO   = 253
DONT = 254
SB   = 250   # subnegotiation begin
SE   = 240   # subnegotiation end
ECHO = 1
NAWS = 31


class TelnetHandler:
    def __init__(self, writer: asyncio.StreamWriter):
        self.writer = writer
        self._buf = bytearray()

    async def negotiate(self):
        # Tell client we WILL handle echo; ask for window size
        self.writer.write(bytes([IAC, WILL, ECHO, IAC, DO, NAWS]))
        await self.writer.drain()

    async def lines(self, reader: asyncio.StreamReader):
        """Async generator yielding decoded lines (strips IAC sequences)."""
        while True:
            try:
                chunk = await reader.read(256)
            except (asyncio.IncompleteReadError, ConnectionResetError):
                break
            if not chunk:
                break
            self._buf.extend(chunk)
            while True:
                line, sep, rest = self._buf.partition(b"\n")
                if not sep:
                    break
                self._buf = bytearray(rest)
                clean = self._strip_iac(bytes(line))
                text = clean.decode("utf-8", errors="replace").rstrip("\r\n ")
                yield text

    @staticmethod
    def _strip_iac(data: bytes) -> bytes:
        out = bytearray()
        i = 0
        while i < len(data):
            b = data[i]
            if b == IAC:
                i += 1
                if i >= len(data):
                    break
                cmd = data[i]
                if cmd in (WILL, WONT, DO, DONT):
                    i += 2  # skip option byte
                elif cmd == SB:
                    # skip until IAC SE
                    i += 1
                    while i < len(data) - 1:
                        if data[i] == IAC and data[i + 1] == SE:
                            i += 2
                            break
                        i += 1
                else:
                    i += 1  # skip single-byte command
            else:
                out.append(b)
                i += 1
        return bytes(out)
