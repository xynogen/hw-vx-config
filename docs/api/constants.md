# `hw_vx_config.constants`

Protocol constants and option look-up tables extracted from the C# Demo v2.11.

**Source:** [`src/hw_vx_config/constants.py`](../../src/hw_vx_config/constants.py)

---

## Protocol Constants

| Constant | Value | Description |
|---|---|---|
| `UDP_PORT` | `65535` | Destination port for all commands |
| `RECV_TIMEOUT` | `1.0` | Socket receive timeout (seconds) |
| `RECV_BUFFER` | `1024` | Receive buffer size (bytes) |

---

## Setting Codes (`SETTINGS`)

A `dict[str, str]` mapping two-letter codes to human-readable names.
Used in `G{code}` (get) and `S{code}{value}` (set) commands.

### Network

| Code | Name |
|------|------|
| `ON` | Username |
| `DN` | Device Name |
| `FE` | MAC Address |
| `IP` | IP Address |
| `PN` | Port Number |
| `TP` | Protocol |
| `RM` | Work Mode |
| `DI` | Remote IP |
| `DP` | Remote Port |
| `GI` | Gateway IP |
| `NM` | Subnet Mask |
| `DH` | DHCP |

### Serial

| Code | Name |
|------|------|
| `BR` | Baud Rate |
| `PR` | Parity |
| `BB` | Data Bits |
| `DT` | DTR Mode |
| `FC` | RTS |

### Advanced

| Code | Name |
|------|------|
| `CM` | Connection Mode |
| `CT` | Connection Timeout |
| `RC` | Reconnect |
| `ML` | Max Length |
| `MD` | Max Delay |

---

## Option Maps

Used to convert numeric indices to human-readable labels.

### `PROTOCOL_OPTIONS`

| Index | Label |
|-------|-------|
| `0` | UDP |
| `1` | TCP |

### `WORK_MODE_OPTIONS`

| Index | Label |
|-------|-------|
| `0` | Server |
| `1` | Client |

### `DHCP_OPTIONS` / `TOGGLE_OPTIONS`

| Index | Label |
|-------|-------|
| `0` | Disabled |
| `1` | Enabled |

### `BAUD_RATE_OPTIONS`

| Index | Label |
|-------|-------|
| `0` | 1200 |
| `1` | 2400 |
| `2` | 4800 |
| `3` | 9600 |
| `4` | 19200 |
| `5` | 38400 |
| `6` | 57600 |
| `7` | 115200 |

### `PARITY_OPTIONS`

| Index | Label |
|-------|-------|
| `0` | None |
| `1` | Even |
| `2` | Odd |
| `3` | Mark |
| `4` | Space |

### `DATA_BITS_OPTIONS`

| Index | Label |
|-------|-------|
| `0` | 7 bits |
| `1` | 8 bits |
