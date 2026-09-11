"""
HW-VX6330K / HW-VX6346KL Network Configuration Tool for Linux.

Ported from the C# Demo v2.11 (Networking.cs + Form1.cs).
Protocol: UDP packets to port 65535 (HW-VX IP Protocol).

No DLLs needed — pure Python sockets.
"""

__version__ = "2.1.1"

from uhfreader18.hwvx import DeviceConfig, HwVxDevice, HwVxNetworking, SearchResult

__all__ = [
    "DeviceConfig",
    "HwVxDevice",
    "HwVxNetworking",
    "SearchResult",
]
