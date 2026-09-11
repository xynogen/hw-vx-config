# Changelog

## 3.0.0

- Move all HW-VX network protocol into the `uhfreader18.hwvx` sub-package.
- **Breaking:** remove the `hw_vx_config.models`, `hw_vx_config.transport`, and
  `hw_vx_config.device` modules. Import `DeviceConfig`, `SearchResult`,
  `HwVxNetworking`, and `HwVxDevice` from `uhfreader18.hwvx` (they remain
  re-exported from the `hw_vx_config` top-level for convenience).
- Require `uhfreader18>=0.4,<0.5`.
- Derive the CLI's display option maps from the library enums.
- Decode reader-info bytes through the `uhfreader18` enums.

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
