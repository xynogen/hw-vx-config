"""Tests for hw_vx_config.ui — output helpers, validators, and ask()."""

from __future__ import annotations

import pytest

from hw_vx_config import ui

# ─── Output helpers ──────────────────────────────────────────────────


class TestOutputHelpers:
    """All output functions print with the standard indent prefix."""

    def test_ok(self, capsys: pytest.CaptureFixture[str]) -> None:
        ui.ok("done")
        assert capsys.readouterr().out == "  ✅ done\n"

    def test_warn(self, capsys: pytest.CaptureFixture[str]) -> None:
        ui.warn("careful")
        assert capsys.readouterr().out == "  ⚠  careful\n"

    def test_err(self, capsys: pytest.CaptureFixture[str]) -> None:
        ui.err("bad")
        assert capsys.readouterr().out == "  ❌ bad\n"

    def test_info(self, capsys: pytest.CaptureFixture[str]) -> None:
        ui.info("hello")
        assert capsys.readouterr().out == "  hello\n"

    def test_hint_has_icon(self, capsys: pytest.CaptureFixture[str]) -> None:
        ui.hint("try this")
        out = capsys.readouterr().out
        assert "💡" in out
        assert "try this" in out

    def test_hint_differs_from_info(self, capsys: pytest.CaptureFixture[str]) -> None:
        """hint() and info() must produce different output."""
        ui.info("msg")
        info_out = capsys.readouterr().out
        ui.hint("msg")
        hint_out = capsys.readouterr().out
        assert info_out != hint_out

    def test_section(self, capsys: pytest.CaptureFixture[str]) -> None:
        ui.section("Title")
        assert capsys.readouterr().out == "  ── Title ──\n"

    def test_kv(self, capsys: pytest.CaptureFixture[str]) -> None:
        ui.kv("Label", "Value")
        out = capsys.readouterr().out
        assert "Label" in out
        assert "Value" in out
        assert ":" in out


# ─── Validators ──────────────────────────────────────────────────────


class TestIsValidIp:
    def test_valid(self) -> None:
        assert ui.is_valid_ip("192.168.1.1")
        assert ui.is_valid_ip("0.0.0.0")
        assert ui.is_valid_ip("255.255.255.255")
        assert ui.is_valid_ip("10.0.0.1")

    def test_invalid_octets(self) -> None:
        assert not ui.is_valid_ip("256.0.0.1")
        assert not ui.is_valid_ip("1.2.3.999")

    def test_too_few_parts(self) -> None:
        assert not ui.is_valid_ip("192.168.1")

    def test_too_many_parts(self) -> None:
        assert not ui.is_valid_ip("1.2.3.4.5")

    def test_non_numeric(self) -> None:
        assert not ui.is_valid_ip("abc.def.ghi.jkl")

    def test_empty(self) -> None:
        assert not ui.is_valid_ip("")

    def test_spaces(self) -> None:
        assert not ui.is_valid_ip(" 192.168.1.1")

    def test_negative_octet(self) -> None:
        assert not ui.is_valid_ip("-1.0.0.0")


class TestIsValidPort:
    def test_valid_range(self) -> None:
        assert ui.is_valid_port("1")
        assert ui.is_valid_port("80")
        assert ui.is_valid_port("8080")
        assert ui.is_valid_port("65535")

    def test_zero(self) -> None:
        assert not ui.is_valid_port("0")

    def test_too_high(self) -> None:
        assert not ui.is_valid_port("65536")
        assert not ui.is_valid_port("99999")

    def test_non_numeric(self) -> None:
        assert not ui.is_valid_port("abc")
        assert not ui.is_valid_port("")

    def test_negative(self) -> None:
        assert not ui.is_valid_port("-1")


class TestIsValidOption:
    def test_valid_key(self) -> None:
        opts = {0: "UDP", 1: "TCP"}
        checker = ui.is_valid_option(opts)
        assert checker("0")
        assert checker("1")

    def test_invalid_key(self) -> None:
        opts = {0: "UDP", 1: "TCP"}
        checker = ui.is_valid_option(opts)
        assert not checker("2")
        assert not checker("9")

    def test_non_numeric(self) -> None:
        opts = {0: "UDP"}
        checker = ui.is_valid_option(opts)
        assert not checker("abc")
        assert not checker("")


# ─── confirm() ───────────────────────────────────────────────────────


class TestConfirm:
    def test_yes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("builtins.input", lambda _: "y")
        assert ui.confirm("Do it?")

    def test_yes_uppercase(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("builtins.input", lambda _: "Y")
        assert ui.confirm("Do it?")

    def test_no(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("builtins.input", lambda _: "n")
        assert not ui.confirm("Do it?")

    def test_empty_is_no(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("builtins.input", lambda _: "")
        assert not ui.confirm("Do it?")

    def test_garbage_is_no(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("builtins.input", lambda _: "maybe")
        assert not ui.confirm("Do it?")


# ─── ask() ───────────────────────────────────────────────────────────


class TestAsk:
    def test_empty_keeps_current(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("builtins.input", lambda _: "")
        assert ui.ask("IP", "192.168.1.1") == "192.168.1.1"

    def test_new_value_returned(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("builtins.input", lambda _: "10.0.0.1")
        assert ui.ask("IP", "192.168.1.1") == "10.0.0.1"

    def test_with_options_valid(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("builtins.input", lambda _: "1")
        assert ui.ask("Protocol", "0", {0: "UDP", 1: "TCP"}) == "1"

    def test_with_options_empty_keeps_current(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("builtins.input", lambda _: "")
        assert ui.ask("Protocol", "0", {0: "UDP", 1: "TCP"}) == "0"

    def test_with_options_rejects_invalid_then_accepts(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Invalid option causes re-prompt, then valid input is accepted."""
        responses = iter(["9", "1"])
        monkeypatch.setattr("builtins.input", lambda _: next(responses))
        assert ui.ask("Protocol", "0", {0: "UDP", 1: "TCP"}) == "1"

    def test_custom_validator_rejects_then_accepts(self, monkeypatch: pytest.MonkeyPatch) -> None:
        responses = iter(["banana", "10.0.0.1"])
        monkeypatch.setattr("builtins.input", lambda _: next(responses))
        result = ui.ask("IP", "1.2.3.4", validator=ui.is_valid_ip, error_msg="Bad IP")
        assert result == "10.0.0.1"

    def test_validator_overrides_option_check(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When both options and validator are given, validator takes precedence."""
        # validator always returns True, so even "99" passes
        monkeypatch.setattr("builtins.input", lambda _: "99")
        result = ui.ask("X", "0", {0: "A", 1: "B"}, validator=lambda _: True)
        assert result == "99"
