"""
UHF RFID binary protocol (UHFReader18) over TCP.

This module implements the binary frame protocol used by the RFID reader
for reader-defined commands (Set Address, Get Reader Information, etc.).
The HW-VX module bridges serial ↔ TCP, so these frames are sent over
the device's configured TCP port.

Frame format (command):
    Len | Adr | Cmd | Data[] | LSB-CRC16 | MSB-CRC16

Frame format (response):
    Len | Adr | reCmd | Status | Data[] | LSB-CRC16 | MSB-CRC16
"""

from __future__ import annotations

import socket
from dataclasses import dataclass

# ─── CRC-16 ──────────────────────────────────────────────────────────

_PRESET_VALUE = 0xFFFF
_POLYNOMIAL = 0x8408


def crc16(data: bytes) -> int:
    """
    Compute CRC-16 per the UHFReader18 spec.

    Uses preset 0xFFFF and polynomial 0x8408 (bit-reversed 0x1021).
    """
    crc = _PRESET_VALUE
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ _POLYNOMIAL
            else:
                crc >>= 1
    return crc & 0xFFFF


# ─── Frame helpers ───────────────────────────────────────────────────


def build_frame(adr: int, cmd: int, data: bytes = b"") -> bytes:
    """
    Build a command frame ready to send.

    Parameters
    ----------
    adr : int
        Reader address (0x00-0xFE, 0xFF = broadcast).
    cmd : int
        Command byte.
    data : bytes
        Optional command parameters.

    Returns
    -------
    bytes
        Complete frame including length and CRC-16.
    """
    # Len = len(Data[]) + 4  (Adr + Cmd + CRC16x2)
    length = len(data) + 4
    payload = bytes([length, adr, cmd]) + data
    checksum = crc16(payload)
    return payload + bytes([checksum & 0xFF, (checksum >> 8) & 0xFF])


@dataclass
class RfidResponse:
    """Parsed response from the RFID reader."""

    length: int
    address: int
    command: int
    status: int
    data: bytes
    crc: int

    @property
    def ok(self) -> bool:
        """True when status indicates success (0x00)."""
        return self.status == 0x00

    @property
    def status_text(self) -> str:
        """Human-readable status description."""
        return _STATUS_CODES.get(self.status, f"Unknown (0x{self.status:02X})")


_STATUS_CODES: dict[int, str] = {
    0x00: "Success",
    0x01: "Inventory finished (partial)",
    0x02: "Inventory scan-time overflow",
    0x03: "More data (multi-packet)",
    0x04: "Reader flash full",
    0x05: "Access password error",
    0x09: "Kill tag error",
    0x0A: "Kill password cannot be zero",
    0x0B: "Tag does not support command",
    0x0C: "Access password cannot be zero",
    0x0D: "Tag already protected",
    0x0E: "Tag not protected",
    0x10: "6B locked bytes, write fail",
    0x11: "6B cannot lock",
    0x12: "6B already locked",
    0x13: "Save fail (use before power-off)",
    0x14: "Cannot adjust power",
    0xF9: "Command execute error",
    0xFA: "Tag found but poor communication",
    0xFB: "No tag in effective field",
    0xFC: "Tag returned error code",
    0xFD: "Command length wrong",
    0xFE: "Illegal command or CRC error",
    0xFF: "Parameter error",
}


def parse_response(raw: bytes) -> RfidResponse:
    """
    Parse a response frame from the reader.

    Raises
    ------
    ValueError
        If the frame is too short or CRC doesn't match.
    """
    if len(raw) < 5:
        raise ValueError(f"Response too short ({len(raw)} bytes): {raw.hex()}")

    length = raw[0]
    frame = raw[: length + 1]  # +1 for the length byte itself

    if len(frame) < length + 1:
        raise ValueError(f"Incomplete frame: expected {length + 1} bytes, got {len(frame)}")

    # Verify CRC (computed over everything except the 2 CRC bytes)
    payload = frame[:-2]
    received_crc = frame[-2] | (frame[-1] << 8)
    computed_crc = crc16(payload)
    if received_crc != computed_crc:
        raise ValueError(
            f"CRC mismatch: received 0x{received_crc:04X}, computed 0x{computed_crc:04X}"
        )

    return RfidResponse(
        length=length,
        address=frame[1],
        command=frame[2],
        status=frame[3],
        data=frame[4:-2] if length > 5 else b"",
        crc=received_crc,
    )


# ─── Reader commands ─────────────────────────────────────────────────

# Command codes (reader-defined)
CMD_GET_READER_INFO = 0x21
CMD_SET_REGION = 0x22
CMD_SET_ADDRESS = 0x24
CMD_SET_SCAN_TIME = 0x25
CMD_SET_BAUD_RATE = 0x28
CMD_SET_POWER = 0x2F
CMD_ACOUSTO_OPTIC = 0x33

# EPC C1G2 commands
CMD_INVENTORY = 0x01


@dataclass
class ReaderInfo:
    """Parsed Get Reader Information response."""

    address: int
    version: str
    reader_type: int
    protocol_type: int
    max_freq: int
    min_freq: int
    power: int
    scan_time: int


class RfidClient:
    """
    TCP client for the UHF RFID binary protocol.

    Connects to the HW-VX module's TCP port (the port configured
    in the module's network settings) and sends binary RFID commands.

    Parameters
    ----------
    ip : str
        Device IP address.
    port : int
        TCP port (from the device's network config, typically 2077 or similar).
    timeout : float
        Socket timeout in seconds.
    """

    def __init__(self, ip: str, port: int, timeout: float = 3.0) -> None:
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self._sock: socket.socket | None = None

    def connect(self) -> None:
        """Establish TCP connection to the reader."""
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(self.timeout)
        self._sock.connect((self.ip, self.port))

    def close(self) -> None:
        """Close the TCP connection."""
        if self._sock:
            self._sock.close()
            self._sock = None

    def __enter__(self) -> RfidClient:
        self.connect()
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _send_command(self, adr: int, cmd: int, data: bytes = b"") -> RfidResponse:
        """Send a command frame and wait for the response."""
        if not self._sock:
            raise ConnectionError("Not connected — call connect() first")

        frame = build_frame(adr, cmd, data)
        self._sock.sendall(frame)
        raw = self._sock.recv(1024)
        if not raw:
            raise ConnectionError("No response from reader")
        return parse_response(raw)

    # ── Reader-defined commands ──────────────────────────────────────

    def get_reader_info(self, adr: int = 0x00) -> ReaderInfo:
        """
        Get reader information (address, firmware, power, etc.).

        Cmd 0x21 — no data payload.
        """
        resp = self._send_command(adr, CMD_GET_READER_INFO)
        if not resp.ok:
            raise RuntimeError(f"Get reader info failed: {resp.status_text}")

        d = resp.data
        if len(d) < 7:
            raise ValueError(f"Unexpected info response length: {len(d)} bytes")

        return ReaderInfo(
            address=resp.address,
            version=f"{d[0]}.{d[1]}",
            reader_type=d[2],
            protocol_type=d[3],
            max_freq=d[4],
            min_freq=d[5],
            power=d[6],
            scan_time=d[7] if len(d) > 7 else 0,
        )

    def discover_address(self) -> tuple[ReaderInfo, int]:
        """
        Find the reader's real address via broadcast.

        The HW-VX module's network config exposes the *module*'s TCP port,
        but the *reader* behind the serial port lives at a 0-254 address
        that is set on the reader itself — and that address is not visible
        in the network config. UHFReader18 guarantees that every reader on
        the bus answers to the broadcast address ``0xFF`` and reveals its
        real address in the reply's Adr byte. We use that single round-trip
        to learn the address, then return it so the caller can talk to the
        reader directly.

        Raises
        ------
        ConnectionError
            If the reader doesn't reply to broadcast — i.e. it's dead or
            the serial link is broken (not just an address mismatch).
        """
        try:
            info = self.get_reader_info(0xFF)
        except (TimeoutError, ConnectionError) as exc:
            # Normalise to ConnectionError: TimeoutError and ConnectionError
            # are sibling OSError subclasses, so callers need a single except.
            raise ConnectionError(
                "Reader did not respond to broadcast — check power and serial wiring"
            ) from exc
        return info, info.address

    def set_address(self, current_adr: int, new_adr: int) -> RfidResponse:
        """
        Set a new reader address (Cmd 0x24).

        Parameters
        ----------
        current_adr : int
            Current reader address (0x00-0xFE).
        new_adr : int
            New address (0x00-0xFE). 0xFF is reserved (broadcast) and
            will be auto-set to 0x00 by the reader.

        Returns
        -------
        RfidResponse
            The reader's acknowledgement (Adr in response is the *old* address).
        """
        if not (0x00 <= new_adr <= 0xFE):
            raise ValueError(f"Address must be 0x00-0xFE, got 0x{new_adr:02X}")
        resp = self._send_command(current_adr, CMD_SET_ADDRESS, bytes([new_adr]))
        if not resp.ok:
            raise RuntimeError(f"Set address failed: {resp.status_text}")
        return resp

    def set_power(self, adr: int, power: int) -> RfidResponse:
        """
        Set the reader's RF output power (Cmd 0x2F).

        Parameters
        ----------
        adr : int
            Reader address.
        power : int
            Power level 0-30 (dBm).
        """
        if not (0 <= power <= 30):
            raise ValueError(f"Power must be 0-30, got {power}")
        resp = self._send_command(adr, CMD_SET_POWER, bytes([power]))
        if not resp.ok:
            raise RuntimeError(f"Set power failed: {resp.status_text}")
        return resp

    def set_scan_time(self, adr: int, scan_time: int) -> RfidResponse:
        """
        Set inventory scan time (Cmd 0x25).

        Parameters
        ----------
        adr : int
            Reader address.
        scan_time : int
            Scan time 3-255 (x100ms). Values 0-2 are auto-set to 10 by reader.
        """
        if not (0 <= scan_time <= 255):
            raise ValueError(f"Scan time must be 0-255, got {scan_time}")
        resp = self._send_command(adr, CMD_SET_SCAN_TIME, bytes([scan_time]))
        if not resp.ok:
            raise RuntimeError(f"Set scan time failed: {resp.status_text}")
        return resp
