"""
Data models for search results and device configuration.
"""

from dataclasses import dataclass


@dataclass
class SearchResult:
    """Represents a single device discovered during a broadcast search."""

    mac_address: str = ""
    port_number: str = ""
    ip_address: str = ""
    username: str = ""
    device_name: str = ""


@dataclass
class DeviceConfig:
    """All settings that can be read / written via the UDP protocol."""

    # Network
    username: str = ""
    device_name: str = ""
    mac_address: str = ""
    ip_address: str = ""
    port_number: str = ""
    protocol: str = ""  # index into PROTOCOL_OPTIONS
    work_mode: str = ""  # index into WORK_MODE_OPTIONS
    remote_ip: str = ""
    remote_port: str = ""
    gateway_ip: str = ""
    subnet_mask: str = ""
    dhcp: str = ""

    # Serial
    baud_rate: str = ""  # index into BAUD_RATE_OPTIONS
    parity: str = ""  # index into PARITY_OPTIONS
    data_bits: str = ""  # index into DATA_BITS_OPTIONS
    dtr_mode: str = ""  # index into TOGGLE_OPTIONS
    rts: str = ""  # index into TOGGLE_OPTIONS

    # Advanced
    connection_mode: str = ""
    connection_timeout: str = ""
    reconnect: str = ""
    max_length: str = ""
    max_delay: str = ""
