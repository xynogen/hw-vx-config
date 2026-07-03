# Documentation

## API Reference

Detailed reference for every module in the `hw_vx_config` package.

| Module | Description |
|---|---|
| [`constants`](api/constants.md) | Protocol constants, setting codes, and option look-up tables |
| [`models`](api/models.md) | `SearchResult` and `DeviceConfig` dataclasses |
| [`transport`](api/transport.md) | Low-level UDP socket transport (`HwVxNetworking`) |
| [`device`](api/device.md) | High-level device operations (`HwVxDevice`) |
| [`formatting`](api/formatting.md) | Pretty-print helpers for configuration output |
| [`cli`](api/cli.md) | Command-line interface — interactive menu & sub-commands |
| [`protocol`](api/protocol.md) | TCP port 2077 RFID binary protocol — frame layout, CRC, keepalive |

## Architecture

```
┌──────────────────────────────────────────────────┐
│                    cli.py                        │  ← user-facing (argparse + interactive menu)
│                                                  │
├──────────────────────────────────────────────────┤
│                  device.py                       │  ← high-level API
│     (connect, get_config, save_config, …)        │
├──────────────────────────────────────────────────┤
│                transport.py                      │  ← low-level UDP
│   (send, receive, request, request_single,       │
│    search)                                       │
├──────────────────────────────────────────────────┤
│          constants.py  │  models.py              │  ← shared data
│  (codes, option maps)  │  (dataclasses)          │
└──────────────────────────────────────────────────┘
```

## Protocol Overview

All communication uses **UDP on port 65535**. Commands are ASCII strings.

### Command Flow

```
Client                          Device
  │                               │
  │──── X (broadcast) ───────────>│  Search / Echo
  │<─── A{mac}/{port}/… ─────────│  Reply
  │                               │
  │──── W{mac} ──────────────────>│  Select
  │<─── A… ──────────────────────│
  │                               │
  │──── L ───────────────────────>│  Login
  │<─── A… ──────────────────────│
  │                               │
  │──── G{code}|{seq} ───────────>│  Get setting
  │<─── A{value}|{seq} ──────────│
  │                               │
  │──── S{code}{value}|{seq} ────>│  Set setting
  │<─── A… ──────────────────────│
  │                               │
  │──── E ───────────────────────>│  Reboot
  │                               │
```

All replies are prefixed with `A`. The `|{seq}` suffix is a sequence
token used by `request_single` to match replies to requests.
