# hw-vx-config

Network configuration tool for **HW-VX6330K / HW-VX6346KL** serial-to-Ethernet modules on Linux.

Ported from the C# Demo v2.11 — pure Python, no DLLs needed.

## Features

- **Discover** readers on the network via UDP broadcast
- **Read / write** full device configuration (network, serial, advanced)
- **Change IP**, toggle DHCP, reboot — one command
- Interactive TUI menu **and** scriptable CLI sub-commands

## Quick Start

```bash
# Install (editable, with dev tools)
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Interactive mode
hw-vx-config

# Or use sub-commands
hw-vx-config search
hw-vx-config config 192.168.1.100
hw-vx-config set-ip 192.168.1.100 10.0.0.50
hw-vx-config dhcp 192.168.1.100 on
hw-vx-config reboot 192.168.1.100
```

## Project Structure

```
hw-vx-config/
├── src/hw_vx_config/
│   ├── __init__.py        # Package root & public API
│   ├── __main__.py        # python -m hw_vx_config
│   ├── cli.py             # Argument parser + interactive menu
│   ├── constants.py       # Protocol constants & option tables
│   ├── device.py          # High-level device operations
│   ├── formatting.py      # Pretty-print helpers
│   ├── models.py          # SearchResult & DeviceConfig dataclasses
│   └── transport.py       # Low-level UDP socket transport
├── tests/
│   ├── conftest.py        # Shared fixtures
│   ├── test_cli.py
│   ├── test_constants.py
│   ├── test_device.py
│   ├── test_formatting.py
│   ├── test_models.py
│   └── test_transport.py
├── pyproject.toml         # Build config, deps, tool settings
├── requirements.txt
└── requirements-dev.txt
```

## Development

```bash
# Format
ruff format src/ tests/

# Lint
ruff check --fix src/ tests/

# Test
pytest -v

# Test with coverage
pytest --cov=hw_vx_config --cov-report=term-missing
```

## Protocol

UDP packets on port **65535**. Command prefixes:

| Prefix | Action |
|--------|--------|
| `X` | Broadcast search (echo) |
| `W{mac}` | Select device |
| `L` | Login |
| `O` | Logout |
| `G{code}` | Get setting |
| `S{code}{value}` | Set setting |
| `E` | Reboot |

## License

MIT
