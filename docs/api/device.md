# `hw_vx_config.device`

High-level device operations. Mirrors the C# `Form1.cs` button-click flows.

**Source:** [`src/hw_vx_config/device.py`](../../src/hw_vx_config/device.py)

---

## `HwVxDevice`

```python
class HwVxDevice:
    def __init__(self, ip_address: str) -> None: ...
```

High-level operations for a specific HW-VX reader. Wraps
[`HwVxNetworking`](transport.md#hwvxnetworking) and implements the
search → select → login flow automatically.

Supports context manager (`with` statement) for automatic cleanup.

**Parameters:**

| Name | Type | Description |
|---|---|---|
| `ip_address` | `str` | Current IP address of the target device |

**Example:**

```python
from hw_vx_config import HwVxDevice

with HwVxDevice("192.168.1.100") as dev:
    dev.connect()
    cfg = dev.get_config()
    print(cfg.ip_address, cfg.baud_rate)
```

---

### `HwVxDevice.connect`

```python
def connect(self) -> SearchResult
```

Search for the device, select it (`W{mac}`), and login (`L`).
Returns the [`SearchResult`](models.md#searchresult) for the connected device.

**Raises:** `ConnectionError` if no reader is found at the target IP.

---

### `HwVxDevice.get_config`

```python
def get_config(self) -> DeviceConfig
```

Read all 22 settings from the device. Returns a fully populated
[`DeviceConfig`](models.md#deviceconfig).

Mirrors the C# `configButton_Click` flow — issues 22 sequential
`G{code}` requests.

---

### `HwVxDevice.save_config`

```python
def save_config(self, cfg: DeviceConfig) -> None
```

Write all settings to the device and reboot. Sends the full set-command
sequence via unicast first, then retries via broadcast with `W{mac}` as a
fallback in case the IP changed mid-save.

| Parameter | Type | Description |
|---|---|---|
| `cfg` | [`DeviceConfig`](models.md#deviceconfig) | Configuration to write |

---

### `HwVxDevice.change_ip`

```python
def change_ip(self, new_ip: str) -> None
```

Quick IP address change + reboot. Mirrors the C# `changeIpButton_Click`
flow. Sends via unicast then broadcast fallback.

| Parameter | Type | Description |
|---|---|---|
| `new_ip` | `str` | New IP address to assign |

---

### `HwVxDevice.set_dhcp`

```python
def set_dhcp(self, enabled: bool) -> None
```

Enable or disable DHCP and reboot the device.

| Parameter | Type | Description |
|---|---|---|
| `enabled` | `bool` | `True` to enable, `False` to disable |

---

### `HwVxDevice.reboot`

```python
def reboot(self) -> None
```

Send a reboot command (`E`) to the device.

---

### `HwVxDevice.close`

```python
def close(self) -> None
```

Close the underlying transport.
