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

## Documentation

📖 **[Full API Reference →](docs/README.md)**

| Module | Docs | Description |
|---|---|---|
| `constants` | [reference](docs/api/constants.md) | Protocol constants, setting codes, option tables |
| `models` | [reference](docs/api/models.md) | `SearchResult` and `DeviceConfig` dataclasses |
| `transport` | [reference](docs/api/transport.md) | Low-level UDP transport (`HwVxNetworking`) |
| `device` | [reference](docs/api/device.md) | High-level device operations (`HwVxDevice`) |
| `formatting` | [reference](docs/api/formatting.md) | Pretty-print helpers |
| `cli` | [reference](docs/api/cli.md) | Interactive menu & scriptable sub-commands |

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
├── tests/                 # 55 unit tests (mocked sockets)
├── docs/                  # API reference & architecture
│   ├── README.md
│   └── api/
├── main.py                # python main.py entry point
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
