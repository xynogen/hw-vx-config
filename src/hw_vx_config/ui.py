"""
Terminal UI helpers — all output indentation and icons live here.
cli.py calls these; never hardcodes spacing or prefixes directly.
"""

from __future__ import annotations

from collections.abc import Callable

_I = "  "  # base indent


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


def kv(label: str, value: str) -> None:
    print(f"{_I}{label:<20}: {value}")


# ─── Input helpers ───────────────────────────────────────────────────


def confirm(prompt: str) -> bool:
    """Ask a yes/no question.  Returns True on 'y'."""
    return input(f"{_I}{prompt} (y/n): ").strip().lower() == "y"


# ─── Validators ──────────────────────────────────────────────────────


def is_valid_ip(value: str) -> bool:
    """Validate an IPv4 address string."""
    parts = value.split(".")
    if len(parts) != 4:
        return False
    for p in parts:
        # Reject whitespace, leading zeros abuse, empty octets
        if not p or not p.isdigit():
            return False
        try:
            n = int(p)
        except ValueError:
            return False
        if n < 0 or n > 255:
            return False
    return True


def is_valid_port(value: str) -> bool:
    """Validate a TCP/UDP port number string."""
    try:
        n = int(value)
    except ValueError:
        return False
    return 1 <= n <= 65535


def is_valid_option(options: dict[int, str]) -> Callable[[str], bool]:
    """Return a validator that checks *value* is a key in *options*."""

    def _check(value: str) -> bool:
        try:
            return int(value) in options
        except ValueError:
            return False

    return _check


# ─── Smart prompt ────────────────────────────────────────────────────


def ask(
    label: str,
    current: str,
    options: dict[int, str] | None = None,
    validator: Callable[[str], bool] | None = None,
    error_msg: str = "Invalid value.",
) -> str:
    """
    Prompt for a single field; empty input keeps current value.

    Parameters
    ----------
    label : str
        Field name shown in the prompt.
    current : str
        Current value (shown in brackets, returned on empty input).
    options : dict | None
        If given, shows option hints and validates against keys.
    validator : callable | None
        Extra validation function.  Overrides the built-in option check.
    error_msg : str
        Message shown when validation fails.
    """
    # Build the prompt string
    if options:
        hint_str = ", ".join(f"{k}={v}" for k, v in options.items())
        prompt = f"    {label} [{current}] ({hint_str}): "
    else:
        prompt = f"    {label} [{current}]: "

    # Determine effective validator
    if validator is None and options is not None:
        validator = is_valid_option(options)
        error_msg = f"Must be one of: {', '.join(str(k) for k in options)}"

    while True:
        val = input(prompt).strip()
        if not val:
            return current
        if validator and not validator(val):
            warn(error_msg)
            continue
        return val
