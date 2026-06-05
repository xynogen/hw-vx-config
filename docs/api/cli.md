# `hw_vx_config.cli`

Command-line interface — both interactive (TUI menu) and scriptable sub-commands.

**Source:** [`src/hw_vx_config/cli.py`](../../src/hw_vx_config/cli.py)

---

## Entry Points

All three invoke the same `main()` function:

```bash
python main.py [args]         # Convenience wrapper
python -m hw_vx_config [args] # Module mode
hw-vx-config [args]           # Console script (after pip install)
```

---

## `main`

```python
def main(argv: list[str] | None = None) -> None
```

Top-level entry point. Parses arguments and dispatches to the appropriate
sub-command or launches the interactive menu.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `argv` | `list[str] \| None` | `None` | Argument list. `None` = `sys.argv[1:]` |

---

## Sub-commands

### `search`

```bash
hw-vx-config search
```

Broadcast UDP search for all readers on the local network. Prints a
table of discovered devices.

### `config <ip>`

```bash
hw-vx-config config 192.168.1.100
```

Connect to the reader at `<ip>`, read all 22 settings, and print a
formatted configuration table.

### `set-ip <ip> <new_ip>`

```bash
hw-vx-config set-ip 192.168.1.100 10.0.0.50
```

Change the reader's IP address from `<ip>` to `<new_ip>` and reboot.

### `dhcp <ip> <on|off>`

```bash
hw-vx-config dhcp 192.168.1.100 on
```

Enable or disable DHCP on the reader and reboot.

### `reboot <ip>`

```bash
hw-vx-config reboot 192.168.1.100
```

Send a reboot command to the reader.

### `interactive` (default)

```bash
hw-vx-config
hw-vx-config interactive
```

Launch the interactive TUI menu with options for search, configure,
change IP, DHCP, edit full config, reboot, and manual IP entry.

---

## Flags

| Flag | Description |
|---|---|
| `-V`, `--version` | Print version and exit |

---

## Helper Functions

### `search_readers`

```python
def search_readers() -> list[SearchResult]
```

Broadcast search and print results table. Returns the list of
[`SearchResult`](models.md#searchresult) objects found.

### `select_reader`

```python
def select_reader(results: list[SearchResult]) -> SearchResult | None
```

Interactive prompt to pick a reader from a list. Auto-selects if only one
result. Returns `None` if the user cancels.
