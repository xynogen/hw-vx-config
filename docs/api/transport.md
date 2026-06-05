# `hw_vx_config.transport`

Low-level UDP transport for the HW-VX protocol. Direct port of C# `Networking.cs`.

**Source:** [`src/hw_vx_config/transport.py`](../../src/hw_vx_config/transport.py)

---

## `HwVxNetworking`

```python
class HwVxNetworking:
    def __init__(self, ip_address: str = "255.255.255.255") -> None: ...
```

UDP communication with HW-VX6330K / HW-VX6346KL TCP/IP modules.
Supports context manager (`with` statement) for automatic cleanup.

**Parameters:**

| Name | Type | Default | Description |
|---|---|---|---|
| `ip_address` | `str` | `"255.255.255.255"` | Destination IP. Use broadcast for discovery. |

**Example:**

```python
from hw_vx_config.transport import HwVxNetworking

with HwVxNetworking("192.168.1.100") as net:
    reply = net.request("GON|1")
    print(reply)
```

---

### `HwVxNetworking.send`

```python
def send(self, command: str) -> None
```

Send a raw ASCII command packet to the target.

---

### `HwVxNetworking.receive`

```python
def receive(self) -> str
```

Block until a UDP packet arrives or timeout. Returns `""` on timeout.

---

### `HwVxNetworking.request`

```python
def request(self, command: str, retries: int = 5) -> str
```

Send *command* and wait for an `A`-prefixed reply. Returns the reply body
with the `A` prefix stripped.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `command` | `str` | — | Command string to send |
| `retries` | `int` | `5` | Number of send/receive attempts |

**Raises:** `TimeoutError` if no valid reply after all retries.

---

### `HwVxNetworking.request_single`

```python
def request_single(self, command: str, check: str) -> str
```

Send `command|check` and expect `A{value}|{check}` back. Returns just the
*value* portion. Matches the C# `requestSingle` helper.

| Parameter | Type | Description |
|---|---|---|
| `command` | `str` | Command prefix (e.g. `"GON"`) |
| `check` | `str` | Sequence token for reply validation (e.g. `"1"`) |

**Raises:** `ValueError` if the reply doesn't contain the expected check token.

---

### `HwVxNetworking.search`

```python
def search(self) -> list[SearchResult]
```

Broadcast an echo (`X`) and collect all device responses. Each reply has
the form `A{mac}/{port}` from the device's IP. Returns a list of
[`SearchResult`](models.md#searchresult) objects.

---

### `HwVxNetworking.close`

```python
def close(self) -> None
```

Close the underlying socket.
