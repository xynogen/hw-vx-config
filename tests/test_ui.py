"""Tests for hw_vx_config.ui — output helpers and typed prompts."""

from __future__ import annotations

import errno
import os
import pty
import select
import subprocess
import sys
import time
from ipaddress import IPv4Address
from pathlib import Path

import pytest
from uhfreader18.hwvx import NetProtocol

from hw_vx_config import ui


def test_arrow_keys_edit_interactive_input() -> None:
    master, slave = pty.openpty()
    env = os.environ | {"PYTHONPATH": str(Path(__file__).parents[1] / "src")}
    proc = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import hw_vx_config.ui; print('RESULT=' + input('> '))",
        ],
        stdin=slave,
        stdout=slave,
        stderr=slave,
        env=env,
    )
    os.close(slave)
    os.write(master, b"ac\x1b[Db\n")

    output = b""
    deadline = time.monotonic() + 3
    while proc.poll() is None and time.monotonic() < deadline:
        ready, _, _ = select.select([master], [], [], 0.1)
        if ready:
            try:
                output += os.read(master, 4096)
            except OSError as exc:
                if exc.errno != errno.EIO:
                    raise
                break

    proc.wait(timeout=1)
    os.close(master)
    assert b"RESULT=abc" in output


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


# ─── typed prompts ───────────────────────────────────────────────────


class TestAskIp:
    def test_empty_keeps_current(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("builtins.input", lambda _: "")
        assert ui.ask_ip("IP", IPv4Address("192.168.1.1")) == IPv4Address("192.168.1.1")

    def test_new_value_returned(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("builtins.input", lambda _: "10.0.0.1")
        assert ui.ask_ip("IP", IPv4Address("192.168.1.1")) == IPv4Address("10.0.0.1")

    def test_rejects_invalid_then_accepts(self, monkeypatch: pytest.MonkeyPatch) -> None:
        responses = iter(["256.0.0.1", "10.0.0.1"])
        monkeypatch.setattr("builtins.input", lambda _: next(responses))
        assert ui.ask_ip("IP", IPv4Address("1.2.3.4")) == IPv4Address("10.0.0.1")


class TestAskPort:
    def test_empty_keeps_current(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("builtins.input", lambda _: "")
        assert ui.ask_port("Port", 4196) == 4196

    def test_new_value(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("builtins.input", lambda _: "8080")
        assert ui.ask_port("Port", 80) == 8080

    def test_rejects_out_of_range_then_accepts(self, monkeypatch: pytest.MonkeyPatch) -> None:
        responses = iter(["0", "65536", "443"])
        monkeypatch.setattr("builtins.input", lambda _: next(responses))
        assert ui.ask_port("Port", 80) == 443


class TestAskEnum:
    def test_empty_keeps_current(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("builtins.input", lambda _: "")
        assert ui.ask_enum("Protocol", NetProtocol.UDP, NetProtocol) is NetProtocol.UDP

    def test_selects_by_value(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("builtins.input", lambda _: "1")
        assert ui.ask_enum("Protocol", NetProtocol.UDP, NetProtocol) is NetProtocol.TCP

    def test_rejects_invalid_then_accepts(self, monkeypatch: pytest.MonkeyPatch) -> None:
        responses = iter(["9", "1"])
        monkeypatch.setattr("builtins.input", lambda _: next(responses))
        assert ui.ask_enum("Protocol", NetProtocol.UDP, NetProtocol) is NetProtocol.TCP


class TestAskText:
    def test_empty_keeps_current(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("builtins.input", lambda _: "")
        assert ui.ask_text("Name", "admin") == "admin"

    def test_new_value(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("builtins.input", lambda _: "root")
        assert ui.ask_text("Name", "admin") == "root"
