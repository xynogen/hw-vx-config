"""
Terminal UI helpers — all output indentation and icons live here.
cli.py calls these; never hardcodes spacing or prefixes directly.
"""

from __future__ import annotations

_I = "  "  # base indent


def ok(msg: str) -> None:
    print(f"{_I}✅ {msg}")


def warn(msg: str) -> None:
    print(f"{_I}⚠  {msg}")


def err(msg: str) -> None:
    print(f"{_I}❌ {msg}")


def info(msg: str) -> None:
    print(f"{_I}{msg}")


def hint(msg: str) -> None:
    print(f"{_I}{msg}")


def section(title: str) -> None:
    print(f"{_I}── {title} ──")


def kv(label: str, value: str) -> None:
    print(f"{_I}{label:<20}: {value}")
