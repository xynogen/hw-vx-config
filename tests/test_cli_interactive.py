"""Tests for the interactive CLI refactor — SessionState, helpers, and command dispatch."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from hw_vx_config.cli import (
    COMMANDS,
    SessionState,
    _require_config,
    _require_connection,
    _with_device,
    interactive_menu,
    search_readers,
)
from hw_vx_config.models import DeviceConfig, SearchResult

# ─── SessionState ────────────────────────────────────────────────────


class TestSessionState:
    def test_defaults(self) -> None:
        s = SessionState()
        assert s.ip is None
        assert s.mac is None
        assert s.config is None
        assert s.reader_adr == 0

    def test_connected_false_by_default(self) -> None:
        assert not SessionState().connected

    def test_connected_true_when_ip_set(self) -> None:
        s = SessionState(ip="192.168.1.1")
        assert s.connected

    def test_update_from_config(self) -> None:
        s = SessionState(ip="10.0.0.1", mac="old")
        cfg = DeviceConfig(mac_address="AA:BB:CC:DD:EE:FF", ip_address="10.0.0.1")
        s.update_from_config(cfg)
        assert s.config is cfg
        assert s.mac == "AA:BB:CC:DD:EE:FF"

    def test_update_from_config_keeps_mac_if_empty(self) -> None:
        s = SessionState(ip="10.0.0.1", mac="old")
        cfg = DeviceConfig(mac_address="", ip_address="10.0.0.1")
        s.update_from_config(cfg)
        assert s.mac == "old"


# ─── _require_connection / _require_config ───────────────────────────


class TestRequireConnection:
    def test_returns_false_when_no_ip(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert not _require_connection(SessionState())
        assert "No reader selected" in capsys.readouterr().out

    def test_returns_true_when_connected(self) -> None:
        assert _require_connection(SessionState(ip="1.2.3.4"))


class TestRequireConfig:
    def test_false_when_no_ip(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert not _require_config(SessionState())

    def test_false_when_no_config(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert not _require_config(SessionState(ip="1.2.3.4"))
        assert "No config loaded" in capsys.readouterr().out

    def test_true_when_both(self) -> None:
        s = SessionState(ip="1.2.3.4", config=DeviceConfig())
        assert _require_config(s)


# ─── _with_device ────────────────────────────────────────────────────


class TestWithDevice:
    def test_timeout_prints_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("hw_vx_config.cli.HwVxDevice") as mock:
            mock.return_value.__enter__ = MagicMock(return_value=mock.return_value)
            mock.return_value.__exit__ = MagicMock(return_value=False)
            mock.return_value.connect.side_effect = TimeoutError("timeout")
            result = _with_device("1.2.3.4", lambda d, c: None)
        assert result is None
        assert "not responding" in capsys.readouterr().out

    def test_connection_error_prints_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("hw_vx_config.cli.HwVxDevice") as mock:
            mock.return_value.__enter__ = MagicMock(return_value=mock.return_value)
            mock.return_value.__exit__ = MagicMock(return_value=False)
            mock.return_value.connect.side_effect = ConnectionError("refused")
            result = _with_device("1.2.3.4", lambda d, c: None)
        assert result is None
        assert "Connection failed" in capsys.readouterr().out

    def test_value_error_prints_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("hw_vx_config.cli.HwVxDevice") as mock:
            mock.return_value.__enter__ = MagicMock(return_value=mock.return_value)
            mock.return_value.__exit__ = MagicMock(return_value=False)
            mock.return_value.connect.side_effect = ValueError("bad data")
            result = _with_device("1.2.3.4", lambda d, c: None)
        assert result is None
        assert "Bad response" in capsys.readouterr().out

    def test_success_returns_callback_result(self) -> None:
        with patch("hw_vx_config.cli.HwVxDevice") as mock:
            dev = mock.return_value.__enter__.return_value
            dev.connect.return_value = None
            dev.get_config.return_value = DeviceConfig()
            mock.return_value.__enter__ = MagicMock(return_value=dev)
            mock.return_value.__exit__ = MagicMock(return_value=False)
            result = _with_device("1.2.3.4", lambda d, c: "ok")
        assert result == "ok"


# ─── Command dispatch table ─────────────────────────────────────────


class TestCommandDispatch:
    def test_all_menu_options_registered(self) -> None:
        """Every menu option 1-10 must have a handler."""
        for i in range(1, 11):
            assert str(i) in COMMANDS, f"Option {i} missing from COMMANDS"

    def test_handlers_are_callable(self) -> None:
        for key, handler in COMMANDS.items():
            assert callable(handler), f"COMMANDS[{key!r}] is not callable"


# ─── search_readers ─────────────────────────────────────────────────


class TestSearchReaders:
    def test_no_results(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("hw_vx_config.cli.HwVxNetworking") as mock_net:
            net = mock_net.return_value.__enter__.return_value
            net.search.return_value = []
            results = search_readers()
        assert results == []
        assert "No readers found" in capsys.readouterr().out

    def test_results_shown_in_box(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("hw_vx_config.cli.HwVxNetworking") as mock_net:
            net = mock_net.return_value.__enter__.return_value
            net.search.return_value = [
                SearchResult(
                    ip_address="192.168.1.100",
                    mac_address="0.34.112.0.167.227",
                    port_number="4196",
                    device_name="HW-VX6330K",
                )
            ]
            results = search_readers()
        assert len(results) == 1
        out = capsys.readouterr().out
        # Results should be in a Box (consistent styling)
        assert "╔" in out
        assert "╚" in out
        assert "192.168.1.100" in out

    def test_timeout_handled(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("hw_vx_config.cli.HwVxNetworking") as mock_net:
            mock_net.return_value.__enter__.return_value.search.side_effect = TimeoutError()
            results = search_readers()
        assert results == []
        assert "timed out" in capsys.readouterr().out


# ─── interactive_menu Ctrl+C handling ────────────────────────────────


class TestInteractiveMenu:
    def test_ctrl_c_exits_gracefully(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Ctrl+C during the menu should print 'Bye!' without traceback."""
        with patch("builtins.input", side_effect=KeyboardInterrupt):
            interactive_menu()
        assert "Bye!" in capsys.readouterr().out

    def test_quit_exits(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("builtins.input", return_value="q"):
            interactive_menu()
        assert "Bye!" in capsys.readouterr().out

    def test_unknown_option_no_crash(self) -> None:
        """Typing garbage should not crash the menu."""
        responses = iter(["xyz", "q"])
        with patch("builtins.input", side_effect=lambda _: next(responses)):
            interactive_menu()  # should not raise
