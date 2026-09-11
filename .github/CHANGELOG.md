# Changelog

## 3.0.0

- Move all HW-VX network protocol into the `uhfreader18.hwvx` sub-package.
- **Breaking:** remove the `hw_vx_config.models`, `hw_vx_config.transport`, and
  `hw_vx_config.device` modules. Import `DeviceConfig`, `SearchResult`,
  `HwVxNetworking`, and `HwVxDevice` from `uhfreader18.hwvx` (they remain
  re-exported from the `hw_vx_config` top-level for convenience).
- Require `uhfreader18>=0.6,<0.7`.
- **Breaking:** adopt the library's fully-typed models. `DeviceConfig` fields
  are real types (`IPv4Address`, `int`, and the module `IntEnum`s) instead of
  wire strings; assign enum members and `IPv4Address` values directly.
- Replace the string-based `ui.ask()` and hand-rolled validators with typed
  prompts (`ask_ip`, `ask_port`, `ask_enum`, `ask_text`) that parse and return
  the field's real type; `IPv4Address()` is the IP validator.
- Drop the `hw_vx_config.constants` option maps and the `fmt_option` helper —
  enums render their own names, so no index-to-label tables to keep in sync.
- Decode reader-info through the `uhfreader18` enums
  (`ReaderInfo.reader_model`, `ReaderInfo.protocols`).

### Migration

```python
# hw-vx-config 2.x
from hw_vx_config.models import DeviceConfig, SearchResult
from hw_vx_config.transport import HwVxNetworking
from hw_vx_config.device import HwVxDevice

# hw-vx-config 3.x
from uhfreader18.hwvx import DeviceConfig, SearchResult, HwVxNetworking, HwVxDevice
```

## 2.0.0

- Move `RfidClient` and UHFReader18 protocol ownership to the `uhfreader18` package.
- Add runtime dependency `uhfreader18>=0.1,<0.2`.
- Remove `hw_vx_config.RfidClient` and `hw_vx_config.rfid`.
- Keep RFID CLI commands backed by `uhfreader18.RfidClient`.

### Migration

```python
# hw-vx-config 1.x
from hw_vx_config import RfidClient

# hw-vx-config 2.x
from uhfreader18 import RfidClient
```
