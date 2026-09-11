# Documentation

`hw-vx-config` is a thin CLI over the `uhfreader18.hwvx` sub-package. All
HW-VX protocol code (transport, device flows, config models, setting codes,
enums) lives in the library; this package only adds the command-line
interface and its display formatting.

## API Reference

| Module | Description |
|---|---|
| [`cli`](api/cli.md) | Command-line interface — interactive menu & sub-commands |
| [`formatting`](api/formatting.md) | Pretty-print helpers for configuration output |

The HW-VX protocol API (`HwVxDevice`, `HwVxNetworking`, `DeviceConfig`,
`SearchResult`, setting codes, enums) is documented in the library:
[uhfreader18 `docs/HWVX.md`](https://github.com/xynogen/uhfreader18/blob/main/docs/HWVX.md).

## Architecture

```
┌──────────────────────────────────────────────────┐
│               hw_vx_config.cli                   │  ← argparse + interactive menu
│               hw_vx_config.formatting            │  ← display helpers
├──────────────────────────────────────────────────┤
│               uhfreader18.hwvx                   │  ← all HW-VX protocol
│  HwVxDevice · HwVxNetworking · DeviceConfig ·    │
│  SearchResult · SETTINGS · enums                 │
└──────────────────────────────────────────────────┘
```

The HW-VX UDP setting protocol (command flow, frame layout, enums) is
documented in the library — see
[uhfreader18 `docs/HWVX.md`](https://github.com/xynogen/uhfreader18/blob/main/docs/HWVX.md).
