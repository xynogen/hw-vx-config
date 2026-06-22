"""
Example: using hw-vx-config as a library.

Install first:
    pip install hw-vx-config

Or from source:
    pip install -e .
"""

from hw_vx_config import HwVxDevice, HwVxNetworking

# ── 1. Discover all readers on the network ───────────────────────────

net = HwVxNetworking("255.255.255.255")
results = net.search()
net.close()

for r in results:
    print(f"Found: {r.ip_address}  MAC={r.mac_address}  name={r.device_name}")

# ── 2. Read config from a known IP ───────────────────────────────────

with HwVxDevice("10.10.23.241") as dev:
    dev.connect()
    cfg = dev.get_config()

print(cfg.ip_address)  # "10.10.23.241"
print(cfg.mac_address)  # raw decimal-dot, e.g. "0.34.112.0.167.227"
print(cfg.baud_rate)  # index string, e.g. "6" → 57600

# ── 3. Change a setting and save ─────────────────────────────────────

with HwVxDevice("10.10.23.241") as dev:
    dev.connect()
    cfg = dev.get_config()

    cfg.remote_ip = "10.10.36.58"
    cfg.remote_port = "2077"
    cfg.work_mode = "1"  # 1 = Client

    dev.save_config(cfg)  # writes all settings and reboots the reader

# ── 4. Quick operations ───────────────────────────────────────────────

with HwVxDevice("10.10.23.241") as dev:
    dev.connect()
    dev.change_ip("10.10.23.100")  # change IP and reboot

with HwVxDevice("10.10.23.100") as dev:
    dev.connect()
    dev.set_dhcp(True)  # enable DHCP and reboot

with HwVxDevice("10.10.23.100") as dev:
    dev.connect()
    dev.reboot()
