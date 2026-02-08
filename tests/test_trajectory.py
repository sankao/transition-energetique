"""Tests for the deployment trajectory module."""

import pytest
from src.trajectory import (
    TrajectoryConfig,
    logistic,
    capacite_solaire_gwc,
    penetration_pac,
    cout_solaire_eur_kw,
    cout_batterie_eur_kwh,
    gaz_backup_twh,
    calculer_trajectoire,
    resume_trajectoire,
)


class TestLogistic:
    """Tests for the logistic S-curve function."""

    def test_midpoint_is_half(self):
        assert logistic(2035, 2035, 0.35) == pytest.approx(0.5)

    def test_monotonic_increasing(self):
        values = [logistic(y, 2035, 0.35) for y in range(2020, 2051)]
        for i in range(len(values) - 1):
            assert values[i + 1] > values[i]

    def test_bounded_zero_one(self):
        for y in range(2000, 2060):
            v = logistic(y, 2035, 0.35)
            assert 0 < v < 1

    def test_steepness_effect(self):
        """Higher steepness = more concentrated around midpoint."""
        gentle = logistic(2030, 2035, 0.2)
        steep = logistic(2030, 2035, 0.5)
        # Further from midpoint, steeper curve gives lower value
        assert steep < gentle


class TestCapaciteSolaire:
    """Tests for solar capacity deployment."""

    def test_start_at_current(self):
        config = TrajectoryConfig()
        assert capacite_solaire_gwc(2024, config) == config.solaire_actuel_gwc

    def test_end_at_target(self):
        config = TrajectoryConfig()
        assert capacite_solaire_gwc(2050, config) == config.solaire_cible_gwc

    def test_monotonic_increasing(self):
        config = TrajectoryConfig()
        prev = 0
        for y in range(2024, 2051):
            v = capacite_solaire_gwc(y, config)
            assert v >= prev
            prev = v

    def test_midpoint_roughly_half(self):
        """Around midpoint, capacity should be roughly halfway."""
        config = TrajectoryConfig()
        mid = capacite_solaire_gwc(config.solaire_midpoint, config)
        halfway = (config.solaire_actuel_gwc + config.solaire_cible_gwc) / 2
        assert abs(mid - halfway) / halfway < 0.15  # Within 15%

    def test_before_start_returns_current(self):
        config = TrajectoryConfig()
        assert capacite_solaire_gwc(2020, config) == config.solaire_actuel_gwc


class TestPenetrationPac:
    """Tests for heat pump penetration."""

    def test_start_at_current(self):
        config = TrajectoryConfig()
        assert penetration_pac(2024, config) == config.pac_actuel_fraction

    def test_end_at_target(self):
        config = TrajectoryConfig()
        assert penetration_pac(2050, config) == config.pac_cible_fraction

    def test_monotonic(self):
        config = TrajectoryConfig()
        prev = 0
        for y in range(2024, 2051):
            v = penetration_pac(y, config)
            assert v >= prev
            prev = v


class TestCoutSolaire:
    """Tests for solar cost learning curve."""

    def test_decreasing_over_time(self):
        config = TrajectoryConfig()
        cost_2024 = cout_solaire_eur_kw(2024, config)
        cost_2050 = cout_solaire_eur_kw(2050, config)
        assert cost_2050 < cost_2024

    def test_starts_at_current(self):
        config = TrajectoryConfig()
        cost = cout_solaire_eur_kw(2024, config)
        assert cost == pytest.approx(config.solaire_cout_actuel_eur_kw, rel=0.05)

    def test_positive(self):
        config = TrajectoryConfig()
        for y in range(2024, 2051):
            assert cout_solaire_eur_kw(y, config) > 0


class TestCoutBatterie:
    """Tests for battery cost learning curve."""

    def test_decreasing_over_time(self):
        config = TrajectoryConfig()
        cost_2024 = cout_batterie_eur_kwh(2024, config)
        cost_2050 = cout_batterie_eur_kwh(2050, config)
        assert cost_2050 < cost_2024

    def test_starts_at_current(self):
        config = TrajectoryConfig()
        cost = cout_batterie_eur_kwh(2024, config)
        assert cost == pytest.approx(config.batterie_cout_actuel_eur_kwh, rel=0.01)

    def test_significant_reduction(self):
        """Battery costs should drop substantially over 26 years."""
        config = TrajectoryConfig()
        cost_2024 = cout_batterie_eur_kwh(2024, config)
        cost_2050 = cout_batterie_eur_kwh(2050, config)
        reduction = (cost_2024 - cost_2050) / cost_2024
        assert reduction > 0.40  # At least 40% reduction


class TestGazBackup:
    """Tests for gas backup estimation."""

    def test_at_500_gwc(self):
        """At 500 GWc, gas should be ~114 TWh."""
        result = gaz_backup_twh(500.0)
        assert abs(result - 114.0) < 20  # Within 20 TWh

    def test_decreases_with_solar(self):
        assert gaz_backup_twh(700.0) < gaz_backup_twh(500.0)

    def test_zero_at_high_capacity(self):
        assert gaz_backup_twh(1000.0) == 0.0

    def test_non_negative(self):
        for gwc in range(0, 1500, 100):
            assert gaz_backup_twh(float(gwc)) >= 0.0


class TestCalculerTrajectoire:
    """Tests for full trajectory calculation."""

    def test_correct_length(self):
        config = TrajectoryConfig()
        traj = calculer_trajectoire(config)
        expected = config.annee_fin - config.annee_debut + 1
        assert len(traj) == expected

    def test_first_year(self):
        traj = calculer_trajectoire()
        assert traj[0]['annee'] == 2024

    def test_last_year(self):
        traj = calculer_trajectoire()
        assert traj[-1]['annee'] == 2050

    def test_solar_reaches_target(self):
        traj = calculer_trajectoire()
        assert traj[-1]['solaire_gwc'] == 500.0

    def test_cumulative_investment_positive(self):
        traj = calculer_trajectoire()
        assert traj[-1]['cumul_invest_eur_b'] > 0

    def test_cumulative_emissions_positive(self):
        traj = calculer_trajectoire()
        assert traj[-1]['cumul_emissions_evitees_mt'] > 0

    def test_all_fields_present(self):
        traj = calculer_trajectoire()
        expected_keys = [
            'annee', 'solaire_gwc', 'solaire_ajout_gwc', 'pac_fraction',
            'cout_solaire_eur_kw', 'cout_batterie_eur_kwh', 'gaz_backup_twh',
            'invest_solaire_eur_b', 'cout_gaz_annuel_eur_b', 'cumul_invest_eur_b',
            'emissions_gaz_mt', 'emissions_evitees_mt', 'cumul_emissions_evitees_mt',
        ]
        for key in expected_keys:
            assert key in traj[0]


class TestResumeTrajectoire:
    """Tests for trajectory summary."""

    def test_returns_string(self):
        assert isinstance(resume_trajectoire(), str)

    def test_contains_milestones(self):
        result = resume_trajectoire()
        assert "2030" in result
        assert "2050" in result

    def test_contains_learning_curves(self):
        result = resume_trajectoire()
        assert "€/kW" in result
        assert "€/kWh" in result
