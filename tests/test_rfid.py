"""Tests for the UHF RFID binary protocol module."""

from __future__ import annotations

import socket
from unittest.mock import MagicMock, patch

import pytest

from hw_vx_config.rfid import (
    CMD_GET_READER_INFO,
    CMD_SET_ADDRESS,
    RfidClient,
    RfidResponse,
    build_frame,
    crc16,
    parse_response,
)

# -- CRC-16 ---------------------------------------------------------------


class TestCrc16:
    def test_empty(self) -> None:
        assert crc16(b"") == 0xFFFF

    def test_known_frame(self) -> None:
        """CRC of a Set Address command payload (Len=0x05, Adr=0x00, Cmd=0x24, Data=0x01)."""
        payload = bytes([0x05, 0x00, 0x24, 0x01])
        result = crc16(payload)
        # Rebuild the full frame and verify round-trip
        frame = payload + bytes([result & 0xFF, (result >> 8) & 0xFF])
        assert crc16(frame[:-2]) == result

    def test_deterministic(self) -> None:
        data = bytes([0x04, 0x00, 0x21])
        assert crc16(data) == crc16(data)


# -- build_frame -----------------------------------------------------------


class TestBuildFrame:
    def test_no_data(self) -> None:
        """Get Reader Info: Len=0x04, Adr=0x00, Cmd=0x21, CRC16."""
        frame = build_frame(0x00, CMD_GET_READER_INFO)
        assert frame[0] == 0x04  # Len = 0 + 4
        assert frame[1] == 0x00  # Adr
        assert frame[2] == 0x21  # Cmd
        assert len(frame) == 5  # 1(len) + 1(adr) + 1(cmd) + 2(crc)

    def test_with_data(self) -> None:
        """Set Address: Len=0x05, Adr=0x00, Cmd=0x24, Data=0x01, CRC16."""
        frame = build_frame(0x00, CMD_SET_ADDRESS, bytes([0x01]))
        assert frame[0] == 0x05  # Len = 1 + 4
        assert frame[1] == 0x00  # Adr
        assert frame[2] == 0x24  # Cmd
        assert frame[3] == 0x01  # Data (new address)
        assert len(frame) == 6

    def test_crc_valid(self) -> None:
        """Built frame should have valid CRC."""
        frame = build_frame(0x00, CMD_GET_READER_INFO)
        payload = frame[:-2]
        expected_crc = crc16(payload)
        actual_crc = frame[-2] | (frame[-1] << 8)
        assert actual_crc == expected_crc

    def test_broadcast_address(self) -> None:
        frame = build_frame(0xFF, CMD_GET_READER_INFO)
        assert frame[1] == 0xFF


# -- parse_response --------------------------------------------------------


class TestParseResponse:
    def _make_response(self, adr: int, cmd: int, status: int, data: bytes = b"") -> bytes:
        """Build a valid response frame for testing."""
        length = len(data) + 5
        payload = bytes([length, adr, cmd, status]) + data
        checksum = crc16(payload)
        return payload + bytes([checksum & 0xFF, (checksum >> 8) & 0xFF])

    def test_success_no_data(self) -> None:
        raw = self._make_response(0x00, CMD_SET_ADDRESS, 0x00)
        resp = parse_response(raw)
        assert resp.ok
        assert resp.address == 0x00
        assert resp.command == CMD_SET_ADDRESS
        assert resp.status == 0x00
        assert resp.data == b""

    def test_success_with_data(self) -> None:
        info_data = bytes([0x02, 0x24, 0x09, 0x03, 0x20, 0x00, 0x1E, 0x0A])
        raw = self._make_response(0x00, CMD_GET_READER_INFO, 0x00, info_data)
        resp = parse_response(raw)
        assert resp.ok
        assert resp.data == info_data

    def test_error_status(self) -> None:
        raw = self._make_response(0x00, CMD_SET_ADDRESS, 0xFF)
        resp = parse_response(raw)
        assert not resp.ok
        assert resp.status == 0xFF
        assert "Parameter error" in resp.status_text

    def test_too_short(self) -> None:
        with pytest.raises(ValueError, match="too short"):
            parse_response(bytes([0x01, 0x02]))

    def test_bad_crc(self) -> None:
        raw = self._make_response(0x00, CMD_SET_ADDRESS, 0x00)
        # Corrupt the CRC
        corrupted = raw[:-1] + bytes([raw[-1] ^ 0xFF])
        with pytest.raises(ValueError, match="CRC mismatch"):
            parse_response(corrupted)

    def test_status_text_unknown(self) -> None:
        raw = self._make_response(0x00, 0x99, 0x42)
        resp = parse_response(raw)
        assert "Unknown" in resp.status_text


# -- RfidResponse ----------------------------------------------------------


class TestRfidResponse:
    def test_ok_property(self) -> None:
        resp = RfidResponse(5, 0x00, 0x24, 0x00, b"", 0)
        assert resp.ok

    def test_not_ok(self) -> None:
        resp = RfidResponse(5, 0x00, 0x24, 0xFE, b"", 0)
        assert not resp.ok
        assert "Illegal command" in resp.status_text


# -- RfidClient (mocked socket) -------------------------------------------


class TestRfidClient:
    def _make_response(self, adr: int, cmd: int, status: int, data: bytes = b"") -> bytes:
        length = len(data) + 5
        payload = bytes([length, adr, cmd, status]) + data
        checksum = crc16(payload)
        return payload + bytes([checksum & 0xFF, (checksum >> 8) & 0xFF])

    @patch("hw_vx_config.rfid.socket.socket")
    def test_get_reader_info(self, mock_socket_cls: MagicMock) -> None:
        info_data = bytes([0x02, 0x24, 0x09, 0x03, 0x20, 0x00, 0x1E, 0x0A])
        mock_sock = MagicMock()
        mock_sock.recv.return_value = self._make_response(
            0x00, CMD_GET_READER_INFO, 0x00, info_data
        )
        mock_socket_cls.return_value = mock_sock

        with RfidClient("192.168.1.100", 2077) as client:
            info = client.get_reader_info(0x00)

        assert info.address == 0x00
        assert info.version == "2.36"
        assert info.reader_type == 0x09
        assert info.power == 30
        assert info.scan_time == 10

    @patch("hw_vx_config.rfid.socket.socket")
    def test_set_address(self, mock_socket_cls: MagicMock) -> None:
        mock_sock = MagicMock()
        mock_sock.recv.return_value = self._make_response(0x00, CMD_SET_ADDRESS, 0x00)
        mock_socket_cls.return_value = mock_sock

        with RfidClient("192.168.1.100", 2077) as client:
            resp = client.set_address(0x00, 0x01)

        assert resp.ok
        # Verify the frame sent contains the right command and data
        sent_frame = mock_sock.sendall.call_args[0][0]
        assert sent_frame[2] == CMD_SET_ADDRESS
        assert sent_frame[3] == 0x01  # new address

    @patch("hw_vx_config.rfid.socket.socket")
    def test_set_address_error(self, mock_socket_cls: MagicMock) -> None:
        mock_sock = MagicMock()
        mock_sock.recv.return_value = self._make_response(0x00, CMD_SET_ADDRESS, 0xFF)
        mock_socket_cls.return_value = mock_sock

        with (
            RfidClient("192.168.1.100", 2077) as client,
            pytest.raises(RuntimeError, match="Set address failed"),
        ):
            client.set_address(0x00, 0x01)

    def test_set_address_invalid_range(self) -> None:
        client = RfidClient("192.168.1.100", 2077)
        client._sock = MagicMock()
        with pytest.raises(ValueError, match="0x00-0xFE"):
            client.set_address(0x00, 0xFF)

    @patch("hw_vx_config.rfid.socket.socket")
    def test_not_connected_raises(self, mock_socket_cls: MagicMock) -> None:
        client = RfidClient("192.168.1.100", 2077)
        with pytest.raises(ConnectionError, match="Not connected"):
            client.get_reader_info()

    @patch("hw_vx_config.rfid.socket.socket")
    def test_no_response_raises(self, mock_socket_cls: MagicMock) -> None:
        mock_sock = MagicMock()
        mock_sock.recv.return_value = b""
        mock_socket_cls.return_value = mock_sock

        with (
            RfidClient("192.168.1.100", 2077) as client,
            pytest.raises(ConnectionError, match="No response"),
        ):
            client.get_reader_info()


# -- discover_address (broadcast-first) --------------------------------


_INFO_PAYLOAD = bytes([0x02, 0x24, 0x09, 0x03, 0x20, 0x00, 0x1E, 0x0A])


def _info_frame(reply_adr: int) -> bytes:
    """Build a valid Get Reader Information response frame for *reply_adr*."""
    length = len(_INFO_PAYLOAD) + 5
    payload = bytes([length, reply_adr, CMD_GET_READER_INFO, 0x00]) + _INFO_PAYLOAD
    checksum = crc16(payload)
    return payload + bytes([checksum & 0xFF, (checksum >> 8) & 0xFF])


class TestDiscoverAddress:
    """
    ``RfidClient.discover_address`` sends exactly one frame — broadcast
    ``0xFF`` — and returns ``(info, address)`` from the reply. The reader's
    Adr byte in the response is the only truth: works on any device, no
    cache, no matter what address it was commissioned with.
    """

    @patch("hw_vx_config.rfid.socket.socket")
    def test_returns_address_from_broadcast(self, mock_socket_cls: MagicMock) -> None:
        """Single broadcast frame; the reply's Adr byte is the reader's address."""
        mock_sock = MagicMock()
        mock_sock.recv.return_value = _info_frame(0x07)
        mock_socket_cls.return_value = mock_sock

        with RfidClient("192.168.1.100", 2077) as client:
            info, adr = client.discover_address()

        # Exactly one sendall (the broadcast).
        assert mock_sock.sendall.call_count == 1
        sent_frame = mock_sock.sendall.call_args_list[0].args[0]
        # Frame layout: [Len, Adr, Cmd, ...CRC]; Adr byte must be 0xFF.
        assert sent_frame[1] == 0xFF
        assert adr == 0x07
        assert info.version == "2.36"

    @patch("hw_vx_config.rfid.socket.socket")
    def test_dead_reader_raises_connection_error(self, mock_socket_cls: MagicMock) -> None:
        """Broadcast times out → ConnectionError surfaces to the caller."""
        mock_sock = MagicMock()
        mock_sock.recv.side_effect = socket.timeout
        mock_socket_cls.return_value = mock_sock

        with (
            RfidClient("192.168.1.100", 2077) as client,
            pytest.raises(ConnectionError),
        ):
            client.discover_address()

    @patch("hw_vx_config.rfid.socket.socket")
    def test_address_zero_works(self, mock_socket_cls: MagicMock) -> None:
        """Reader at address 0 is a valid case (and the common default)."""
        mock_sock = MagicMock()
        mock_sock.recv.return_value = _info_frame(0x00)
        mock_socket_cls.return_value = mock_sock

        with RfidClient("192.168.1.100", 2077) as client:
            _info, adr = client.discover_address()

        assert adr == 0x00
