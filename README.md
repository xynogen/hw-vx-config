# hw-vx-config

[![PyPI version](https://img.shields.io/pypi/v/hw-vx-config)](https://pypi.org/project/hw-vx-config/)
[![Python](https://img.shields.io/pypi/pyversions/hw-vx-config)](https://pypi.org/project/hw-vx-config/)
[![License: MIT](https://img.shields.io/github/license/xynogen/hw-vx-config)](LICENSE)
[![CI](https://github.com/xynogen/hw-vx-config/actions/workflows/ci.yml/badge.svg)](https://github.com/xynogen/hw-vx-config/actions/workflows/ci.yml)

Network configuration tool for HW-VX6330K / HW-VX6346KL serial-to-Ethernet modules on Linux.
Sends UDP packets directly to the device — no DLLs, no runtime dependencies, pure stdlib.

Accepts a device IP or discovers via broadcast; reads and writes all network, serial, and
advanced settings over the HW-VX UDP protocol (port 65535).

> **Note:** This tool has only been tested on Linux. While it may work on other platforms,
> no guarantees are made for macOS or Windows.

## Table of Contents

- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [CLI Reference](#cli-reference)
- [Interactive Menu](#interactive-menu)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Protocol](#protocol)
- [Documentation](#documentation)
- [Uninstall](#uninstall)
- [License](#license)

## Requirements

- Python 3.10 or later
- Linux (uses `SO_BROADCAST`; port 65535 requires no root)
- Device reachable on the local network (same subnet or routed UDP)

## Quick Start

```bash
pip install hw-vx-config

# Discover all readers on the network
hw-vx-config search
```

Or install with [pipx](https://pipx.pypa.io/) for isolated CLI usage:

```bash
pipx install hw-vx-config
```

## CLI Reference

All operations take the current device IP as the first positional argument.

```bash
# Discover all readers via broadcast
hw-vx-config search

# Print full configuration for a device
hw-vx-config config <ip>

# Change static IP and reboot
hw-vx-config set-ip <current-ip> <new-ip>

# Enable or disable DHCP and reboot
hw-vx-config dhcp <ip> on|off

# Send reboot command
hw-vx-config reboot <ip>

# Launch interactive menu
hw-vx-config interactive
hw-vx-config              # same — interactive is the default
```

### RFID Reader Commands

These commands use the UHF RFID binary protocol (UHFReader18) over TCP.
The `<port>` is the device's configured TCP port (from network settings).

```bash
# Get reader information (address, firmware, power, etc.)
hw-vx-config reader-info <ip> <port>

# Set reader address from 0 to 1
hw-vx-config set-reader-addr <ip> <port> 1

# Set reader address when current address is not 0
hw-vx-config set-reader-addr <ip> <port> 5 --adr 1
```

## Interactive Menu

The interactive menu (`hw-vx-config` with no arguments) provides a numbered prompt:

```
  ╔══════════════════════════════════════════════════════╗
  ║  HW-VX6330K / HW-VX6346KL  Network Config Tool       ║
  ║  Linux Edition — ported from C# Demo v2.11           ║
  ╚══════════════════════════════════════════════════════╝

  ╔══════════════════════════════════════════════════════╗
  ║  1. Search for readers                               ║  ← broadcast discovery, select from results
  ║  2. Connect to specific IP                           ║  ← skip discovery, target a known address
  ╠══════════════════════════════════════════════════════╣
  ║  3. Show current configuration                       ║
  ║  4. Change IP address                                ║
  ║  5. Enable/Disable DHCP                              ║
  ║  6. Change remote server                             ║  ← Remote IP, Remote Port, Work Mode
  ╠══════════════════════════════════════════════════════╣
  ║  7. Edit & save full configuration                   ║  ← field-by-field editor, confirm before write
  ║  8. Reboot reader                                    ║
  ╠══════════════════════════════════════════════════════╣
  ║  9. RFID reader info                                 ║  ← address, firmware, power (TCP binary)
  ║  10. Set RFID reader address                         ║  ← change reader Adr (0–254)
  ╠══════════════════════════════════════════════════════╣
  ║  q. Quit   l. List menu                              ║
  ╚══════════════════════════════════════════════════════╝
```

Option 2 is useful when the device is on a different subnet and broadcast cannot reach it.

## Examples

The `examples/` directory contains companion scripts.

| File | Description |
|:---|:---|
| `server_uhf.py` | TCP server that receives RFID tag data from the reader on port 2077. Run this alongside the reader when `Work Mode` is set to `Client` and `Remote Port` is `2077`. |
| `library_usage.py` | Shows how to use `HwVxDevice` and `HwVxNetworking` directly in Python code — discover, read config, change settings, and quick operations. |
| `rfid_usage.py` | Shows how to use `RfidClient` to get reader info and change the reader address via the binary protocol. |

```bash
python examples/server_uhf.py
# Listening on 0.0.0.0:2077
```

## Troubleshooting

| Problem | Possible cause | Fix |
|:---|:---|:---|
| `search` returns nothing | Firewall blocks UDP 65535 | Open UDP 65535 inbound/outbound (`sudo ufw allow 65535/udp`) |
| | Device on a different subnet | Use `hw-vx-config interactive` → option 2 (connect by IP) |
| | Broadcast not reaching device | Ensure host and device share the same L2 network / VLAN |
| Timeout on `config` / `set-ip` | Device IP changed or unreachable | Verify with `ping <ip>`; re-discover with `search` |
| `Permission denied` on socket | Rare kernel policy | Run with `sudo` or check `sysctl net.ipv4.ip_unprivileged_port_start` |

## Development

Install with dev extras, then use the standard toolchain:

```bash
pip install -e ".[dev]"

# Lint and format
ruff check --fix src/ tests/
ruff format src/ tests/

# Type check
mypy src/

# Run tests
pytest

# Tests with coverage
pytest --cov=hw_vx_config --cov-report=term-missing
```

Tests live in `tests/` and mock the UDP socket — no device needed to run them.

## Protocol

UDP port **65535** (device config) and TCP port **2077** (RFID tag push). Full details → [`docs/api/protocol.md`](docs/api/protocol.md) and [`docs/DOCUMENTATION.md`](docs/DOCUMENTATION.md).

## Further Reading

- **[`docs/api/`](docs/api/)** — per-module API reference and RFID binary protocol
- **[`docs/DOCUMENTATION.md`](docs/DOCUMENTATION.md)** — full UHFReader18 manual (EPC C1G2 / ISO18000-6B command set, status codes, tag memory)

## Uninstall

```bash
pip uninstall hw-vx-config
# or if installed with pipx:
pipx uninstall hw-vx-config
```

## Tested with

- Hardware: HW-VX6330K, HW-VX6346KL
- Protocol: UDP port 65535, ASCII request/reply
- OS: Linux (Ubuntu 22.04+)

## License

MIT — see [PyPI page](https://pypi.org/project/hw-vx-config/) for the published package.
