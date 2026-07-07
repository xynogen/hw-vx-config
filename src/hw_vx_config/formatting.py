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


def fmt_mac(raw: str) -> str:
    """Convert decimal-dot MAC (e.g. '0.34.112.0.167.227') to 'XX:XX:XX:XX:XX:XX'."""
    try:
        return ":".join(f"{int(b):02X}" for b in raw.split("."))
    except (ValueError, AttributeError):
        return raw


def fmt_option(value: str, options: dict[int, str]) -> str:
    """Format an index *value* with its human-readable label."""
    try:
        idx = int(value)
        label = options.get(idx, "?")
        return f"{value} ({label})"
    except (ValueError, TypeError):
        return value


class Box:
    """
    Builds a fixed-width box from a list of (label, value) rows.

    Geometry is derived automatically:
    - label_width = longest label
    - inner_width = indent(2) + label_width + " : " (3) + value_gutter(2) + max_value
      (clamped to at least 54 so short tables still look right)
    """

    _MIN_INNER = 54
    _INDENT = "  "  # left margin before ║

    def __init__(self) -> None:
        # Each entry: ("row", label, value) | ("div",) | ("hdr", title)
        self._entries: list[tuple] = []

    def hdr(self, title: str) -> "Box":
        self._entries.append(("hdr", title))
        return self

    def div(self) -> "Box":
        self._entries.append(("div",))
        return self

    def row(self, label: str, value: str) -> "Box":
        self._entries.append(("row", label, value))
        return self

    def item(self, text: str) -> "Box":
        """Full-width text line (no label/value split)."""
        self._entries.append(("item", text))
        return self

    def _geometry(self) -> tuple[int, int]:
        """Return (label_width, inner_width)."""
        labels = [e[1] for e in self._entries if e[0] == "row"]
        values = [e[2] for e in self._entries if e[0] == "row"]
        items = [e[1] for e in self._entries if e[0] in ("item", "hdr")]

        label_w = max((len(lbl) for lbl in labels), default=0)
        value_w = max((len(val) for val in values), default=0)
        item_w = max((len(txt) for txt in items), default=0)

        # row content: "  {label:<label_w} : {value}" → 2 + label_w + 3 + value_w
        row_content = 2 + label_w + 3 + value_w
        # item/hdr content: "  {text}" → 2 + item_w
        item_content = 2 + item_w

        # +1 for at least one trailing space before ║
        inner = max(self._MIN_INNER, row_content + 1, item_content + 1)
        return label_w, inner

    def render(self) -> str:
        label_w, inner = self._geometry()
        ind = self._INDENT
        border = "═" * inner

        def line_row(label: str, value: str) -> str:
            content = f"  {label:<{label_w}} : {value}"
            return f"{ind}║{content}{' ' * (inner - len(content))}║"

        def line_hdr(title: str) -> str:
            inner_text = f"  {title}  "
            return f"{ind}║{inner_text}{' ' * (inner - len(inner_text))}║"

        def line_item(text: str) -> str:
            content = f"  {text}"
            return f"{ind}║{content}{' ' * (inner - len(content))}║"

        out = [f"{ind}╔{border}╗"]
        for entry in self._entries:
            if entry[0] == "hdr":
                out.append(line_hdr(entry[1]))
            elif entry[0] == "div":
                out.append(f"{ind}╠{border}╣")
            elif entry[0] == "item":
                out.append(line_item(entry[1]))
            else:  # row
                out.append(line_row(entry[1], entry[2]))
        out.append(f"{ind}╚{border}╝")
        return "\n".join(out)


def format_config(cfg: DeviceConfig) -> str:
    """Return a pretty box-drawing representation of *cfg*."""
    box = (
        Box()
        .hdr("NETWORK SETTINGS")
        .div()
        .row("IP Address", cfg.ip_address)
        .row("Subnet Mask", cfg.subnet_mask)
        .row("Gateway IP", cfg.gateway_ip)
        .row("MAC Address", fmt_mac(cfg.mac_address))
        .row("Port", cfg.port_number)
        .row("Protocol", fmt_option(cfg.protocol, PROTOCOL_OPTIONS))
        .row("Work Mode", fmt_option(cfg.work_mode, WORK_MODE_OPTIONS))
        .row("DHCP", fmt_option(cfg.dhcp, DHCP_OPTIONS))
        .row("Remote IP", cfg.remote_ip)
        .row("Remote Port", cfg.remote_port)
        .row("Username", cfg.username)
        .row("Device Name", cfg.device_name)
        .div()
        .hdr("SERIAL SETTINGS")
        .div()
        .row("Baud Rate", fmt_option(cfg.baud_rate, BAUD_RATE_OPTIONS))
        .row("Parity", fmt_option(cfg.parity, PARITY_OPTIONS))
        .row("Data Bits", fmt_option(cfg.data_bits, DATA_BITS_OPTIONS))
        .row("DTR Mode", fmt_option(cfg.dtr_mode, TOGGLE_OPTIONS))
        .row("RTS", fmt_option(cfg.rts, TOGGLE_OPTIONS))
        .div()
        .hdr("ADVANCED SETTINGS")
        .div()
        .row("Connection Mode", cfg.connection_mode)
        .row("Conn. Timeout", cfg.connection_timeout)
        .row("Reconnect", cfg.reconnect)
        .row("Max Length", cfg.max_length)
        .row("Max Delay", cfg.max_delay)
    )
    return "\n" + box.render() + "\n"


def print_config(cfg: DeviceConfig) -> None:
    """Print a formatted device configuration to stdout."""
    print(format_config(cfg))
