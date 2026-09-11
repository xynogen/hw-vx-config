"""Tests for hw_vx_config.formatting."""

from uhfreader18 import Protocol, ReaderType
from uhfreader18.hwvx import DeviceConfig

from hw_vx_config.formatting import (
    Box,
    fmt_mac,
    fmt_protocol,
    fmt_reader_type,
    format_config,
)


class TestFmtMac:
    def test_decimal_dot_to_colon_hex(self) -> None:
        assert fmt_mac("0.34.112.0.166.237") == "00:22:70:00:A6:ED"

    def test_zero_padded(self) -> None:
        assert fmt_mac("0.0.0.0.0.1") == "00:00:00:00:00:01"

    def test_max_values(self) -> None:
        assert fmt_mac("255.255.255.255.255.255") == "FF:FF:FF:FF:FF:FF"

    def test_invalid_returns_raw(self) -> None:
        """Non-numeric input should pass through unchanged."""
        assert fmt_mac("AA:BB:CC:DD:EE:FF") == "AA:BB:CC:DD:EE:FF"

    def test_empty_string_returns_empty(self) -> None:
        assert fmt_mac("") == ""


class TestFmtReaderType:
    def test_known(self) -> None:
        assert fmt_reader_type(ReaderType.UHFREADER18) == "UHFReader18"

    def test_unknown(self) -> None:
        assert fmt_reader_type(None) == "Unknown"


class TestFmtProtocol:
    def test_both_protocols(self) -> None:
        both = Protocol.ISO18000_6C | Protocol.ISO18000_6B
        assert fmt_protocol(both) == "18000-6C + 18000-6B"

    def test_6c_only(self) -> None:
        assert fmt_protocol(Protocol.ISO18000_6C) == "18000-6C"

    def test_6b_only(self) -> None:
        assert fmt_protocol(Protocol.ISO18000_6B) == "18000-6B"

    def test_none(self) -> None:
        assert fmt_protocol(Protocol(0)) == "none"


class TestFormatConfig:
    def test_contains_all_sections(self, sample_config: DeviceConfig) -> None:
        output = format_config(sample_config)
        assert "NETWORK SETTINGS" in output
        assert "SERIAL SETTINGS" in output
        assert "ADVANCED SETTINGS" in output

    def test_contains_ip_address(self, sample_config: DeviceConfig) -> None:
        output = format_config(sample_config)
        assert "192.168.1.100" in output

    def test_contains_formatted_options(self, sample_config: DeviceConfig) -> None:
        output = format_config(sample_config)
        assert "UDP" in output  # protocol enum name
        assert "SERVER" in output  # work_mode enum name
        assert "9600" in output  # baud_rate bps

    def test_box_drawing_present(self, sample_config: DeviceConfig) -> None:
        output = format_config(sample_config)
        assert "╔" in output
        assert "╚" in output
        assert "║" in output

    def test_default_config_formats_without_error(self) -> None:
        """Even a blank config should render cleanly."""
        output = format_config(DeviceConfig())
        assert "NETWORK SETTINGS" in output


class TestBoxOverflow:
    """Box must expand to fit long values without breaking borders."""

    def test_long_value_stays_inside_border(self) -> None:
        long_val = "A" * 80
        rendered = Box().row("Name", long_val).render()
        for line in rendered.strip().splitlines():
            # Every content line must end with ║
            stripped = line.strip()
            assert stripped.endswith("║") or stripped.endswith("╗") or stripped.endswith("╝")

    def test_long_item_stays_inside_border(self) -> None:
        long_text = "B" * 80
        rendered = Box().item(long_text).render()
        for line in rendered.strip().splitlines():
            stripped = line.strip()
            assert stripped.endswith("║") or stripped.endswith("╗") or stripped.endswith("╝")

    def test_long_header_stays_inside_border(self) -> None:
        long_hdr = "C" * 80
        rendered = Box().hdr(long_hdr).render()
        for line in rendered.strip().splitlines():
            stripped = line.strip()
            assert stripped.endswith("║") or stripped.endswith("╗") or stripped.endswith("╝")

    def test_mixed_long_content(self) -> None:
        """Mix of short labels + long values should all fit."""
        rendered = (
            Box()
            .hdr("SHORT HEADER")
            .div()
            .row("Short", "val")
            .row("Name", "X" * 100)
            .item("Y" * 90)
            .render()
        )
        for line in rendered.strip().splitlines():
            stripped = line.strip()
            assert (
                stripped.endswith("║")
                or stripped.endswith("╗")
                or stripped.endswith("╝")
                or stripped.endswith("╣")
            )

    def test_short_content_uses_minimum_width(self) -> None:
        """Short content should still respect _MIN_INNER."""
        rendered = Box().row("A", "B").render()
        # Top border line: indent + ╔ + ═*inner + ╗
        top_line = rendered.strip().splitlines()[0].strip()
        border_width = top_line.count("═")
        assert border_width >= Box._MIN_INNER
