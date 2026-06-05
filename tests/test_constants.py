"""Tests for hw_vx_config.constants."""

from hw_vx_config.constants import (
    BAUD_RATE_OPTIONS,
    DATA_BITS_OPTIONS,
    DHCP_OPTIONS,
    PARITY_OPTIONS,
    PROTOCOL_OPTIONS,
    SETTINGS,
    TOGGLE_OPTIONS,
    UDP_PORT,
    WORK_MODE_OPTIONS,
)


class TestConstants:
    """Verify protocol constants are sane."""

    def test_udp_port(self) -> None:
        assert UDP_PORT == 65535

    def test_settings_has_expected_keys(self) -> None:
        expected_keys = {
            "ON",
            "DN",
            "FE",
            "IP",
            "PN",
            "TP",
            "RM",
            "DI",
            "DP",
            "GI",
            "NM",
            "DH",
            "BR",
            "PR",
            "BB",
            "DT",
            "FC",
            "CM",
            "CT",
            "RC",
            "ML",
            "MD",
        }
        assert expected_keys == set(SETTINGS.keys())

    def test_baud_rate_options_count(self) -> None:
        assert len(BAUD_RATE_OPTIONS) == 8

    def test_protocol_options(self) -> None:
        assert PROTOCOL_OPTIONS == {0: "UDP", 1: "TCP"}

    def test_work_mode_options(self) -> None:
        assert WORK_MODE_OPTIONS == {0: "Server", 1: "Client"}

    def test_dhcp_options(self) -> None:
        assert DHCP_OPTIONS == {0: "Disabled", 1: "Enabled"}

    def test_parity_options(self) -> None:
        assert len(PARITY_OPTIONS) == 5

    def test_data_bits_options(self) -> None:
        assert DATA_BITS_OPTIONS == {0: "7 bits", 1: "8 bits"}

    def test_toggle_options(self) -> None:
        assert TOGGLE_OPTIONS == {0: "Disabled", 1: "Enabled"}
