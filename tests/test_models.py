"""Tests for hw_vx_config.models."""

from dataclasses import fields

from hw_vx_config.models import DeviceConfig, SearchResult


class TestSearchResult:
    """Tests for the SearchResult dataclass."""

    def test_defaults(self) -> None:
        r = SearchResult()
        assert r.mac_address == ""
        assert r.port_number == ""
        assert r.ip_address == ""
        assert r.username == ""
        assert r.device_name == ""

    def test_construction(self, sample_search_result: SearchResult) -> None:
        assert sample_search_result.ip_address == "192.168.1.100"
        assert sample_search_result.mac_address == "AA:BB:CC:DD:EE:FF"

    def test_equality(self) -> None:
        a = SearchResult(mac_address="AA", ip_address="1.2.3.4")
        b = SearchResult(mac_address="AA", ip_address="1.2.3.4")
        assert a == b

    def test_inequality(self) -> None:
        a = SearchResult(mac_address="AA")
        b = SearchResult(mac_address="BB")
        assert a != b


class TestDeviceConfig:
    """Tests for the DeviceConfig dataclass."""

    def test_defaults_all_empty_strings(self) -> None:
        cfg = DeviceConfig()
        for f in fields(cfg):
            assert getattr(cfg, f.name) == "", f"Field {f.name} should default to ''"

    def test_field_count(self) -> None:
        """Ensure we haven't accidentally lost fields during refactoring."""
        assert len(fields(DeviceConfig())) == 22

    def test_construction(self, sample_config: DeviceConfig) -> None:
        assert sample_config.ip_address == "192.168.1.100"
        assert sample_config.baud_rate == "3"
        assert sample_config.subnet_mask == "255.255.255.0"
