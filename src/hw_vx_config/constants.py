"""Human-readable option maps for the CLI.

Protocol semantics (setting codes, ports, enum values) live in
``uhfreader18.hwvx``. These maps only turn a setting's numeric value into
a label for display, derived from the library enums so nothing is
duplicated.
"""

from uhfreader18.hwvx import BaudRate, DataBits, NetProtocol, NetWorkMode, Parity, Toggle

PROTOCOL_OPTIONS: dict[int, str] = {p.value: p.name for p in NetProtocol}
WORK_MODE_OPTIONS: dict[int, str] = {m.value: m.name.capitalize() for m in NetWorkMode}
BAUD_RATE_OPTIONS: dict[int, str] = {b.value: str(b.bps) for b in BaudRate}
PARITY_OPTIONS: dict[int, str] = {p.value: p.name.capitalize() for p in Parity}
DATA_BITS_OPTIONS: dict[int, str] = {d.value: f"{d.count} bits" for d in DataBits}
DHCP_OPTIONS: dict[int, str] = {t.value: t.name.capitalize() for t in Toggle}
TOGGLE_OPTIONS: dict[int, str] = {t.value: t.name.capitalize() for t in Toggle}
