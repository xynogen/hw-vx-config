# RFID Reader — TCP Push Protocol (Port 2077)

The reader initiates a TCP connection to the host on port **2077** and pushes tag reports autonomously. The host only sends TCP ACKs — no commands are issued over this channel.

See `DOCUMENTATION.md` for the full command/response protocol (RS232/RS485).

## Tag Report Frame (18 bytes)

| Offset | Field | Value |
|--------|-------|-------|
| 0 | Len | `0x11` — 17 remaining bytes |
| 1 | Adr | Reader address (default `0x00`) |
| 2 | reCmd | `0xEE` — tag report |
| 3 | Status | `0x00` — success |
| 4–15 | EPC | 8-byte EPC + 4 zero padding |
| 16 | CRC-16 LSB | CRC low byte |
| 17 | CRC-16 MSB | CRC high byte |

## CRC-16 Verification

CRC-16/CCITT reflected, computed over bytes 0–15 (Len through EPC). Stored little-endian.

```
PRESET_VALUE = 0xFFFF
POLYNOMIAL   = 0x8408
```

A frame is valid when CRC computed over all 18 bytes yields `0x0000`.
