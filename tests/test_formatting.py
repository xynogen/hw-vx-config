"""Tests for hw_vx_config.formatting."""

from hw_vx_config.formatting import fmt_mac, fmt_option, format_config
from hw_vx_config.models import DeviceConfig


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


class TestFmtOption:
    def test_known_index(self) -> None:
        assert fmt_option("0", {0: "UDP", 1: "TCP"}) == "0 (UDP)"
        assert fmt_option("1", {0: "UDP", 1: "TCP"}) == "1 (TCP)"

    def test_unknown_index(self) -> None:
        assert fmt_option("9", {0: "UDP", 1: "TCP"}) == "9 (?)"

    def test_non_numeric_value(self) -> None:
        assert fmt_option("abc", {0: "UDP"}) == "abc"

    def test_empty_value(self) -> None:
        assert fmt_option("", {0: "UDP"}) == ""


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
        assert "0 (UDP)" in output  # protocol
        assert "0 (Server)" in output  # work_mode
        assert "3 (9600)" in output  # baud_rate

    def test_box_drawing_present(self, sample_config: DeviceConfig) -> None:
        output = format_config(sample_config)
        assert "╔" in output
        assert "╚" in output
        assert "║" in output

    def test_default_config_formats_without_error(self) -> None:
        """Even a blank config should render cleanly."""
        output = format_config(DeviceConfig())
        assert "NETWORK SETTINGS" in output
