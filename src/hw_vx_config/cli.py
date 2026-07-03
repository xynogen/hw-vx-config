"""
Command-line interface — both interactive (TUI menu) and scriptable sub-commands.
"""

from __future__ import annotations

import argparse

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

# ─── Interactive helpers ─────────────────────────────────────────────


def _ask(label: str, current: str, options: dict[int, str] | None = None) -> str:
    """Prompt for a single field; empty input keeps current value."""
    if options:
        hint = ", ".join(f"{k}={v}" for k, v in options.items())
        val = input(f"    {label} [{current}] ({hint}): ").strip()
    else:
        val = input(f"    {label} [{current}]: ").strip()
    return val if val else current


def search_readers() -> list[SearchResult]:
    """Broadcast search for all readers on the network."""
    ui.info("🔍 Searching for readers (broadcast)...")
    with HwVxNetworking("255.255.255.255") as net:
        results = net.search()

    if not results:
        ui.warn("No readers found. Check cable and network.")
        return []

    ui.info(f"Found {len(results)} reader(s):\n")
    ui.info(f"{'#':<4} {'IP Address':<18} {'MAC Address':<20} {'Port':<8} {'Name'}")
    ui.info(f"{'─' * 4} {'─' * 18} {'─' * 20} {'─' * 8} {'─' * 20}")
    for i, r in enumerate(results, 1):
        ui.info(
            f"{i:<4} {r.ip_address:<18} {fmt_mac(r.mac_address):<20} {r.port_number:<8} {r.device_name}"
        )
    print()
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


# ─── Interactive menu ────────────────────────────────────────────────


def interactive_menu() -> None:
    """Main interactive menu loop."""

    selected_ip: str | None = None
    selected_mac: str | None = None
    current_config: DeviceConfig | None = None
    reader_adr: int = 0  # RFID reader address, discovered via option 9

    _menu = (
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

    print(BANNER)
    print(_menu.render())

    while True:
        if selected_ip:
            ui.info(f"📡 Connected: {selected_ip} ({fmt_mac(selected_mac or '')})")

        choice = input("\n  Select option: ").strip()

        if choice in ("q", "Q"):
            ui.info("Bye! 👋")
            break

        if choice in ("l", "L"):
            print(_menu.render())
            continue

        # ── 1. Search ──
        if choice == "1":
            results = search_readers()
            if results:
                r = select_reader(results)
                if r:
                    selected_ip = r.ip_address
                    selected_mac = r.mac_address
                    ui.ok(f"Selected: {selected_ip}")
                    try:
                        with HwVxDevice(selected_ip) as dev:
                            dev.connect()
                            current_config = dev.get_config()
                            selected_mac = current_config.mac_address or selected_mac
                        ui.ok("Configuration loaded.")
                    except Exception as e:
                        ui.warn(f"Could not read config: {e}")

        # ── 2. Connect to specific IP ──
        elif choice == "2":
            ip = input("  Enter reader IP address: ").strip()
            if ip:
                selected_ip = ip
                selected_mac = ""
                ui.info(f"Connecting to {ip}...")
                try:
                    with HwVxDevice(selected_ip) as dev:
                        dev.connect()
                        current_config = dev.get_config()
                        selected_mac = current_config.mac_address or selected_mac
                    ui.ok(f"Connected to {ip} (port {current_config.port_number}).")
                except Exception as e:
                    ui.warn(f"Connected but could not read config: {e}")
                    ui.hint("RFID commands will ask for the TCP port manually.")

        # ── 3. Show config ──
        elif choice == "3":
            if not selected_ip:
                ui.warn("No reader selected. Search first (option 1).")
                continue
            try:
                with HwVxDevice(selected_ip) as dev:
                    dev.connect()
                    current_config = dev.get_config()
                    selected_mac = current_config.mac_address or selected_mac
                    print_config(current_config)
            except Exception as e:
                ui.err(f"Error: {e}")

        # ── 4. Change IP ──
        elif choice == "4":
            if not selected_ip:
                ui.warn("No reader selected. Search first (option 1).")
                continue
            try:
                # Read current values so user can press Enter to keep them
                with HwVxDevice(selected_ip) as dev:
                    dev.connect()
                    cfg = dev.get_config()
                    current_config = cfg
                    selected_mac = cfg.mac_address or selected_mac

                ui.info("Edit network addressing (Enter = keep current value):\n")
                new_ip = _ask("IP Address", cfg.ip_address)
                new_mask = _ask("Subnet Mask", cfg.subnet_mask)
                new_gw = _ask("Gateway IP", cfg.gateway_ip)

                print()
                ui.kv("IP Address", new_ip)
                ui.kv("Subnet Mask", new_mask)
                ui.kv("Gateway IP", new_gw)
                print()

                confirm = input("  Apply and reboot? (y/n): ").strip().lower()
                if confirm == "y":
                    with HwVxDevice(selected_ip) as dev:
                        dev.connect()
                        dev.change_network(new_ip, new_mask, new_gw)
                    ui.ok("Network settings applied. Reader is rebooting...")
                    ui.hint("Wait ~5 seconds, then search again.")
                    selected_ip = new_ip
                else:
                    ui.info("Cancelled.")
            except Exception as e:
                ui.err(f"Error: {e}")

        # ── 5. DHCP ──
        elif choice == "5":
            if not selected_ip:
                ui.warn("No reader selected. Search first (option 1).")
                continue
            ui.info("1. Enable DHCP")
            ui.info("2. Disable DHCP (use static IP)")
            sub = input("  Select: ").strip()
            if sub in ("1", "2"):
                enable = sub == "1"
                confirm = (
                    input(f"  {'Enable' if enable else 'Disable'} DHCP and reboot? (y/n): ")
                    .strip()
                    .lower()
                )
                if confirm == "y":
                    try:
                        with HwVxDevice(selected_ip) as dev:
                            dev.connect()
                            dev.set_dhcp(enable)
                        action = "enabled" if enable else "disabled"
                        ui.ok(f"DHCP {action}. Reader is rebooting...")
                        if enable:
                            ui.hint("Reader will get IP from DHCP server.")
                            ui.hint("Search again after ~10 seconds to find new IP.")
                    except Exception as e:
                        ui.err(f"Error: {e}")

        # ── 6. Change remote server ──
        elif choice == "6":
            if not selected_ip:
                ui.warn("No reader selected. Search first (option 1).")
                continue
            try:
                with HwVxDevice(selected_ip) as dev:
                    dev.connect()
                    cfg = dev.get_config()

                    ui.kv("Remote IP", cfg.remote_ip)
                    ui.kv("Remote Port", cfg.remote_port)
                    ui.kv("Work Mode", fmt_option(cfg.work_mode, WORK_MODE_OPTIONS))
                    print()

                    new_remote_ip = input(f"  Remote IP [{cfg.remote_ip}]: ").strip()
                    new_remote_port = input(f"  Remote Port [{cfg.remote_port}]: ").strip()
                    new_work_mode = input(
                        f"  Work Mode [{cfg.work_mode}] (0=Server, 1=Client): "
                    ).strip()

                    cfg.remote_ip = new_remote_ip or cfg.remote_ip
                    cfg.remote_port = new_remote_port or cfg.remote_port
                    cfg.work_mode = new_work_mode or cfg.work_mode

                    confirm = input("  Save and reboot? (y/n): ").strip().lower()
                    if confirm == "y":
                        dev.save_config(cfg)
                        ui.ok("Remote server updated. Reader is rebooting...")
                    else:
                        ui.info("Cancelled.")
            except Exception as e:
                ui.err(f"Error: {e}")

        # ── 7. Edit full config ──
        elif choice == "7":
            if not selected_ip:
                ui.warn("No reader selected. Search first (option 1).")
                continue
            try:
                with HwVxDevice(selected_ip) as dev:
                    dev.connect()
                    cfg = dev.get_config()
                    current_config = cfg
                    selected_mac = cfg.mac_address or selected_mac
                    print_config(cfg)

                    ui.info("Edit settings (press Enter to keep current value):\n")

                    ui.section("Network")
                    cfg.ip_address = _ask("IP Address", cfg.ip_address)
                    cfg.subnet_mask = _ask("Subnet Mask", cfg.subnet_mask)
                    cfg.gateway_ip = _ask("Gateway IP", cfg.gateway_ip)
                    cfg.port_number = _ask("Port", cfg.port_number)
                    cfg.protocol = _ask("Protocol", cfg.protocol, PROTOCOL_OPTIONS)
                    cfg.work_mode = _ask("Work Mode", cfg.work_mode, WORK_MODE_OPTIONS)
                    cfg.remote_ip = _ask("Remote IP", cfg.remote_ip)
                    cfg.remote_port = _ask("Remote Port", cfg.remote_port)
                    cfg.username = _ask("Username", cfg.username)
                    cfg.device_name = _ask("Device Name", cfg.device_name)

                    ui.section("Serial")
                    cfg.baud_rate = _ask("Baud Rate", cfg.baud_rate, BAUD_RATE_OPTIONS)
                    cfg.parity = _ask("Parity", cfg.parity, PARITY_OPTIONS)
                    cfg.data_bits = _ask("Data Bits", cfg.data_bits, DATA_BITS_OPTIONS)
                    cfg.dtr_mode = _ask("DTR Mode", cfg.dtr_mode, TOGGLE_OPTIONS)
                    cfg.rts = _ask("RTS", cfg.rts, TOGGLE_OPTIONS)

                    print()
                    print_config(cfg)
                    confirm = input("  Save this configuration and reboot? (y/n): ").strip().lower()
                    if confirm == "y":
                        dev.save_config(cfg)
                        ui.ok("Configuration saved. Reader is rebooting...")
                        ui.hint("Wait ~5 seconds, then search again.")
                    else:
                        ui.info("Cancelled.")
            except Exception as e:
                ui.err(f"Error: {e}")

        # ── 8. Reboot ──
        elif choice == "8":
            if not selected_ip:
                ui.warn("No reader selected. Search first (option 1).")
                continue
            confirm = input(f"  Reboot reader at {selected_ip}? (y/n): ").strip().lower()
            if confirm == "y":
                try:
                    with HwVxDevice(selected_ip) as dev:
                        dev.connect()
                        dev.reboot()
                    ui.ok("Reboot command sent.")
                except Exception as e:
                    ui.err(f"Error: {e}")

        # ── 9. RFID reader info ──
        elif choice == "9":
            if not selected_ip:
                ui.warn("No reader selected. Search first (option 1).")
                continue
            if not current_config:
                ui.warn("No config loaded. Connect first (option 1 or 2).")
                continue
            try:
                tcp_port = int(current_config.port_number)
                with RfidClient(selected_ip, tcp_port) as client:
                    info = client.get_reader_info(reader_adr)
                reader_adr = info.address

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
            except Exception as e:
                ui.err(f"Error: {e}")

        # ── 10. Set RFID reader address ──
        elif choice == "10":
            if not selected_ip:
                ui.warn("No reader selected. Search first (option 1).")
                continue
            if not current_config:
                ui.warn("No config loaded. Connect first (option 1 or 2).")
                continue
            try:
                tcp_port = int(current_config.port_number)
                # Auto-read current address if not yet known
                with RfidClient(selected_ip, tcp_port) as client:
                    info = client.get_reader_info(reader_adr)
                reader_adr = info.address
                ui.info(f"Current reader address: {reader_adr}")

                new_adr_str = input("  New reader address (0-254): ").strip()
                if not new_adr_str:
                    ui.info("Cancelled.")
                    continue
                new_adr = int(new_adr_str)
                if not (0 <= new_adr <= 254):
                    ui.warn("Address must be 0-254.")
                    continue

                ui.kv("Current address", str(reader_adr))
                ui.kv("New address", str(new_adr))
                confirm = input("  Apply? (y/n): ").strip().lower()
                if confirm == "y":
                    with RfidClient(selected_ip, tcp_port) as client:
                        client.set_address(reader_adr, new_adr)
                    ui.ok(f"Reader address changed: {reader_adr} -> {new_adr}")
                    reader_adr = new_adr
                else:
                    ui.info("Cancelled.")
            except Exception as e:
                ui.err(f"Error: {e}")

        else:
            pass


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
        with HwVxDevice(args.ip) as dev:
            dev.connect()
            cfg = dev.get_config()
            print_config(cfg)

    elif args.command == "set-ip":
        with HwVxDevice(args.ip) as dev:
            dev.connect()
            new_cfg: DeviceConfig | None = (
                dev.get_config() if (args.mask is None or args.gateway is None) else None
            )
            mask = args.mask or (new_cfg.subnet_mask if new_cfg is not None else "255.255.255.0")
            gateway = args.gateway or (new_cfg.gateway_ip if new_cfg is not None else "0.0.0.0")
            dev.change_network(args.new_ip, mask, gateway)
        print(f"IP changed to {args.new_ip} (mask={mask} gw={gateway}). Reader rebooting...")

    elif args.command == "dhcp":
        with HwVxDevice(args.ip) as dev:
            dev.connect()
            dev.set_dhcp(args.state == "on")
        state = "enabled" if args.state == "on" else "disabled"
        print(f"DHCP {state}. Reader rebooting...")

    elif args.command == "reboot":
        with HwVxDevice(args.ip) as dev:
            dev.connect()
            dev.reboot()
        print("Reboot command sent.")

    elif args.command == "reader-info":
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

    elif args.command == "set-reader-addr":
        with RfidClient(args.ip, args.port) as client:
            client.set_address(args.adr, args.new_addr)
        print(
            f"Reader address changed: {args.adr} -> {args.new_addr}\n"
            f"Use --adr {args.new_addr} for subsequent commands."
        )
