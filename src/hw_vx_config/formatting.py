"""
Pretty-printing helpers for device configuration.
"""

from hw_vx_config.constants import (
    BAUD_RATE_OPTIONS,
    DATA_BITS_OPTIONS,
    DHCP_OPTIONS,
    PARITY_OPTIONS,
    PROTOCOL_OPTIONS,
    TOGGLE_OPTIONS,
    WORK_MODE_OPTIONS,
)
from hw_vx_config.models import DeviceConfig


def fmt_option(value: str, options: dict[int, str]) -> str:
    """Format an index *value* with its human-readable label."""
    try:
        idx = int(value)
        label = options.get(idx, "?")
        return f"{value} ({label})"
    except (ValueError, TypeError):
        return value


def format_config(cfg: DeviceConfig) -> str:
    """Return a pretty box-drawing representation of *cfg*."""
    lines: list[str] = [
        "",
        "  ╔══════════════════════════════════════════════════════╗",
        "  ║              NETWORK SETTINGS                       ║",
        "  ╠══════════════════════════════════════════════════════╣",
        f"  ║  IP Address      : {cfg.ip_address:<33}║",
        f"  ║  Subnet Mask     : {cfg.subnet_mask:<33}║",
        f"  ║  Gateway IP      : {cfg.gateway_ip:<33}║",
        f"  ║  MAC Address     : {cfg.mac_address:<33}║",
        f"  ║  Port            : {cfg.port_number:<33}║",
        f"  ║  Protocol        : {fmt_option(cfg.protocol, PROTOCOL_OPTIONS):<33}║",
        f"  ║  Work Mode       : {fmt_option(cfg.work_mode, WORK_MODE_OPTIONS):<33}║",
        f"  ║  DHCP            : {fmt_option(cfg.dhcp, DHCP_OPTIONS):<33}║",
        f"  ║  Remote IP       : {cfg.remote_ip:<33}║",
        f"  ║  Remote Port     : {cfg.remote_port:<33}║",
        f"  ║  Username        : {cfg.username:<33}║",
        f"  ║  Device Name     : {cfg.device_name:<33}║",
        "  ╠══════════════════════════════════════════════════════╣",
        "  ║              SERIAL SETTINGS                        ║",
        "  ╠══════════════════════════════════════════════════════╣",
        f"  ║  Baud Rate       : {fmt_option(cfg.baud_rate, BAUD_RATE_OPTIONS):<33}║",
        f"  ║  Parity          : {fmt_option(cfg.parity, PARITY_OPTIONS):<33}║",
        f"  ║  Data Bits       : {fmt_option(cfg.data_bits, DATA_BITS_OPTIONS):<33}║",
        f"  ║  DTR Mode        : {fmt_option(cfg.dtr_mode, TOGGLE_OPTIONS):<33}║",
        f"  ║  RTS             : {fmt_option(cfg.rts, TOGGLE_OPTIONS):<33}║",
        "  ╠══════════════════════════════════════════════════════╣",
        "  ║              ADVANCED SETTINGS                      ║",
        "  ╠══════════════════════════════════════════════════════╣",
        f"  ║  Connection Mode : {cfg.connection_mode:<33}║",
        f"  ║  Conn. Timeout   : {cfg.connection_timeout:<33}║",
        f"  ║  Reconnect       : {cfg.reconnect:<33}║",
        f"  ║  Max Length       : {cfg.max_length:<33}║",
        f"  ║  Max Delay        : {cfg.max_delay:<33}║",
        "  ╚══════════════════════════════════════════════════════╝",
        "",
    ]
    return "\n".join(lines)


def print_config(cfg: DeviceConfig) -> None:
    """Print a formatted device configuration to stdout."""
    print(format_config(cfg))
