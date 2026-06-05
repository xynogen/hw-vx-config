"""Tests for hw_vx_config.device — transport layer is mocked."""

from __future__ import annotations

from unittest.mock import MagicMock, call, patch

import pytest

from hw_vx_config.device import HwVxDevice
from hw_vx_config.models import DeviceConfig, SearchResult


@pytest.fixture()
def mock_transport() -> MagicMock:
    """A fully mocked HwVxNetworking instance."""
    transport = MagicMock()
    transport.search.return_value = [
        SearchResult(
            mac_address="AA:BB:CC:DD:EE:FF",
            port_number="4196",
            ip_address="192.168.1.100",
        )
    ]
    transport.request.return_value = "OK"
    return transport


@pytest.fixture()
def device(mock_transport: MagicMock) -> HwVxDevice:
    """HwVxDevice with mocked transport."""
    with patch("hw_vx_config.device.HwVxNetworking", return_value=mock_transport):
        dev = HwVxDevice("192.168.1.100")
    return dev


class TestConnect:
    def test_sets_mac_from_search(self, device: HwVxDevice, mock_transport: MagicMock) -> None:
        result = device.connect()
        assert device.mac == "AA:BB:CC:DD:EE:FF"
        assert result.ip_address == "192.168.1.100"

    def test_sends_select_and_login(self, device: HwVxDevice, mock_transport: MagicMock) -> None:
        device.connect()
        mock_transport.request.assert_any_call("WAA:BB:CC:DD:EE:FF", retries=3)
        mock_transport.request.assert_any_call("L", retries=3)

    def test_raises_on_no_readers(self, device: HwVxDevice, mock_transport: MagicMock) -> None:
        mock_transport.search.return_value = []
        with pytest.raises(ConnectionError, match="No reader found"):
            device.connect()


class TestGetConfig:
    def test_reads_all_settings(self, device: HwVxDevice, mock_transport: MagicMock) -> None:
        # Map each check token to a value
        values = {
            "1": "admin",
            "2": "MyDevice",
            "3": "AA:BB",
            "4": "192.168.1.100",
            "5": "4196",
            "6": "0",
            "7": "0",
            "8": "0",
            "9": "60",
            "10": "0",
            "11": "0",
            "12": "3",
            "13": "0",
            "14": "1",
            "15": "0",
            "16": "1024",
            "17": "0",
            "18": "192.168.1.1",
            "19": "5000",
            "20": "192.168.1.1",
            "21": "255.255.255.0",
            "22": "0",
        }

        def fake_request_single(cmd: str, check: str) -> str:
            return values[check]

        mock_transport.request_single.side_effect = fake_request_single

        device.connect()
        cfg = device.get_config()

        assert cfg.username == "admin"
        assert cfg.device_name == "MyDevice"
        assert cfg.ip_address == "192.168.1.100"
        assert cfg.baud_rate == "3"
        assert cfg.subnet_mask == "255.255.255.0"
        assert cfg.dhcp == "0"
        assert mock_transport.request_single.call_count == 22


class TestSaveConfig:
    def test_sends_login_and_reboot(
        self, device: HwVxDevice, mock_transport: MagicMock, sample_config: DeviceConfig
    ) -> None:
        device.mac = "AA:BB:CC:DD:EE:FF"

        with patch("hw_vx_config.device.HwVxNetworking") as mock_net:
            broadcast_mock = MagicMock()
            mock_net.return_value = broadcast_mock
            broadcast_mock.__enter__ = MagicMock(return_value=broadcast_mock)
            broadcast_mock.__exit__ = MagicMock(return_value=False)

            device.save_config(sample_config)

        # Unicast pass should start with login
        send_calls = [c for c in mock_transport.send.call_args_list]
        assert send_calls[0] == call("L")
        # Last unicast call should be reboot
        unicast_commands = [c[0][0] for c in send_calls]
        assert "E" in unicast_commands


class TestChangeIp:
    def test_sends_ip_change_and_reboot(
        self, device: HwVxDevice, mock_transport: MagicMock
    ) -> None:
        device.mac = "AA:BB:CC:DD:EE:FF"
        mock_transport.receive.return_value = ""

        with patch("hw_vx_config.device.HwVxNetworking") as mock_net:
            broadcast_mock = MagicMock()
            mock_net.return_value = broadcast_mock
            broadcast_mock.__enter__ = MagicMock(return_value=broadcast_mock)
            broadcast_mock.__exit__ = MagicMock(return_value=False)
            broadcast_mock.receive.return_value = ""

            device.change_ip("10.0.0.50")

        unicast_cmds = [c[0][0] for c in mock_transport.send.call_args_list]
        assert "SIP10.0.0.50|34" in unicast_cmds
        assert "E|35" in unicast_cmds


class TestSetDhcp:
    def test_enable_dhcp(self, device: HwVxDevice, mock_transport: MagicMock) -> None:
        device.set_dhcp(True)
        cmds = [c[0][0] for c in mock_transport.send.call_args_list]
        assert "SDH1|40" in cmds
        assert "E" in cmds

    def test_disable_dhcp(self, device: HwVxDevice, mock_transport: MagicMock) -> None:
        device.set_dhcp(False)
        cmds = [c[0][0] for c in mock_transport.send.call_args_list]
        assert "SDH0|40" in cmds


class TestReboot:
    def test_sends_reboot(self, device: HwVxDevice, mock_transport: MagicMock) -> None:
        device.reboot()
        mock_transport.send.assert_called_once_with("E")


class TestContextManager:
    def test_closes_transport(self, mock_transport: MagicMock) -> None:
        with (
            patch("hw_vx_config.device.HwVxNetworking", return_value=mock_transport),
            HwVxDevice("1.2.3.4") as _dev,
        ):
            pass
        mock_transport.close.assert_called_once()
