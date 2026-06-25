# hw-vx-config

Network configuration tool for HW-VX6330K / HW-VX6346KL serial-to-Ethernet modules on Linux.
Sends UDP packets directly to the device — no DLLs, no runtime dependencies, pure stdlib.

Accepts a device IP or discovers via broadcast; reads and writes all network, serial, and
advanced settings over the HW-VX UDP protocol (port 65535).

## Table of Contents

- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [CLI Reference](#cli-reference)
- [Interactive Menu](#interactive-menu)
- [Protocol](#protocol)
- [Examples](#examples)
- [Development](#development)
- [License](#license)

## Requirements

- Python 3.10 or later
- Linux (uses `SO_BROADCAST`; port 65535 requires no root)
- Device reachable on the local network (same subnet or routed UDP)

## Quick Start

```bash
python -m venv .venv && source .venv/bin/activate
pip install hw-vx-config

# Discover all readers on the network
hw-vx-config search
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

## Interactive Menu

The interactive menu (`hw-vx-config` with no arguments) provides a numbered prompt:

```
1. Search for readers          — broadcast discovery, select from results
2. Connect to specific IP      — skip discovery, target a known address directly
3. Show current configuration
4. Change IP address
5. Enable/Disable DHCP
6. Edit & save full configuration — field-by-field editor, confirm before write
7. Change remote server        — set Remote IP, Remote Port, Work Mode
8. Reboot reader
q. Quit
```

Option 2 is useful when the device is on a different subnet and broadcast cannot reach it.

## Protocol

UDP on port **65535**. Every packet is ASCII. Replies are prefixed with `A`.

| Prefix | Direction | Action |
|:---|:---|:---|
| `X` | → device | Broadcast echo — triggers discovery reply |
| `W{mac}` | → device | Select device by MAC |
| `L` | → device | Login |
| `O` | → device | Logout |
| `G{code}` | → device | Get one setting |
| `S{code}{value}\|{seq}` | → device | Set one setting |
| `E` | → device | Save and reboot |
| `A{payload}` | ← device | All replies |

Discovery reply format: `A{mac}/{port}/.../{username}/{device_name}` from the device's source IP.

Setting codes of note: `IP` (IP address), `NM` (subnet mask), `GI` (gateway), `DH` (DHCP),
`BR` (baud rate), `TP` (protocol), `RM` (work mode). Full table in `src/hw_vx_config/constants.py`.

## Examples

The `examples/` directory contains companion scripts.

| File | Description |
|:---|:---|
| `server_uhf.py` | TCP server that receives RFID tag data from the reader on port 2077. Run this alongside the reader when `Work Mode` is set to `Client` and `Remote Port` is `2077`. |
| `library_usage.py` | Shows how to use `HwVxDevice` and `HwVxNetworking` directly in Python code — discover, read config, change settings, and quick operations. |

```bash
python examples/server_uhf.py
# Listening on 0.0.0.0:2077
```

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

## Tested with

- Package version: **0.1.0**
- Hardware: HW-VX6330K, HW-VX6346KL
- Protocol: UDP port 65535, ASCII request/reply
- OS: Linux (Ubuntu 22.04+)

## License

MIT
