"""Tests for the interactive CLI refactor — SessionState, helpers, and command dispatch."""

from __future__ import annotations

from collections.abc import Callable
from unittest.mock import MagicMock, patch

import pytest

from hw_vx_config.cli import (
    COMMANDS,
    SessionState,
    _cmd_change_ip,
    _cmd_dhcp,
    _cmd_edit_full,
    _cmd_reboot,
    _cmd_remote_server,
    _cmd_search,
    _cmd_show_config,
    _require_config,
    _require_connection,
    _run_menu,
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
        assert not s.broadcast
        assert s.broadcast_ip == "255.255.255.255"

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


class TestSearchCommand:
    def test_l2_mode_does_not_ask_for_cidr(self) -> None:
        state = SessionState()
        with (
            patch("hw_vx_config.cli.ui.text", return_value="1") as text,
            patch("hw_vx_config.cli.search_readers", return_value=[]) as search,
        ):
            _cmd_search(state)

        text.assert_called_once_with("  Discovery mode: ")
        search.assert_called_once_with(None)

    def test_discovery_submenu_is_boxed(self, capsys: pytest.CaptureFixture[str]) -> None:
        with (
            patch("hw_vx_config.cli.ui.text", return_value="1"),
            patch("hw_vx_config.cli.search_readers", return_value=[]),
        ):
            _cmd_search(SessionState())

        out = capsys.readouterr().out
        assert "DISCOVERY MODE" in out
        assert "╔" in out and "╚" in out

    def test_cidr_mode_asks_for_network(self) -> None:
        state = SessionState()
        with (
            patch("hw_vx_config.cli.ui.text", side_effect=["2", "172.27.43.64/28"]),
            patch("hw_vx_config.cli.search_readers", return_value=[]) as search,
        ):
            _cmd_search(state)

        search.assert_called_once_with("172.27.43.64/28")

    @pytest.mark.parametrize(("choice", "broadcast"), [("1", False), ("2", True)])
    def test_scans_once_and_uses_selected_mode(self, choice: str, broadcast: bool) -> None:
        result = SearchResult(
            ip_address="192.168.1.100",
            mac_address="AA:BB:CC:DD:EE:FF",
        )
        state = SessionState()

        with (
            patch("hw_vx_config.cli.search_readers", return_value=[result]) as search,
            patch("hw_vx_config.cli._with_device") as with_device,
            patch("builtins.input", side_effect=["2", "10.10.0.0/24", choice]),
        ):
            _cmd_search(state)

        search.assert_called_once_with("10.10.0.0/24")
        with_device.assert_called_once()
        assert with_device.call_args.args[0] == result.ip_address
        assert with_device.call_args.kwargs == {
            "mac_address": result.mac_address,
            "broadcast": broadcast,
            "broadcast_ip": "10.10.0.255",
        }
        assert state.broadcast is broadcast
        assert state.broadcast_ip == "10.10.0.255"

    def test_configuration_submenu_is_boxed(self, capsys: pytest.CaptureFixture[str]) -> None:
        result = SearchResult(ip_address="192.168.1.100", mac_address="AA:BB:CC:DD:EE:FF")
        with (
            patch("hw_vx_config.cli.search_readers", return_value=[result]),
            patch("hw_vx_config.cli._with_device"),
            patch("builtins.input", side_effect=["1", "1"]),
        ):
            _cmd_search(SessionState())

        out = capsys.readouterr().out
        assert "CONFIGURATION MODE" in out
        assert out.count("╔") >= 2


class TestRuntimeMode:
    @pytest.mark.parametrize(
        "handler",
        [_cmd_show_config, _cmd_change_ip, _cmd_remote_server, _cmd_edit_full],
    )
    def test_config_operations_keep_broadcast_mode(
        self, handler: Callable[[SessionState], None]
    ) -> None:
        state = SessionState(
            ip="192.168.1.100",
            mac="AA:BB:CC:DD:EE:FF",
            broadcast=True,
            broadcast_ip="10.10.0.255",
        )
        with patch("hw_vx_config.cli._with_device") as with_device:
            handler(state)

        assert with_device.call_args.kwargs == {
            "mac_address": state.mac,
            "broadcast": True,
            "broadcast_ip": "10.10.0.255",
        }

    @pytest.mark.parametrize(
        ("handler", "inputs"),
        [
            (_cmd_dhcp, ["1"]),
            (_cmd_reboot, []),
        ],
    )
    def test_direct_operations_keep_broadcast_mode(
        self,
        handler: Callable[[SessionState], None],
        inputs: list[str],
    ) -> None:
        state = SessionState(
            ip="192.168.1.100",
            mac="AA:BB:CC:DD:EE:FF",
            broadcast=True,
            broadcast_ip="10.10.0.255",
        )
        with (
            patch("builtins.input", side_effect=inputs),
            patch("hw_vx_config.cli.ui.confirm", return_value=True),
            patch("hw_vx_config.cli.HwVxDevice") as device,
        ):
            device.return_value.__enter__.return_value = device.return_value
            handler(state)

        device.assert_called_once_with(
            state.ip,
            mac_address=state.mac,
            broadcast=True,
            broadcast_ip="10.10.0.255",
        )


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

    def test_empty_target_reports_l2_broadcast(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("hw_vx_config.cli.HwVxNetworking") as mock_net:
            mock_net.return_value.__enter__.return_value.search.return_value = []
            search_readers()

        assert "L2 broadcast (255.255.255.255)" in capsys.readouterr().out

    def test_sweeps_each_usable_ip_in_cidr(self) -> None:
        with patch("hw_vx_config.cli.HwVxNetworking") as mock_net:
            net = mock_net.return_value.__enter__.return_value
            net.search_targets.return_value = []
            search_readers("172.27.43.64/28")

        mock_net.assert_called_once_with("255.255.255.255")
        net.search_targets.assert_called_once_with([f"172.27.43.{host}" for host in range(65, 79)])

    def test_cidr_reports_range(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("hw_vx_config.cli.HwVxNetworking") as mock_net:
            mock_net.return_value.__enter__.return_value.search_targets.return_value = []
            search_readers("172.27.43.64/28")

        out = capsys.readouterr().out
        assert "172.27.43.64/28" in out
        assert "14 hosts: 172.27.43.65 - 172.27.43.78" in out

    def test_prefixless_network_sweeps_24(self) -> None:
        with patch("hw_vx_config.cli.HwVxNetworking") as mock_net:
            net = mock_net.return_value.__enter__.return_value
            net.search_targets.return_value = []
            search_readers("10.10.23.0")

        targets = net.search_targets.call_args.args[0]
        assert targets[0] == "10.10.23.1"
        assert targets[-1] == "10.10.23.254"
        assert len(targets) == 254

    def test_rejects_invalid_cidr(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("hw_vx_config.cli.HwVxNetworking") as mock_net:
            assert search_readers("not-a-network") == []

        mock_net.assert_not_called()
        assert "Invalid network" in capsys.readouterr().out

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
    def test_l_lists_only_discovery_options_when_disconnected(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("builtins.input", side_effect=["l", "q"]):
            _run_menu(SessionState())

        out = capsys.readouterr().out
        assert "1. Search for readers" in out
        assert "2. Connect to specific IP" in out
        assert "3. Show current configuration" not in out

    def test_l_hides_rfid_options_until_config_loaded(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("builtins.input", side_effect=["l", "q"]):
            _run_menu(SessionState(ip="10.10.23.241"))

        out = capsys.readouterr().out
        assert "8. Reboot reader" in out
        assert "9. RFID reader info" not in out

    def test_l_lists_all_options_when_config_loaded(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        state = SessionState(ip="10.10.23.241", config=DeviceConfig())
        with patch("builtins.input", side_effect=["l", "q"]):
            _run_menu(state)

        out = capsys.readouterr().out
        assert "9. RFID reader info" in out
        assert "10. Set RFID reader address" in out

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
