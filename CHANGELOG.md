# Changelog

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
