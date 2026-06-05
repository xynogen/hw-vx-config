"""
HW-VX6330K / HW-VX6346KL Network Configuration Tool for Linux.

Ported from the C# Demo v2.11 (Networking.cs + Form1.cs).
Protocol: UDP packets to port 65535 (HW-VX IP Protocol).

No DLLs needed — pure Python sockets.
"""

__version__ = "1.0.0"

from hw_vx_config.device import HwVxDevice
from hw_vx_config.models import DeviceConfig, SearchResult
from hw_vx_config.transport import HwVxNetworking

__all__ = [
    "DeviceConfig",
    "HwVxDevice",
    "HwVxNetworking",
    "SearchResult",
]
