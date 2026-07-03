"""
Example: UHF RFID reader commands via the binary protocol.

Connects to the HW-VX module's TCP port and sends UHFReader18
binary commands to get reader info and change the reader address.

Usage:
    python examples/rfid_usage.py
"""

from hw_vx_config.rfid import RfidClient

READER_IP = "192.168.1.100"
READER_PORT = 2077  # TCP port from the device's network config


def main() -> None:
    with RfidClient(READER_IP, READER_PORT) as client:
        # Get reader information
        info = client.get_reader_info(adr=0x00)
        print(f"Address:  0x{info.address:02X}")
        print(f"Firmware: v{info.version}")
        print(f"Power:    {info.power} dBm")
        print(f"Scan Time: {info.scan_time * 100} ms")

        # Change reader address from 0x00 to 0x01
        client.set_address(current_adr=0x00, new_adr=0x01)
        print("Address changed to 0x01")

        # Verify by reading info with the new address
        info = client.get_reader_info(adr=0x01)
        print(f"New address: 0x{info.address:02X}")


if __name__ == "__main__":
    main()
