"""Tests for the agriculture sector module."""

import pytest
from src.agriculture import (
    AgricultureConfig,
    consommation_actuelle_twh,
    consommation_electrifiee_twh,
    production_agricole_twh,
    consommation_mensuelle_twh,
    bilan_agriculture,
    resume_agriculture,
)


class TestAgricultureConfig:
    """Tests for AgricultureConfig defaults."""

    def test_total_current_reasonable(self):
        config = AgricultureConfig()
        total = (config.machinisme_twh + config.serres_twh +
                 config.irrigation_twh + config.elevage_twh + config.autres_twh)
        assert 40 < total < 60

    def test_seasonal_profile_has_all_months(self):
        config = AgricultureConfig()
        assert len(config.profil_mensuel) >= 11  # At least 11 unique months

    def test_electrification_fractions_valid(self):
        config = AgricultureConfig()
        assert 0 <= config.machinisme_electrifiable_fraction <= 1
        assert 0 <= config.serres_pac_fraction <= 1


class TestConsommationActuelle:
    """Tests for current consumption calculation."""

    def test_total_matches_sum(self):
        result = consommation_actuelle_twh()
        expected = (result['machinisme_twh'] + result['serres_twh'] +
                    result['irrigation_twh'] + result['elevage_twh'] +
                    result['autres_twh'])
        assert result['total_twh'] == pytest.approx(expected)

    def test_all_positive(self):
        result = consommation_actuelle_twh()
        for v in result.values():
            assert v >= 0


class TestConsommationElectrifiee:
    """Tests for electrified consumption."""

    def test_less_than_current(self):
        """Electrification should reduce total energy consumption."""
        actuel = consommation_actuelle_twh()
        electrifie = consommation_electrifiee_twh()
        assert electrifie['total_elec_twh'] < actuel['total_twh']

    def test_residual_fossil(self):
        """Some machinery remains fossil."""
        result = consommation_electrifiee_twh()
        assert result['machinisme_fossile_residuel_twh'] > 0

    def test_pac_reduces_greenhouses(self):
        """Heat pumps reduce greenhouse electricity need."""
        config = AgricultureConfig()
        result = consommation_electrifiee_twh(config)
        assert result['serres_elec_twh'] < config.serres_twh


class TestProductionAgricole:
    """Tests for agricultural energy production."""

    def test_agrivoltaics_significant(self):
        result = production_agricole_twh()
        assert result['agrivoltaisme_twh'] > 50

    def test_methanisation_potential(self):
        result = production_agricole_twh()
        assert result['methanisation_potentiel_twh'] > result['methanisation_actuel_twh']

    def test_total_positive(self):
        result = production_agricole_twh()
        assert result['total_production_twh'] > 0


class TestConsommationMensuelle:
    """Tests for monthly consumption."""

    def test_summer_higher(self):
        """Summer months should have higher agricultural consumption."""
        july = consommation_mensuelle_twh('Juillet')
        january = consommation_mensuelle_twh('Janvier')
        assert july > january

    def test_annual_sum_matches(self):
        """Monthly values should sum to annual total."""
        config = AgricultureConfig()
        mois = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
        total_monthly = sum(consommation_mensuelle_twh(m, config) for m in mois)
        elec = consommation_electrifiee_twh(config)
        assert total_monthly == pytest.approx(elec['total_elec_twh'], rel=0.05)


class TestBilanAgriculture:
    """Tests for agricultural balance."""

    def test_net_producer(self):
        """Agriculture should be a net energy producer with agrivoltaics."""
        bilan = bilan_agriculture()
        assert bilan['bilan_net_twh'] > 0

    def test_reduction_positive(self):
        bilan = bilan_agriculture()
        assert bilan['reduction_conso_twh'] > 0


class TestResumeAgriculture:
    """Tests for summary output."""

    def test_returns_string(self):
        assert isinstance(resume_agriculture(), str)

    def test_contains_sections(self):
        result = resume_agriculture()
        assert "Machinisme" in result
        assert "Agrivoltaïsme" in result or "Agrivolta" in result
        assert "TWh" in result
