# `hw_vx_config.formatting`

Pretty-printing helpers for device configuration.

**Source:** [`src/hw_vx_config/formatting.py`](../../src/hw_vx_config/formatting.py)

---

## `fmt_option`

```python
def fmt_option(value: str, options: dict[int, str]) -> str
```

Format an index *value* with its human-readable label from an options map.

| Parameter | Type | Description |
|---|---|---|
| `value` | `str` | The raw index string (e.g. `"3"`) |
| `options` | `dict[int, str]` | Look-up map (e.g. `BAUD_RATE_OPTIONS`) |

**Returns:** Formatted string like `"3 (9600)"`, or the raw value if it
can't be parsed as an integer.

**Examples:**

```python
>>> fmt_option("0", {0: "UDP", 1: "TCP"})
"0 (UDP)"

>>> fmt_option("abc", {0: "UDP"})
"abc"
```

---

## `format_config`

```python
def format_config(cfg: DeviceConfig) -> str
```

Return a pretty box-drawing string representation of a
[`DeviceConfig`](models.md#deviceconfig). Contains three sections:
Network Settings, Serial Settings, and Advanced Settings.

**Returns:** Multi-line string with Unicode box-drawing characters.

---

## `print_config`

```python
def print_config(cfg: DeviceConfig) -> None
```

Print `format_config(cfg)` to stdout. Convenience wrapper.
