"""
Terminal UI helpers — all output indentation and icons live here.
cli.py calls these; never hardcodes spacing or prefixes directly.
"""

from __future__ import annotations

import readline  # noqa: F401 -- prevents arrow keys appearing as escape text in input()
from enum import IntEnum
from ipaddress import AddressValueError, IPv4Address
from typing import TypeVar

_I = "  "  # base indent

E = TypeVar("E", bound=IntEnum)


# ─── Output helpers ──────────────────────────────────────────────────


def ok(msg: str) -> None:
    print(f"{_I}✅ {msg}")


def warn(msg: str) -> None:
    print(f"{_I}⚠  {msg}")


def err(msg: str) -> None:
    print(f"{_I}❌ {msg}")


def info(msg: str) -> None:
    print(f"{_I}{msg}")


def hint(msg: str) -> None:
    """Subtle guidance — visually distinct from info()."""
    print(f"{_I}💡 {msg}")


def section(title: str) -> None:
    print(f"{_I}── {title} ──")


def kv(label: str, value: object) -> None:
    print(f"{_I}{label:<20}: {value}")


# ─── Input helpers ───────────────────────────────────────────────────


def text(prompt: str) -> str:
    """Read editable text; readline handles arrows and other editing keys."""
    return input(prompt).strip()


def confirm(prompt: str) -> bool:
    """Ask a yes/no question. Returns True on 'y'."""
    return text(f"{_I}{prompt} (y/n): ").lower() == "y"


# ─── Typed prompts ───────────────────────────────────────────────────
#
# The library models config fields as real types (IPv4Address, int, IntEnum).
# These prompts read a string, keep the current value on empty input, and
# return the parsed type — the constructor is the validator, so there is no
# hand-rolled is_valid_* to keep in sync with stdlib parsing rules.


def ask_ip(label: str, current: IPv4Address) -> IPv4Address:
    """Prompt for an IPv4 address; empty keeps *current*."""
    while True:
        val = text(f"    {label} [{current}]: ")
        if not val:
            return current
        try:
            return IPv4Address(val)
        except AddressValueError:
            warn("Invalid IP address (e.g. 192.168.1.100).")


def ask_port(label: str, current: int) -> int:
    """Prompt for a TCP/UDP port (1-65535); empty keeps *current*."""
    while True:
        val = text(f"    {label} [{current}]: ")
        if not val:
            return current
        try:
            n = int(val)
        except ValueError:
            warn("Port must be a number.")
            continue
        if 1 <= n <= 65535:
            return n
        warn("Port must be 1-65535.")


def ask_enum(label: str, current: E, cls: type[E]) -> E:
    """Prompt for an enum member by numeric value; empty keeps *current*."""
    hint_str = ", ".join(f"{m.value}={m.name}" for m in cls)
    while True:
        val = text(f"    {label} [{current.name}] ({hint_str}): ")
        if not val:
            return current
        try:
            return cls(int(val))
        except ValueError:
            warn(f"Must be one of: {', '.join(str(m.value) for m in cls)}")


def ask_text(label: str, current: str) -> str:
    """Prompt for free text; empty keeps *current*."""
    return text(f"    {label} [{current}]: ") or current
