"""Tests for the industry and tertiary sectors module."""

import pytest
from src.secteurs import (
    IndustrieConfig,
    TertiaireConfig,
    bilan_industrie,
    bilan_tertiaire,
    bilan_tous_secteurs,
    resume_secteurs,
)


class TestIndustrieConfig:
    """Tests for IndustrieConfig defaults."""

    def test_total_reasonable(self):
        config = IndustrieConfig()
        total = (config.chaleur_haute_temp_twh + config.chaleur_moyenne_temp_twh +
                 config.chaleur_basse_temp_twh + config.force_motrice_twh +
                 config.electrochimie_twh + config.autres_twh)
        assert 150 < total < 250

    def test_electrification_fractions_valid(self):
        config = IndustrieConfig()
        assert 0 <= config.haute_temp_electrifiable <= 1
        assert 0 <= config.moyenne_temp_electrifiable <= 1
        assert 0 <= config.basse_temp_electrifiable <= 1


class TestBilanIndustrie:
    """Tests for industrial balance."""

    def test_electrified_less_than_current(self):
        """Electrification + efficiency should reduce total."""
        result = bilan_industrie()
        assert result['total_elec_twh'] < result['actuel_total_twh']

    def test_residual_fossil(self):
        """Some high-temp processes remain fossil."""
        result = bilan_industrie()
        assert result['fossile_residuel_twh'] > 0

    def test_efficiency_gains(self):
        result = bilan_industrie()
        assert result['gain_efficacite_twh'] > 0

    def test_all_keys_present(self):
        result = bilan_industrie()
        expected = ['actuel_total_twh', 'total_elec_twh', 'fossile_residuel_twh',
                    'gain_efficacite_twh']
        for key in expected:
            assert key in result

    def test_custom_config(self):
        config = IndustrieConfig(gain_efficacite_fraction=0.30)
        result = bilan_industrie(config)
        default = bilan_industrie()
        assert result['total_elec_twh'] < default['total_elec_twh']


class TestTertiaireConfig:
    """Tests for TertiaireConfig defaults."""

    def test_total_reasonable(self):
        config = TertiaireConfig()
        total = (config.chauffage_twh + config.climatisation_twh +
                 config.eclairage_twh + config.electricite_specifique_twh +
                 config.eau_chaude_twh + config.autres_twh)
        assert 150 < total < 250


class TestBilanTertiaire:
    """Tests for tertiary balance."""

    def test_electrified_less_than_current(self):
        result = bilan_tertiaire()
        assert result['total_elec_twh'] < result['actuel_total_twh']

    def test_renovation_gains(self):
        result = bilan_tertiaire()
        assert result['gain_renovation_twh'] > 0

    def test_led_gains(self):
        result = bilan_tertiaire()
        assert result['gain_eclairage_twh'] > 0

    def test_climatisation_gains(self):
        result = bilan_tertiaire()
        assert result['gain_climatisation_twh'] > 0

    def test_all_keys_present(self):
        result = bilan_tertiaire()
        expected = ['actuel_total_twh', 'total_elec_twh', 'chauffage_elec_twh',
                    'eclairage_twh', 'gain_renovation_twh']
        for key in expected:
            assert key in result


class TestBilanTousSecteurs:
    """Tests for combined sector balance."""

    def test_total_is_sum(self):
        result = bilan_tous_secteurs()
        expected = result['industrie_actuel_twh'] + result['tertiaire_actuel_twh']
        assert result['total_actuel_twh'] == pytest.approx(expected)

    def test_electrified_total_is_sum(self):
        result = bilan_tous_secteurs()
        expected = result['industrie_elec_twh'] + result['tertiaire_elec_twh']
        assert result['total_elec_twh'] == pytest.approx(expected)

    def test_reduction(self):
        result = bilan_tous_secteurs()
        assert result['total_elec_twh'] < result['total_actuel_twh']


class TestResumeSecteurs:
    """Tests for summary output."""

    def test_returns_string(self):
        assert isinstance(resume_secteurs(), str)

    def test_contains_sections(self):
        result = resume_secteurs()
        assert "INDUSTRIE" in result
        assert "TERTIAIRE" in result
        assert "SYNTHÈSE" in result or "SYNTHESE" in result
        assert "TWh" in result

    def test_contains_key_concepts(self):
        result = resume_secteurs()
        assert "chaleur" in result.lower() or "Chaleur" in result
        assert "PAC" in result or "pac" in result.lower()
