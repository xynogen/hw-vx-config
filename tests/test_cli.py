"""Tests for hw_vx_config.cli — argument parsing and version flag."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from hw_vx_config.cli import build_parser, main


class TestBuildParser:
    def test_subcommands_exist(self) -> None:
        parser = build_parser()
        # argparse stores sub-parsers; verify by parsing known commands
        args = parser.parse_args(["search"])
        assert args.command == "search"

    def test_config_requires_ip(self) -> None:
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["config"])  # missing required 'ip'

    def test_set_ip_args(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["set-ip", "192.168.1.1", "10.0.0.1"])
        assert args.ip == "192.168.1.1"
        assert args.new_ip == "10.0.0.1"

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


class TestVersionFlag:
    def test_version_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        main(["--version"])
        captured = capsys.readouterr()
        assert "hw-vx-config" in captured.out
        assert "1.0.0" in captured.out


class TestSearchCommand:
    def test_search_calls_search_readers(self) -> None:
        with patch("hw_vx_config.cli.search_readers", return_value=[]) as mock_search:
            main(["search"])
            mock_search.assert_called_once()
