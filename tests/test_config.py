"""Tests for the configuration module."""

import pytest
from src.config import (
    EnergyModelConfig,
    TemporalConfig,
    ProductionConfig,
    ConsumptionConfig,
    StorageConfig,
    FinancialConfig,
    DEFAULT_CONFIG,
)


class TestEnergyModelConfig:
    """Tests for the main configuration class."""

    def test_default_config_valid(self):
        """Default configuration should be valid."""
        config = EnergyModelConfig()
        assert config.production.solar_capacity_gwc == 500.0
        assert config.consumption.heat_pump_cop == 2.0
        assert config.storage.battery_efficiency == 0.85

    def test_config_validation_solar_negative(self):
        """Negative solar capacity should raise error."""
        config = EnergyModelConfig()
        config.production.solar_capacity_gwc = -100
        with pytest.raises(ValueError, match="solar_capacity_gwc"):
            config._validate()

    def test_config_validation_cop_out_of_range(self):
        """COP outside valid range should raise error."""
        config = EnergyModelConfig()
        config.consumption.heat_pump_cop = 0.5
        with pytest.raises(ValueError, match="heat_pump_cop"):
            config._validate()

    def test_config_validation_efficiency_out_of_range(self):
        """Battery efficiency outside valid range should raise error."""
        config = EnergyModelConfig()
        config.storage.battery_efficiency = 1.5
        with pytest.raises(ValueError, match="battery_efficiency"):
            config._validate()

    def test_config_summary(self):
        """Summary should include key parameters."""
        config = EnergyModelConfig()
        summary = config.summary()
        assert "500" in summary  # solar capacity
        assert "COP" in summary
        assert "85%" in summary  # battery efficiency


class TestTemporalConfig:
    """Tests for temporal configuration."""

    def test_sunset_times_all_months(self):
        """All 12 months should have sunset times."""
        config = TemporalConfig()
        assert len(config.sunset_times) == 12

    def test_sunset_times_reasonable(self):
        """Sunset times should be reasonable (15-23h)."""
        config = TemporalConfig()
        for month, time in config.sunset_times.items():
            assert 15 <= time <= 23, f"{month} sunset at {time}"

    def test_time_slots_sum_to_24h(self):
        """Time slots should sum to 24 hours."""
        config = TemporalConfig()
        total = sum(config.time_slots.values())
        assert total == 24.0


class TestFinancialConfig:
    """Tests for financial configuration."""

    def test_default_costs_positive(self):
        """All costs should be positive."""
        config = FinancialConfig()
        assert config.gas_cost_eur_per_mwh > 0
        assert config.solar_capex_eur_per_kw > 0
        assert config.storage_capex_eur_per_kwh > 0

    def test_lifetimes_reasonable(self):
        """Asset lifetimes should be reasonable."""
        config = FinancialConfig()
        assert 20 <= config.solar_lifetime_years <= 40
        assert 10 <= config.storage_lifetime_years <= 25


class TestDefaultConfig:
    """Tests for the DEFAULT_CONFIG singleton."""

    def test_default_config_exists(self):
        """DEFAULT_CONFIG should be available."""
        assert DEFAULT_CONFIG is not None

    def test_default_config_is_valid(self):
        """DEFAULT_CONFIG should pass validation."""
        # If it exists, it passed __post_init__ validation
        assert DEFAULT_CONFIG.production.solar_capacity_gwc > 0
