# `hw_vx_config.models`

Data models for search results and device configuration.

**Source:** [`src/hw_vx_config/models.py`](../../src/hw_vx_config/models.py)

---

## `SearchResult`

```python
@dataclass
class SearchResult:
    mac_address: str = ""
    port_number: str = ""
    ip_address: str = ""
    username: str = ""
    device_name: str = ""
```

Represents a single device discovered during a broadcast search.

Returned by [`HwVxNetworking.search()`](transport.md#hwvxnetworkingsearch) and
[`HwVxDevice.connect()`](device.md#hwvxdeviceconnect).

---

## `DeviceConfig`

```python
@dataclass
class DeviceConfig:
    # Network
    username: str           # Login username
    device_name: str        # Friendly device name
    mac_address: str        # Hardware MAC (read-only)
    ip_address: str         # Device IP
    port_number: str        # Listening port
    protocol: str           # 0=UDP, 1=TCP  (index into PROTOCOL_OPTIONS)
    work_mode: str          # 0=Server, 1=Client  (index into WORK_MODE_OPTIONS)
    remote_ip: str          # Remote/target IP (client mode)
    remote_port: str        # Remote/target port (client mode)
    gateway_ip: str         # Default gateway
    subnet_mask: str        # Subnet mask
    dhcp: str               # 0=Disabled, 1=Enabled

    # Serial
    baud_rate: str          # 0=1200 … 7=115200  (index into BAUD_RATE_OPTIONS)
    parity: str             # 0=None … 4=Space  (index into PARITY_OPTIONS)
    data_bits: str          # 0=7bits, 1=8bits  (index into DATA_BITS_OPTIONS)
    dtr_mode: str           # 0=Disabled, 1=Enabled
    rts: str                # 0=Disabled, 1=Enabled

    # Advanced
    connection_mode: str    # 0=Immediately, 1=Connect-with-data
    connection_timeout: str # Timeout in seconds
    reconnect: str          # Auto-reconnect setting
    max_length: str         # Max packet length
    max_delay: str          # Max inter-packet delay
```

All 22 settings that can be read/written via the UDP protocol. Every field
defaults to `""`. Numeric options are stored as string indices — use the
look-up maps in [`constants`](constants.md) to resolve human-readable labels.

Returned by [`HwVxDevice.get_config()`](device.md#hwvxdeviceget_config) and
accepted by [`HwVxDevice.save_config()`](device.md#hwvxdevicesave_config).
