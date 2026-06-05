"""
Protocol constants and option look-up tables.

All values are extracted from the original C# Demo v2.11
(Networking.cs + Form1.cs).
"""

# ─── Protocol Constants ──────────────────────────────────────────────

UDP_PORT: int = 65535
RECV_TIMEOUT: float = 1.0  # seconds
RECV_BUFFER: int = 1024

# ─── Setting Codes ───────────────────────────────────────────────────
#
# Command flow sequences (from C# Form1.cs):
#   Search:  X (broadcast) → parse "A{mac}/{port}" replies
#   Select:  W{mac}
#   Login:   L
#   Logout:  O
#   Reboot:  E
#   Get:     G{setting_code}
#   Set:     S{setting_code}{value}

SETTINGS: dict[str, str] = {
    # Network settings
    "ON": "Username",
    "DN": "Device Name",
    "FE": "MAC Address",
    "IP": "IP Address",
    "PN": "Port Number",
    "TP": "Protocol",  # 0=UDP, 1=TCP
    "RM": "Work Mode",  # 0=Server, 1=Client
    "DI": "Remote IP",
    "DP": "Remote Port",
    "GI": "Gateway IP",
    "NM": "Subnet Mask",
    "DH": "DHCP",  # 0=Disabled, 1=Enabled
    # Serial settings
    "BR": "Baud Rate",  # 0=1200 … 7=115200
    "PR": "Parity",  # 0=None … 4=Space
    "BB": "Data Bits",  # 0=7bits, 1=8bits
    "DT": "DTR Mode",  # 0=Disabled, 1=Enabled
    "FC": "RTS",  # 0=Disabled, 1=Enabled
    # Advanced settings
    "CM": "Connection Mode",  # 0=Immediately, 1=Connect-with-data
    "CT": "Connection Timeout",
    "RC": "Reconnect",
    "ML": "Max Length",
    "MD": "Max Delay",
}

# ─── Human-Readable Option Maps ─────────────────────────────────────

PROTOCOL_OPTIONS: dict[int, str] = {0: "UDP", 1: "TCP"}
WORK_MODE_OPTIONS: dict[int, str] = {0: "Server", 1: "Client"}
DHCP_OPTIONS: dict[int, str] = {0: "Disabled", 1: "Enabled"}

BAUD_RATE_OPTIONS: dict[int, str] = {
    0: "1200",
    1: "2400",
    2: "4800",
    3: "9600",
    4: "19200",
    5: "38400",
    6: "57600",
    7: "115200",
}

PARITY_OPTIONS: dict[int, str] = {
    0: "None",
    1: "Even",
    2: "Odd",
    3: "Mark",
    4: "Space",
}

DATA_BITS_OPTIONS: dict[int, str] = {0: "7 bits", 1: "8 bits"}
TOGGLE_OPTIONS: dict[int, str] = {0: "Disabled", 1: "Enabled"}
