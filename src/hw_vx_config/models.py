"""
Data models for search results and device configuration.
"""

import ipaddress
from dataclasses import dataclass, fields

from hw_vx_config.constants import (
    BAUD_RATE_OPTIONS,
    DATA_BITS_OPTIONS,
    DHCP_OPTIONS,
    PARITY_OPTIONS,
    PROTOCOL_OPTIONS,
    TOGGLE_OPTIONS,
    WORK_MODE_OPTIONS,
)


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

    def validate(self) -> None:
        """
        Check every settable field before it is sent on the wire.

        Raises ``ValueError`` listing all problems.  Called by
        ``HwVxDevice.save_config`` so a bad config never reaches a
        device that would apply it and reboot.
        """
        errors: list[str] = []

        def check_ip(name: str, value: str) -> None:
            try:
                ipaddress.IPv4Address(value)
            except (ipaddress.AddressValueError, ValueError):
                errors.append(f"{name}: {value!r} is not a valid IPv4 address")

        def as_int(value: str) -> int | None:
            # isdigit() accepts unicode digits like '²' that int() rejects,
            # so parse defensively rather than trusting isdigit() alone.
            try:
                return int(value)
            except ValueError:
                return None

        def check_port(name: str, value: str) -> None:
            n = as_int(value)
            if n is None or not (1 <= n <= 65535):
                errors.append(f"{name}: {value!r} must be 1-65535")

        def check_option(name: str, value: str, options: dict[int, str]) -> None:
            n = as_int(value)
            if n is None or n not in options:
                errors.append(f"{name}: {value!r} not in {sorted(options)}")

        def check_uint(name: str, value: str) -> None:
            n = as_int(value)
            if n is None or n < 0:
                errors.append(f"{name}: {value!r} must be a non-negative integer")

        # `|` is the protocol delimiter and would corrupt the packet framing;
        # non-ASCII cannot be encoded by the transport.
        for f in fields(self):
            v = getattr(self, f.name)
            if "|" in v:
                errors.append(f"{f.name}: {v!r} must not contain '|'")
            if not v.isascii():
                errors.append(f"{f.name}: {v!r} must be ASCII")

        check_ip("ip_address", self.ip_address)
        check_ip("subnet_mask", self.subnet_mask)
        check_ip("gateway_ip", self.gateway_ip)
        check_ip("remote_ip", self.remote_ip)
        check_port("port_number", self.port_number)
        check_port("remote_port", self.remote_port)
        check_option("protocol", self.protocol, PROTOCOL_OPTIONS)
        check_option("work_mode", self.work_mode, WORK_MODE_OPTIONS)
        check_option("dhcp", self.dhcp, DHCP_OPTIONS)
        check_option("baud_rate", self.baud_rate, BAUD_RATE_OPTIONS)
        check_option("parity", self.parity, PARITY_OPTIONS)
        check_option("data_bits", self.data_bits, DATA_BITS_OPTIONS)
        check_option("dtr_mode", self.dtr_mode, TOGGLE_OPTIONS)
        check_option("rts", self.rts, TOGGLE_OPTIONS)
        check_option("connection_mode", self.connection_mode, TOGGLE_OPTIONS)
        check_uint("connection_timeout", self.connection_timeout)
        check_uint("reconnect", self.reconnect)
        check_uint("max_length", self.max_length)
        check_uint("max_delay", self.max_delay)

        if errors:
            raise ValueError("Invalid configuration:\n  " + "\n  ".join(errors))
