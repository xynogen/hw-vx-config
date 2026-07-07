"""
Command-line interface — both interactive (TUI menu) and scriptable sub-commands.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import dataclass

from hw_vx_config import ui
from hw_vx_config.constants import (
    BAUD_RATE_OPTIONS,
    DATA_BITS_OPTIONS,
    PARITY_OPTIONS,
    PROTOCOL_OPTIONS,
    TOGGLE_OPTIONS,
    WORK_MODE_OPTIONS,
)
from hw_vx_config.device import HwVxDevice
from hw_vx_config.formatting import Box, fmt_mac, fmt_option, print_config
from hw_vx_config.models import DeviceConfig, SearchResult
from hw_vx_config.rfid import RfidClient
from hw_vx_config.transport import HwVxNetworking

# ─── Banner ──────────────────────────────────────────────────────────

BANNER = (
    Box()
    .item("HW-VX6330K / HW-VX6346KL  Network Config Tool")
    .item("Linux Edition — ported from C# Demo v2.11")
    .render()
)

MENU = (
    Box()
    .item("1. Search for readers")
    .item("2. Connect to specific IP")
    .div()
    .item("3. Show current configuration")
    .item("4. Change IP address")
    .item("5. Enable/Disable DHCP")
    .item("6. Change remote server")
    .div()
    .item("7. Edit & save full configuration")
    .item("8. Reboot reader")
    .div()
    .item("9. RFID reader info")
    .item("10. Set RFID reader address")
    .div()
    .item("q. Quit   l. List menu")
)


# ─── Session state ───────────────────────────────────────────────────


@dataclass
class SessionState:
    """Holds all mutable state for the interactive menu session."""

    ip: str | None = None
    mac: str | None = None
    config: DeviceConfig | None = None
    reader_adr: int = 0

    @property
    def connected(self) -> bool:
        """True when a reader IP has been selected."""
        return self.ip is not None

    def update_from_config(self, cfg: DeviceConfig) -> None:
        """Sync state after reading a config from the device."""
        self.config = cfg
        self.mac = cfg.mac_address or self.mac


# ─── Device helper ───────────────────────────────────────────────────


def _with_device(
    ip: str,
    callback: Callable[[HwVxDevice, DeviceConfig], object],
) -> object:
    """
    Connect to *ip*, read config, run *callback(dev, cfg)*.

    Handles common exceptions with actionable messages.
    Returns whatever *callback* returns, or ``None`` on error.
    """
    try:
        with HwVxDevice(ip) as dev:
            dev.connect()
            cfg = dev.get_config()
            return callback(dev, cfg)
    except TimeoutError:
        ui.err("Reader not responding. Check IP and network cable.")
    except ConnectionError as exc:
        ui.err(f"Connection failed: {exc}")
    except ValueError as exc:
        ui.err(f"Bad response from device: {exc}")
    return None


def _require_connection(state: SessionState) -> bool:
    """Print a warning and return False if no reader is selected."""
    if not state.connected:
        ui.warn("No reader selected. Search first (option 1).")
        return False
    return True


def _require_config(state: SessionState) -> bool:
    """Return False (with warning) if no config has been loaded yet."""
    if not _require_connection(state):
        return False
    if state.config is None:
        ui.warn("No config loaded. Connect first (option 1 or 2).")
        return False
    return True


# ─── Search helpers ──────────────────────────────────────────────────


def search_readers() -> list[SearchResult]:
    """Broadcast search for all readers on the network."""
    ui.info("🔍 Searching for readers (broadcast)...")
    try:
        with HwVxNetworking("255.255.255.255") as net:
            results = net.search()
    except TimeoutError:
        ui.err("Search timed out. Check network connection.")
        return []
    except OSError as exc:
        ui.err(f"Network error: {exc}")
        return []

    if not results:
        ui.warn("No readers found. Check cable and network.")
        return []

    # Build results table using Box for consistent styling
    box = Box().hdr(f"FOUND {len(results)} READER(S)").div()
    for i, r in enumerate(results, 1):
        box.row(
            f"#{i}",
            f"{r.ip_address:<16} {fmt_mac(r.mac_address):<18} "
            f"port {r.port_number:<6} {r.device_name}",
        )
    print("\n" + box.render() + "\n")
    return results


def select_reader(results: list[SearchResult]) -> SearchResult | None:
    """Let user pick a reader from search results."""
    if len(results) == 1:
        return results[0]
    while True:
        choice = input("  Select reader # (or 'q' to cancel): ").strip()
        if choice.lower() == "q":
            return None
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(results):
                return results[idx]
        except ValueError:
            pass
        ui.warn("Invalid choice.")


# ─── Command handlers ────────────────────────────────────────────────
#
# Each handler receives the SessionState and returns None.
# They are responsible for their own input prompts and error handling.


def _cmd_search(state: SessionState) -> None:
    """1. Search for readers."""
    results = search_readers()
    if not results:
        return
    r = select_reader(results)
    if not r:
        return
    state.ip = r.ip_address
    state.mac = r.mac_address

    def _read(dev: HwVxDevice, cfg: DeviceConfig) -> DeviceConfig:
        state.update_from_config(cfg)
        return cfg

    _with_device(state.ip, _read)


def _cmd_connect(state: SessionState) -> None:
    """2. Connect to specific IP."""
    ip = input("  Enter reader IP address: ").strip()
    if not ip:
        return
    if not ui.is_valid_ip(ip):
        ui.warn("Invalid IP address format.")
        return
    state.ip = ip
    state.mac = ""

    def _read(_dev: HwVxDevice, cfg: DeviceConfig) -> DeviceConfig:
        state.update_from_config(cfg)
        return cfg

    _with_device(state.ip, _read)


def _cmd_show_config(state: SessionState) -> None:
    """3. Show current configuration."""
    if not _require_connection(state):
        return

    def _show(_dev: HwVxDevice, cfg: DeviceConfig) -> None:
        state.update_from_config(cfg)
        print_config(cfg)

    _with_device(state.ip, _show)  # type: ignore[arg-type]


def _cmd_change_ip(state: SessionState) -> None:
    """4. Change IP address."""
    if not _require_connection(state):
        return

    def _edit(_dev: HwVxDevice, cfg: DeviceConfig) -> None:
        state.update_from_config(cfg)

        ui.info("Edit network addressing (Enter = keep current value):\n")
        new_ip = ui.ask(
            "IP Address",
            cfg.ip_address,
            validator=ui.is_valid_ip,
            error_msg="Invalid IP address (e.g. 192.168.1.100).",
        )
        new_mask = ui.ask(
            "Subnet Mask",
            cfg.subnet_mask,
            validator=ui.is_valid_ip,
            error_msg="Invalid subnet mask.",
        )
        new_gw = ui.ask(
            "Gateway IP", cfg.gateway_ip, validator=ui.is_valid_ip, error_msg="Invalid gateway IP."
        )

        print()
        ui.kv("IP Address", new_ip)
        ui.kv("Subnet Mask", new_mask)
        ui.kv("Gateway IP", new_gw)
        print()

        if ui.confirm("Apply and reboot?"):
            # Need a fresh connection to apply
            try:
                with HwVxDevice(state.ip) as dev2:  # type: ignore[arg-type]
                    dev2.connect()
                    dev2.change_network(new_ip, new_mask, new_gw)
                ui.ok("Network settings applied. Reader is rebooting...")
                ui.hint("Wait ~5 seconds, then search again.")
                state.ip = new_ip
            except TimeoutError:
                ui.err("Reader not responding during apply.")
            except ConnectionError as exc:
                ui.err(f"Connection failed during apply: {exc}")
        else:
            ui.info("Cancelled.")

    _with_device(state.ip, _edit)  # type: ignore[arg-type]


def _cmd_dhcp(state: SessionState) -> None:
    """5. Enable/Disable DHCP."""
    if not _require_connection(state):
        return
    ui.info("1. Enable DHCP")
    ui.info("2. Disable DHCP (use static IP)")
    sub = input("  Select: ").strip()
    if sub not in ("1", "2"):
        ui.warn("Invalid choice.")
        return
    enable = sub == "1"
    action_word = "Enable" if enable else "Disable"
    if not ui.confirm(f"{action_word} DHCP and reboot?"):
        ui.info("Cancelled.")
        return
    try:
        with HwVxDevice(state.ip) as dev:  # type: ignore[arg-type]
            dev.connect()
            dev.set_dhcp(enable)
        action = "enabled" if enable else "disabled"
        ui.ok(f"DHCP {action}. Reader is rebooting...")
        if enable:
            ui.hint("Reader will get IP from DHCP server.")
            ui.hint("Search again after ~10 seconds to find new IP.")
    except TimeoutError:
        ui.err("Reader not responding.")
    except ConnectionError as exc:
        ui.err(f"Connection failed: {exc}")


def _cmd_remote_server(state: SessionState) -> None:
    """6. Change remote server."""
    if not _require_connection(state):
        return

    def _edit(dev: HwVxDevice, cfg: DeviceConfig) -> None:
        state.update_from_config(cfg)

        ui.kv("Remote IP", cfg.remote_ip)
        ui.kv("Remote Port", cfg.remote_port)
        ui.kv("Work Mode", fmt_option(cfg.work_mode, WORK_MODE_OPTIONS))
        print()

        cfg.remote_ip = ui.ask(
            "Remote IP", cfg.remote_ip, validator=ui.is_valid_ip, error_msg="Invalid IP address."
        )
        cfg.remote_port = ui.ask(
            "Remote Port",
            cfg.remote_port,
            validator=ui.is_valid_port,
            error_msg="Port must be 1-65535.",
        )
        cfg.work_mode = ui.ask("Work Mode", cfg.work_mode, WORK_MODE_OPTIONS)

        if ui.confirm("Save and reboot?"):
            dev.save_config(cfg)
            ui.ok("Remote server updated. Reader is rebooting...")
        else:
            ui.info("Cancelled.")

    _with_device(state.ip, _edit)  # type: ignore[arg-type]


def _cmd_edit_full(state: SessionState) -> None:
    """7. Edit & save full configuration."""
    if not _require_connection(state):
        return

    def _edit(dev: HwVxDevice, cfg: DeviceConfig) -> None:
        state.update_from_config(cfg)
        print_config(cfg)

        ui.info("Edit settings (press Enter to keep current value):\n")

        ui.section("Network")
        cfg.ip_address = ui.ask(
            "IP Address", cfg.ip_address, validator=ui.is_valid_ip, error_msg="Invalid IP address."
        )
        cfg.subnet_mask = ui.ask(
            "Subnet Mask",
            cfg.subnet_mask,
            validator=ui.is_valid_ip,
            error_msg="Invalid subnet mask.",
        )
        cfg.gateway_ip = ui.ask(
            "Gateway IP", cfg.gateway_ip, validator=ui.is_valid_ip, error_msg="Invalid gateway IP."
        )
        cfg.port_number = ui.ask(
            "Port", cfg.port_number, validator=ui.is_valid_port, error_msg="Port must be 1-65535."
        )
        cfg.protocol = ui.ask("Protocol", cfg.protocol, PROTOCOL_OPTIONS)
        cfg.work_mode = ui.ask("Work Mode", cfg.work_mode, WORK_MODE_OPTIONS)
        cfg.remote_ip = ui.ask(
            "Remote IP", cfg.remote_ip, validator=ui.is_valid_ip, error_msg="Invalid IP address."
        )
        cfg.remote_port = ui.ask(
            "Remote Port",
            cfg.remote_port,
            validator=ui.is_valid_port,
            error_msg="Port must be 1-65535.",
        )
        cfg.username = ui.ask("Username", cfg.username)
        cfg.device_name = ui.ask("Device Name", cfg.device_name)

        ui.section("Serial")
        cfg.baud_rate = ui.ask("Baud Rate", cfg.baud_rate, BAUD_RATE_OPTIONS)
        cfg.parity = ui.ask("Parity", cfg.parity, PARITY_OPTIONS)
        cfg.data_bits = ui.ask("Data Bits", cfg.data_bits, DATA_BITS_OPTIONS)
        cfg.dtr_mode = ui.ask("DTR Mode", cfg.dtr_mode, TOGGLE_OPTIONS)
        cfg.rts = ui.ask("RTS", cfg.rts, TOGGLE_OPTIONS)

        print()
        print_config(cfg)
        if ui.confirm("Save this configuration and reboot?"):
            dev.save_config(cfg)
            ui.ok("Configuration saved. Reader is rebooting...")
            ui.hint("Wait ~5 seconds, then search again.")
        else:
            ui.info("Cancelled.")

    _with_device(state.ip, _edit)  # type: ignore[arg-type]


def _cmd_reboot(state: SessionState) -> None:
    """8. Reboot reader."""
    if not _require_connection(state):
        return
    if not ui.confirm(f"Reboot reader at {state.ip}?"):
        ui.info("Cancelled.")
        return
    try:
        with HwVxDevice(state.ip) as dev:  # type: ignore[arg-type]
            dev.connect()
            dev.reboot()
        ui.ok("Reboot command sent.")
    except TimeoutError:
        ui.err("Reader not responding.")
    except ConnectionError as exc:
        ui.err(f"Connection failed: {exc}")


def _cmd_rfid_info(state: SessionState) -> None:
    """9. RFID reader info."""
    if not _require_config(state):
        return
    assert state.config is not None  # guarded above
    assert state.ip is not None
    try:
        tcp_port = int(state.config.port_number)
        with RfidClient(state.ip, tcp_port) as client:
            info = client.get_reader_info(state.reader_adr)
        state.reader_adr = info.address

        box = (
            Box()
            .hdr("RFID READER INFORMATION")
            .div()
            .row("Address", str(info.address))
            .row("Firmware", f"v{info.version}")
            .row("Reader Type", f"0x{info.reader_type:02X}")
            .row("Protocol", f"0x{info.protocol_type:02X}")
            .row("Power", f"{info.power} dBm" if info.power != 0xFF else "Unknown")
            .row("Scan Time", f"{info.scan_time * 100} ms")
        )
        print("\n" + box.render() + "\n")
    except TimeoutError:
        ui.err("RFID reader not responding.")
    except ConnectionError as exc:
        ui.err(f"Connection failed: {exc}")
    except ValueError as exc:
        ui.err(f"Bad response: {exc}")
    except RuntimeError as exc:
        ui.err(f"RFID error: {exc}")


def _cmd_set_rfid_addr(state: SessionState) -> None:
    """10. Set RFID reader address."""
    if not _require_config(state):
        return
    assert state.config is not None
    assert state.ip is not None
    try:
        tcp_port = int(state.config.port_number)
        with RfidClient(state.ip, tcp_port) as client:
            info = client.get_reader_info(state.reader_adr)
        state.reader_adr = info.address
        ui.info(f"Current reader address: {state.reader_adr}")

        new_adr_str = input("  New reader address (0-254): ").strip()
        if not new_adr_str:
            ui.info("Cancelled.")
            return

        try:
            new_adr = int(new_adr_str)
        except ValueError:
            ui.warn("Address must be a number.")
            return
        if not (0 <= new_adr <= 254):
            ui.warn("Address must be 0-254.")
            return

        ui.kv("Current address", str(state.reader_adr))
        ui.kv("New address", str(new_adr))
        if ui.confirm("Apply?"):
            with RfidClient(state.ip, tcp_port) as client:
                client.set_address(state.reader_adr, new_adr)
            ui.ok(f"Reader address changed: {state.reader_adr} -> {new_adr}")
            state.reader_adr = new_adr
        else:
            ui.info("Cancelled.")
    except TimeoutError:
        ui.err("RFID reader not responding.")
    except ConnectionError as exc:
        ui.err(f"Connection failed: {exc}")
    except ValueError as exc:
        ui.err(f"Bad response: {exc}")
    except RuntimeError as exc:
        ui.err(f"RFID error: {exc}")


# ─── Command dispatch table ──────────────────────────────────────────

COMMANDS: dict[str, Callable[[SessionState], None]] = {
    "1": _cmd_search,
    "2": _cmd_connect,
    "3": _cmd_show_config,
    "4": _cmd_change_ip,
    "5": _cmd_dhcp,
    "6": _cmd_remote_server,
    "7": _cmd_edit_full,
    "8": _cmd_reboot,
    "9": _cmd_rfid_info,
    "10": _cmd_set_rfid_addr,
}


# ─── Interactive menu ────────────────────────────────────────────────


def interactive_menu() -> None:
    """Main interactive menu loop with Ctrl+C handling."""
    try:
        _run_menu(SessionState())
    except KeyboardInterrupt:
        print()
        ui.info("Bye! 👋")


def _run_menu(state: SessionState) -> None:
    """Inner menu loop — separated for testability."""
    print(BANNER)
    print(MENU.render())

    while True:
        if state.connected:
            ui.info(f"📡 Connected: {state.ip} ({fmt_mac(state.mac or '')})")

        choice = input("\n  Select option: ").strip()

        if choice in ("q", "Q"):
            ui.info("Bye! 👋")
            break

        if choice in ("l", "L"):
            print(MENU.render())
            continue

        handler = COMMANDS.get(choice)
        if handler:
            handler(state)


# ─── Argument-based CLI ─────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    """Construct the argument parser."""
    parser = argparse.ArgumentParser(
        prog="hw-vx-config",
        description="HW-VX6330K / HW-VX6346KL Network Configuration Tool (Linux)",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="store_true",
        help="show version and exit",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("search", help="Search for readers on the network")

    p_cfg = sub.add_parser("config", help="Show reader configuration")
    p_cfg.add_argument("ip", help="Reader IP address")

    p_ip = sub.add_parser("set-ip", help="Change reader IP address (and optionally mask/gateway)")
    p_ip.add_argument("ip", help="Current reader IP")
    p_ip.add_argument("new_ip", help="New IP address")
    p_ip.add_argument("--mask", default=None, help="New subnet mask (reads from device if omitted)")
    p_ip.add_argument(
        "--gateway", default=None, help="New gateway IP (reads from device if omitted)"
    )

    p_dhcp = sub.add_parser("dhcp", help="Enable or disable DHCP")
    p_dhcp.add_argument("ip", help="Reader IP address")
    p_dhcp.add_argument("state", choices=["on", "off"])

    p_reboot = sub.add_parser("reboot", help="Reboot the reader")
    p_reboot.add_argument("ip", help="Reader IP address")

    sub.add_parser("interactive", help="Interactive menu (default)")

    # ── RFID reader commands ──
    p_ri = sub.add_parser("reader-info", help="Get RFID reader information (via TCP)")
    p_ri.add_argument("ip", help="Reader IP address")
    p_ri.add_argument("port", type=int, help="TCP port (from device network config)")
    p_ri.add_argument("--adr", type=int, default=0, help="Reader address 0-254 (default: 0)")

    p_sa = sub.add_parser("set-reader-addr", help="Set RFID reader address (via TCP)")
    p_sa.add_argument("ip", help="Reader IP address")
    p_sa.add_argument("port", type=int, help="TCP port (from device network config)")
    p_sa.add_argument("new_addr", type=int, help="New reader address (0-254)")
    p_sa.add_argument("--adr", type=int, default=0, help="Current reader address (default: 0)")

    return parser


def main(argv: list[str] | None = None) -> None:
    """Entry point for both ``python -m hw_vx_config`` and the console script."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        from hw_vx_config import __version__

        print(f"hw-vx-config {__version__}")
        return

    if args.command is None or args.command == "interactive":
        interactive_menu()
        return

    if args.command == "search":
        search_readers()

    elif args.command == "config":
        try:
            with HwVxDevice(args.ip) as dev:
                dev.connect()
                cfg = dev.get_config()
                print_config(cfg)
        except TimeoutError:
            ui.err("Reader not responding. Check IP and network cable.")
        except ConnectionError as exc:
            ui.err(f"Connection failed: {exc}")

    elif args.command == "set-ip":
        try:
            with HwVxDevice(args.ip) as dev:
                dev.connect()
                new_cfg: DeviceConfig | None = (
                    dev.get_config() if (args.mask is None or args.gateway is None) else None
                )
                mask = args.mask or (
                    new_cfg.subnet_mask if new_cfg is not None else "255.255.255.0"
                )
                gateway = args.gateway or (new_cfg.gateway_ip if new_cfg is not None else "0.0.0.0")
                dev.change_network(args.new_ip, mask, gateway)
            print(f"IP changed to {args.new_ip} (mask={mask} gw={gateway}). Reader rebooting...")
        except TimeoutError:
            ui.err("Reader not responding.")
        except ConnectionError as exc:
            ui.err(f"Connection failed: {exc}")

    elif args.command == "dhcp":
        try:
            with HwVxDevice(args.ip) as dev:
                dev.connect()
                dev.set_dhcp(args.state == "on")
            state_str = "enabled" if args.state == "on" else "disabled"
            print(f"DHCP {state_str}. Reader rebooting...")
        except TimeoutError:
            ui.err("Reader not responding.")
        except ConnectionError as exc:
            ui.err(f"Connection failed: {exc}")

    elif args.command == "reboot":
        try:
            with HwVxDevice(args.ip) as dev:
                dev.connect()
                dev.reboot()
            print("Reboot command sent.")
        except TimeoutError:
            ui.err("Reader not responding.")
        except ConnectionError as exc:
            ui.err(f"Connection failed: {exc}")

    elif args.command == "reader-info":
        try:
            with RfidClient(args.ip, args.port) as client:
                info = client.get_reader_info(args.adr)
            box = (
                Box()
                .hdr("RFID READER INFORMATION")
                .div()
                .row("Address", str(info.address))
                .row("Firmware", f"v{info.version}")
                .row("Reader Type", f"0x{info.reader_type:02X}")
                .row("Protocol", f"0x{info.protocol_type:02X}")
                .row("Power", f"{info.power} dBm" if info.power != 0xFF else "Unknown")
                .row("Scan Time", f"{info.scan_time * 100} ms")
            )
            print("\n" + box.render() + "\n")
        except TimeoutError:
            ui.err("RFID reader not responding.")
        except ConnectionError as exc:
            ui.err(f"Connection failed: {exc}")

    elif args.command == "set-reader-addr":
        try:
            with RfidClient(args.ip, args.port) as client:
                client.set_address(args.adr, args.new_addr)
            print(
                f"Reader address changed: {args.adr} -> {args.new_addr}\n"
                f"Use --adr {args.new_addr} for subsequent commands."
            )
        except TimeoutError:
            ui.err("RFID reader not responding.")
        except ConnectionError as exc:
            ui.err(f"Connection failed: {exc}")
