"""Tests for hw_vx_config.cli — argument parsing and version flag."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from hw_vx_config.cli import build_parser, main


def test_rfid_client_is_owned_by_uhfreader18() -> None:
    from uhfreader18 import RfidClient

    import hw_vx_config

    assert not hasattr(hw_vx_config, "RfidClient")
    assert RfidClient.__module__ == "uhfreader18.client"


class TestBuildParser:
    def test_subcommands_exist(self) -> None:
        parser = build_parser()
        # argparse stores sub-parsers; verify by parsing known commands
        args = parser.parse_args(["search"])
        assert args.command == "search"

    def test_search_network(self) -> None:
        args = build_parser().parse_args(["search", "--network", "10.10.0.0/24"])
        assert args.network == "10.10.0.0/24"

    def test_config_requires_ip(self) -> None:
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["config"])  # missing required 'ip'

    def test_set_ip_args(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["set-ip", "192.168.1.1", "10.0.0.1"])
        assert args.ip == "192.168.1.1"
        assert args.new_ip == "10.0.0.1"
        assert args.mask is None
        assert args.gateway is None

    def test_set_ip_with_mask_and_gateway(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            ["set-ip", "192.168.1.1", "10.0.0.1", "--mask", "255.255.0.0", "--gateway", "10.0.0.1"]
        )
        assert args.mask == "255.255.0.0"
        assert args.gateway == "10.0.0.1"

    def test_dhcp_state_choices(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["dhcp", "192.168.1.1", "on"])
        assert args.state == "on"

        with pytest.raises(SystemExit):
            parser.parse_args(["dhcp", "192.168.1.1", "maybe"])

    def test_reboot_args(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["reboot", "192.168.1.1"])
        assert args.ip == "192.168.1.1"

    def test_set_reader_power_args(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["set-reader-power", "192.168.1.1", "6000", "20"])
        assert args.command == "set-reader-power"
        assert args.ip == "192.168.1.1"
        assert args.port == 6000
        assert args.power == 20
        assert args.adr == 0

    def test_set_reader_power_requires_power(self) -> None:
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["set-reader-power", "192.168.1.1", "6000"])  # missing power

    def test_set_reader_scantime_args(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["set-reader-scantime", "192.168.1.1", "6000", "20"])
        assert args.command == "set-reader-scantime"
        assert args.ip == "192.168.1.1"
        assert args.port == 6000
        assert args.scan_time == 20
        assert args.adr == 0

    def test_set_reader_scantime_requires_value(self) -> None:
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["set-reader-scantime", "192.168.1.1", "6000"])  # missing scan_time


class TestVersionFlag:
    def test_version_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        main(["--version"])
        captured = capsys.readouterr()
        from hw_vx_config import __version__

        assert "hw-vx-config" in captured.out
        assert __version__ in captured.out


class TestSearchCommand:
    def test_search_calls_search_readers(self) -> None:
        with patch("hw_vx_config.cli.search_readers", return_value=[]) as mock_search:
            main(["search", "--network", "10.10.0.0/24"])
            mock_search.assert_called_once_with("10.10.0.0/24")
