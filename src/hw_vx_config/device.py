"""
High-level device operations.

Mirrors the C# ``Form1.cs`` button-click flows: search → select → login,
then get / set configuration.
"""

from __future__ import annotations

import time

from hw_vx_config.models import DeviceConfig, SearchResult
from hw_vx_config.transport import HwVxNetworking


class HwVxDevice:
    """
    High-level operations for a specific HW-VX reader.

    Parameters
    ----------
    ip_address : str
        The current IP address of the target device.
    """

    def __init__(self, ip_address: str) -> None:
        self.ip = ip_address
        self.net = HwVxNetworking(ip_address)
        self.mac: str = ""

    # ── connection ───────────────────────────────────────────────────

    def connect(self) -> SearchResult:
        """Search, select (``W{mac}``), and login (``L``) to a reader."""
        results = self.net.search()
        if not results:
            raise ConnectionError(f"No reader found at {self.ip}")
        r = results[0]
        self.mac = r.mac_address
        self.net.request(f"W{self.mac}", retries=3)
        self.net.request("L", retries=3)
        return r

    # ── read configuration ───────────────────────────────────────────

    def get_config(self) -> DeviceConfig:
        """Read all settings from the device (C# ``configButton_Click``)."""
        cfg = DeviceConfig()
        r = self.net.request_single
        cfg.username = r("GON", "1")
        cfg.device_name = r("GDN", "2")
        cfg.mac_address = r("GFE", "3")
        cfg.ip_address = r("GIP", "4")
        cfg.port_number = r("GPN", "5")
        cfg.protocol = r("GTP", "6")
        cfg.work_mode = r("GRM", "7")
        cfg.connection_mode = r("GCM", "8")
        cfg.connection_timeout = r("GCT", "9")
        cfg.rts = r("GFC", "10")
        cfg.dtr_mode = r("GDT", "11")
        cfg.baud_rate = r("GBR", "12")
        cfg.parity = r("GPR", "13")
        cfg.data_bits = r("GBB", "14")
        cfg.reconnect = r("GRC", "15")
        cfg.max_length = r("GML", "16")
        cfg.max_delay = r("GMD", "17")
        cfg.remote_ip = r("GDI", "18")
        cfg.remote_port = r("GDP", "19")
        cfg.gateway_ip = r("GGI", "20")
        cfg.subnet_mask = r("GNM", "21")
        cfg.dhcp = r("GDH", "22")
        return cfg

    # ── write configuration ──────────────────────────────────────────

    def save_config(self, cfg: DeviceConfig) -> None:
        """
        Write all settings and reboot.

        Sends commands via unicast first, then retries via broadcast
        with ``W{mac}`` in case the IP changed mid-save.
        """
        delay = 0.01  # 10 ms between commands, matching C#

        self._send_config_pass(self.net.send, cfg, delay, login=True)

        # Broadcast fallback
        with HwVxNetworking("255.255.255.255") as broadcast:
            broadcast.send(f"W{self.mac}")
            time.sleep(0.1)
            self._send_config_pass(broadcast.send, cfg, delay, login=True)

    @staticmethod
    def _send_config_pass(
        send,
        cfg: DeviceConfig,
        delay: float,
        *,
        login: bool = True,
    ) -> None:
        """Emit the full set-command sequence through *send*."""
        if login:
            send("L")
            time.sleep(0.05)

        commands = [
            f"SON{cfg.username}|18",
            f"SDN{cfg.device_name}|19",
            f"STP{cfg.protocol}|20",
            f"SPN{cfg.port_number}|21",
            f"SRM{cfg.work_mode}|22",
            f"SFC{cfg.rts}|23",
            f"SDT{cfg.dtr_mode}|24",
            f"SBR{cfg.baud_rate}|25",
            f"SPR{cfg.parity}|26",
            f"SBB{cfg.data_bits}|27",
            f"SRC{cfg.reconnect}|28",
            f"SCM{cfg.connection_mode}|29",
            f"SCT{cfg.connection_timeout}|30",
            f"SML{cfg.max_length}|31",
            f"SMD{cfg.max_delay}|32",
            f"SDI{cfg.remote_ip}|33",
            f"SDP{cfg.remote_port}|34",
            f"SGI{cfg.gateway_ip}|35",
            f"SNM{cfg.subnet_mask}|36",
            f"SIP{cfg.ip_address}|37",
        ]
        for cmd in commands:
            send(cmd)
            time.sleep(delay)

        send("E")
        time.sleep(0.5)

    # ── quick operations ─────────────────────────────────────────────

    def change_ip(self, new_ip: str) -> None:
        """Change IP address and reboot (C# ``changeIpButton_Click``)."""
        s = self.net.send

        # Unicast
        s("X")
        time.sleep(0.1)
        s("L")
        time.sleep(0.05)
        self.net.receive()  # drain reply
        s(f"SIP{new_ip}|34")
        time.sleep(0.1)
        self.net.receive()
        s("E|35")
        time.sleep(0.2)

        # Broadcast fallback
        with HwVxNetworking("255.255.255.255") as broadcast:
            broadcast.send(f"W{self.mac}")
            time.sleep(0.1)
            broadcast.send("L")
            time.sleep(0.05)
            broadcast.send(f"SIP{new_ip}|34")
            time.sleep(0.1)
            broadcast.receive()
            broadcast.send("E|35")

    def set_dhcp(self, enabled: bool) -> None:
        """Enable / disable DHCP and reboot."""
        val = "1" if enabled else "0"
        self.net.send("L")
        time.sleep(0.05)
        self.net.send(f"SDH{val}|40")
        time.sleep(0.1)
        self.net.send("E")

    def reboot(self) -> None:
        """Send a reboot command."""
        self.net.send("E")

    # ── lifecycle ────────────────────────────────────────────────────

    def close(self) -> None:
        """Close the underlying transport."""
        self.net.close()

    def __enter__(self) -> HwVxDevice:
        return self

    def __exit__(self, *exc) -> None:
        self.close()
