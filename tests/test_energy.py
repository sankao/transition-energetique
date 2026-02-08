"""Tests for the energy calculation module."""

import pytest
from src.energy import (
    calculer_energie_twh,
    calculer_deficit_kw,
    calculer_surplus_kw,
    kw_to_gw,
    gw_to_kw,
)
from src.config import EnergyModelConfig


class TestCalculerEnergieTwh:
    """Tests for the main energy calculation function."""

    def test_zero_deficit_returns_zero(self):
        """No deficit means no gas needed."""
        assert calculer_energie_twh(0, 5) == 0.0
        assert calculer_energie_twh(-1000, 5) == 0.0

    def test_known_calculation(self):
        """Verify against known example from the model."""
        # January 8h-13h: 85.3 GW deficit × 5h × 30 days = 12.795 TWh
        deficit_kw = 85_300_000  # 85.3 GW in kW
        duree_h = 5
        expected = 12.795  # TWh

        result = calculer_energie_twh(deficit_kw, duree_h)
        assert abs(result - expected) < 0.001

    def test_formula_components(self):
        """Verify the formula: Q × R × 30 / 1e9."""
        deficit_kw = 1_000_000_000  # 1 TW (1e9 kW)
        duree_h = 1
        # Expected: 1e9 × 1 × 30 / 1e9 = 30 TWh
        assert calculer_energie_twh(deficit_kw, duree_h) == 30.0

    def test_custom_config_days_per_month(self):
        """Test with custom days per month configuration."""
        config = EnergyModelConfig()
        config.temporal.jours_par_mois = 31

        deficit_kw = 1_000_000_000
        duree_h = 1
        # Expected: 1e9 × 1 × 31 / 1e9 = 31 TWh
        result = calculer_energie_twh(deficit_kw, duree_h, config)
        assert result == 31.0


class TestDeficitSurplus:
    """Tests for deficit and surplus calculations."""

    def test_deficit_positive_when_consumption_higher(self):
        """Deficit is positive when consumption > production."""
        assert calculer_deficit_kw(100, 150) == 50

    def test_deficit_zero_when_production_higher(self):
        """Deficit is zero when production >= consumption."""
        assert calculer_deficit_kw(150, 100) == 0
        assert calculer_deficit_kw(100, 100) == 0

    def test_surplus_positive_when_production_higher(self):
        """Surplus is positive when production > consumption."""
        assert calculer_surplus_kw(150, 100) == 50

    def test_surplus_zero_when_consumption_higher(self):
        """Surplus is zero when consumption >= production."""
        assert calculer_surplus_kw(100, 150) == 0
        assert calculer_surplus_kw(100, 100) == 0


class TestUnitConversions:
    """Tests for unit conversion functions."""

    def test_kw_to_gw(self):
        assert kw_to_gw(1_000_000) == 1.0
        assert kw_to_gw(500_000) == 0.5

    def test_gw_to_kw(self):
        assert gw_to_kw(1.0) == 1_000_000
        assert gw_to_kw(0.5) == 500_000

    def test_roundtrip_conversion(self):
        """Converting back and forth should preserve value."""
        original = 42.5
        assert kw_to_gw(gw_to_kw(original)) == original
