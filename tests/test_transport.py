"""Tests for the transport sector module."""

import pytest
from src.transport import (
    TransportConfig,
    consommation_actuelle_twh,
    consommation_electrifiee_twh,
    facteurs_effectifs,
    demande_recharge_par_plage,
    bilan_transport,
    resume_transport,
)


class TestTransportConfig:
    """Tests for TransportConfig defaults."""

    def test_total_current_reasonable(self):
        """Total transport ~480 TWh matches French reference."""
        config = TransportConfig()
        total = (config.voitures_twh + config.deux_roues_twh + config.bus_cars_twh +
                 config.poids_lourds_twh + config.vul_twh + config.rail_total_twh +
                 config.aviation_domestique_twh + config.aviation_international_twh +
                 config.maritime_twh + config.fluvial_twh)
        assert 400 < total < 550

    def test_electrification_factors_valid(self):
        """All efficiency factors between 0 and 1."""
        config = TransportConfig()
        assert 0 < config.voitures_facteur_electrification < 1
        assert 0 < config.bus_facteur_electrification < 1
        assert 0 < config.pl_batterie_facteur < 1
        assert 0 < config.vul_facteur_electrification < 1

    def test_pl_fractions_sum_to_one(self):
        """PL pathway fractions must sum to 1."""
        config = TransportConfig()
        total = (config.pl_batterie_fraction +
                 config.pl_hydrogene_fraction +
                 config.pl_fossile_residuel_fraction)
        assert total == pytest.approx(1.0)

    def test_charging_profile_sums_to_one(self):
        config = TransportConfig()
        assert sum(config.profil_recharge.values()) == pytest.approx(1.0)

    def test_rail_electric_fraction_valid(self):
        config = TransportConfig()
        assert 0 < config.rail_electrique_fraction <= 1.0


class TestConsommationActuelle:
    """Tests for current consumption."""

    def test_total_matches_sum(self):
        result = consommation_actuelle_twh()
        expected = (result['routier_passagers_twh'] + result['routier_fret_twh'] +
                    result['rail_twh'] + result['aviation_twh'] +
                    result['maritime_fluvial_twh'])
        assert result['total_twh'] == pytest.approx(expected)

    def test_all_positive(self):
        result = consommation_actuelle_twh()
        for v in result.values():
            assert v >= 0

    def test_road_passenger_dominates(self):
        """Road passenger should be largest sub-sector."""
        result = consommation_actuelle_twh()
        assert result['routier_passagers_twh'] > result['routier_fret_twh']
        assert result['routier_passagers_twh'] > result['aviation_twh']

    def test_subtotals_consistent(self):
        result = consommation_actuelle_twh()
        assert result['routier_passagers_twh'] == pytest.approx(
            result['voitures_twh'] + result['deux_roues_twh'] + result['bus_cars_twh'])
        assert result['routier_fret_twh'] == pytest.approx(
            result['poids_lourds_twh'] + result['vul_twh'])
        assert result['aviation_twh'] == pytest.approx(
            result['aviation_domestique_twh'] + result['aviation_international_twh'])


class TestConsommationElectrifiee:
    """Tests for electrified consumption."""

    def test_total_elec_less_than_current(self):
        """Electrification should reduce total energy need."""
        actuel = consommation_actuelle_twh()
        electrifie = consommation_electrifiee_twh()
        assert electrifie['total_elec_twh'] < actuel['total_twh']

    def test_elec_plus_fossil_less_than_current(self):
        """Efficiency gains mean elec + residual < current."""
        actuel = consommation_actuelle_twh()
        electrifie = consommation_electrifiee_twh()
        total_after = electrifie['total_elec_twh'] + electrifie['total_fossile_residuel_twh']
        assert total_after < actuel['total_twh']

    def test_residual_fossil_positive(self):
        """Aviation and heavy trucks ensure residual fossil."""
        result = consommation_electrifiee_twh()
        assert result['total_fossile_residuel_twh'] > 0

    def test_aviation_and_pl_largest_residuals(self):
        """Aviation kerosene and PL are the largest residual fossil sources."""
        result = consommation_electrifiee_twh()
        assert result['aviation_fossile_residuel_twh'] > 30
        assert result['pl_fossile_residuel_twh'] > 30

    def test_rail_mostly_unchanged(self):
        """Rail already mostly electric."""
        config = TransportConfig()
        result = consommation_electrifiee_twh(config)
        assert abs(result['rail_elec_twh'] - config.rail_total_twh) < 5.0

    def test_custom_config_higher_modal_shift(self):
        """Higher modal shift reduces passenger electricity."""
        default = consommation_electrifiee_twh()
        custom = consommation_electrifiee_twh(
            TransportConfig(report_modal_fraction=0.30)
        )
        assert custom['voitures_elec_twh'] < default['voitures_elec_twh']

    def test_all_elec_positive(self):
        result = consommation_electrifiee_twh()
        assert result['voitures_elec_twh'] > 0
        assert result['routier_fret_elec_twh'] > 0
        assert result['rail_elec_twh'] > 0
        assert result['aviation_elec_saf_twh'] > 0


class TestFacteursEffectifs:
    """Tests for backward-compatible factors."""

    def test_passenger_factor_in_range(self):
        result = facteurs_effectifs()
        assert 0.15 < result['facteur_passagers_effectif'] < 0.40

    def test_freight_factor_in_range(self):
        result = facteurs_effectifs()
        assert 0.20 < result['facteur_fret_effectif'] < 0.50

    def test_global_factor_reasonable(self):
        result = facteurs_effectifs()
        assert 0.2 < result['facteur_global_effectif'] < 0.6


class TestBilanTransport:
    """Tests for complete transport balance."""

    def test_reduction_positive(self):
        bilan = bilan_transport()
        assert bilan['reduction_conso_twh'] > 0

    def test_all_keys_present(self):
        bilan = bilan_transport()
        for key in ['conso_actuelle_total_twh', 'conso_electrifiee_twh',
                     'fossile_residuel_twh', 'reduction_conso_twh']:
            assert key in bilan

    def test_energy_conservation(self):
        """current = electrified + residual_fossil + reduction."""
        bilan = bilan_transport()
        reconstructed = (bilan['conso_electrifiee_twh'] +
                         bilan['fossile_residuel_twh'] +
                         bilan['reduction_conso_twh'])
        assert bilan['conso_actuelle_total_twh'] == pytest.approx(reconstructed, rel=0.01)

    def test_fraction_fossile_evitee(self):
        """Most fossil should be avoided."""
        bilan = bilan_transport()
        assert 0.5 < bilan['fraction_fossile_evitee'] < 1.0


class TestDemandeRecharge:
    """Tests for charging profile."""

    def test_all_slots_positive(self):
        config = TransportConfig()
        for plage in config.profil_recharge:
            assert demande_recharge_par_plage(plage, config) > 0

    def test_sum_matches_direct_elec(self):
        """Charging across all slots equals direct road + maritime elec."""
        config = TransportConfig()
        electrifie = consommation_electrifiee_twh(config)
        direct_elec = (electrifie['routier_passagers_elec_twh'] +
                       electrifie['routier_fret_elec_twh'] +
                       electrifie['maritime_elec_twh'] +
                       electrifie['fluvial_elec_twh'])
        total_recharge = sum(
            demande_recharge_par_plage(p, config)
            for p in config.profil_recharge
        )
        assert total_recharge == pytest.approx(direct_elec)

    def test_unknown_slot_returns_zero(self):
        assert demande_recharge_par_plage('invalid') == 0.0


class TestResumeTransport:
    """Tests for summary output."""

    def test_returns_string(self):
        assert isinstance(resume_transport(), str)

    def test_contains_all_modes(self):
        result = resume_transport()
        assert "Voitures" in result
        assert "Poids lourds" in result
        assert "Rail" in result
        assert "Aviation" in result
        assert "TWh" in result

    def test_contains_synthesis(self):
        result = resume_transport()
        assert "SYNTHESE" in result
        assert "Facteur" in result or "facteur" in result.lower()
