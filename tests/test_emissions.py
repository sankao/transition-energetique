"""Tests for the CO2 emissions module."""

import pytest
from src.emissions import (
    EmissionsConfig,
    emissions_gaz_backup_mt,
    emissions_parc_production_mt,
    emissions_evitees_mt,
    bilan_carbone,
    resume_emissions,
)


class TestEmissionsConfig:
    """Tests for EmissionsConfig defaults."""

    def test_gas_factor_positive(self):
        config = EmissionsConfig()
        assert config.facteur_gaz_tco2_par_mwh > 0

    def test_gas_lower_than_coal(self):
        config = EmissionsConfig()
        assert config.facteur_gaz_tco2_par_mwh < config.facteur_charbon_tco2_par_mwh

    def test_nuclear_much_lower_than_gas(self):
        config = EmissionsConfig()
        assert config.facteur_nucleaire_tco2_par_mwh < config.facteur_gaz_tco2_par_mwh / 10

    def test_france_total_reasonable(self):
        config = EmissionsConfig()
        assert 300 < config.emissions_france_total_mt < 500

    def test_sector_sum_close_to_total(self):
        """Sector emissions should roughly add up to the national total."""
        config = EmissionsConfig()
        sector_sum = (
            config.emissions_transport_mt
            + config.emissions_batiments_mt
            + config.emissions_industrie_mt
            + config.emissions_agriculture_mt
            + config.emissions_energie_mt
            + config.emissions_dechets_mt
        )
        # Within 10% (sectors may overlap or exclude some items)
        assert abs(sector_sum - config.emissions_france_total_mt) / config.emissions_france_total_mt < 0.10


class TestEmissionsGaz:
    """Tests for gas backup emissions."""

    def test_zero_gas_zero_emissions(self):
        assert emissions_gaz_backup_mt(0.0) == 0.0

    def test_114_twh_known_value(self):
        """114 TWh × 0.227 = 25.878 MtCO2."""
        result = emissions_gaz_backup_mt(114.0)
        assert result == pytest.approx(114.0 * 0.227, rel=1e-6)

    def test_scales_linearly(self):
        e1 = emissions_gaz_backup_mt(100.0)
        e2 = emissions_gaz_backup_mt(200.0)
        assert e2 == pytest.approx(2 * e1, rel=1e-6)


class TestEmissionsParc:
    """Tests for production mix emissions."""

    def test_all_sources_present(self):
        result = emissions_parc_production_mt(400, 300, 65, 114)
        assert 'nucleaire_mt' in result
        assert 'solaire_mt' in result
        assert 'hydro_mt' in result
        assert 'gaz_mt' in result
        assert 'total_mt' in result

    def test_total_is_sum(self):
        result = emissions_parc_production_mt(400, 300, 65, 114)
        expected = (
            result['nucleaire_mt']
            + result['solaire_mt']
            + result['hydro_mt']
            + result['gaz_mt']
        )
        assert result['total_mt'] == pytest.approx(expected, rel=1e-6)

    def test_gas_dominates(self):
        """Gas should be the dominant source of emissions in the mix."""
        result = emissions_parc_production_mt(400, 300, 65, 114)
        assert result['gaz_mt'] > result['nucleaire_mt']
        assert result['gaz_mt'] > result['solaire_mt']
        assert result['gaz_mt'] > result['hydro_mt']

    def test_zero_gas_very_low_emissions(self):
        """Without gas, electricity is almost carbon-free."""
        result = emissions_parc_production_mt(400, 300, 65, 0)
        assert result['total_mt'] < 15  # < 15 MtCO2 for ~765 TWh


class TestEmissionsEvitees:
    """Tests for avoided emissions calculation."""

    def test_positive_net_avoided(self):
        """Net avoided emissions should be positive for reasonable gas levels."""
        result = emissions_evitees_mt(114.0)
        assert result['total_evitees_mt'] > 0

    def test_transport_dominates(self):
        """Transport should be the largest source of avoided emissions."""
        result = emissions_evitees_mt(114.0)
        assert result['emissions_evitees_transport_mt'] > result['emissions_evitees_batiments_mt']

    def test_more_gas_less_avoided(self):
        """Higher gas backup means fewer net avoided emissions."""
        low_gas = emissions_evitees_mt(50.0)
        high_gas = emissions_evitees_mt(200.0)
        assert low_gas['total_evitees_mt'] > high_gas['total_evitees_mt']


class TestBilanCarbone:
    """Tests for complete carbon balance."""

    def test_significant_reduction(self):
        """Transition should achieve significant CO2 reduction."""
        bilan = bilan_carbone(114.0)
        assert bilan['reduction_pct'] > 30  # At least 30% reduction

    def test_reduction_consistent(self):
        """Reduction should equal current - scenario."""
        bilan = bilan_carbone(114.0)
        expected = bilan['france_actuelle_mt'] - bilan['scenario_total_mt']
        assert bilan['reduction_mt'] == pytest.approx(expected, rel=1e-6)

    def test_zero_gas_maximum_reduction(self):
        """Zero gas scenario should have higher reduction than 114 TWh."""
        bilan_114 = bilan_carbone(114.0)
        bilan_0 = bilan_carbone(0.0)
        assert bilan_0['reduction_pct'] > bilan_114['reduction_pct']

    def test_vs_targets_present(self):
        bilan = bilan_carbone(114.0)
        assert 'vs_objectif_2030_mt' in bilan
        assert 'vs_objectif_2050_mt' in bilan


class TestResumeEmissions:
    """Tests for the summary output."""

    def test_returns_string(self):
        result = resume_emissions()
        assert isinstance(result, str)

    def test_contains_key_sections(self):
        result = resume_emissions()
        assert "MtCO2" in result
        assert "Bilan Carbone" in result
        assert "Réduction" in result
        assert "SNBC" in result

    def test_custom_gas_value(self):
        result = resume_emissions(gaz_twh=50.0)
        assert "50 TWh" in result
