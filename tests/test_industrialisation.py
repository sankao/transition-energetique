"""Tests for the industrialisation module."""

import pytest
from src.industrialisation import (
    IndustrialisationConfig,
    NOMBRE_MAISONS_ELIGIBLES_PAC,
    analyser_besoins_industriels,
    identifier_goulets,
    plan_industrialisation,
    resume_industrialisation,
    _ajout_solaire_annuel_gwc,
    _ajout_pac_annuel_unites,
    _besoin_batterie_gwh,
)
from src.trajectory import TrajectoryConfig


# =========================================================================
# Configuration defaults and validation
# =========================================================================

class TestIndustrialisationConfigDefaults:
    """Tests for IndustrialisationConfig default values."""

    def test_default_pv_factory_capacity(self):
        config = IndustrialisationConfig()
        assert config.capacite_usine_pv_gwc_an == 5.0

    def test_default_pv_factories(self):
        config = IndustrialisationConfig()
        assert config.nb_usines_pv_actuelles == 2

    def test_default_pv_lead_time(self):
        config = IndustrialisationConfig()
        assert config.delai_construction_usine_pv_ans == 2.0

    def test_default_battery_factory_capacity(self):
        config = IndustrialisationConfig()
        assert config.capacite_usine_batterie_gwh_an == 30.0

    def test_default_battery_factories(self):
        config = IndustrialisationConfig()
        assert config.nb_usines_batterie_actuelles == 3

    def test_default_pac_factory_capacity(self):
        config = IndustrialisationConfig()
        assert config.capacite_usine_pac_unites_an == 500_000

    def test_default_pac_factories(self):
        config = IndustrialisationConfig()
        assert config.nb_usines_pac_actuelles == 5

    def test_default_installers_pv(self):
        config = IndustrialisationConfig()
        assert config.installateurs_pv_actuels == 30_000
        assert config.installateurs_pv_par_gwc == 5_000

    def test_default_installers_pac(self):
        config = IndustrialisationConfig()
        assert config.installateurs_pac_actuels == 25_000

    def test_default_silicon_per_kwc(self):
        config = IndustrialisationConfig()
        assert config.silicium_kg_par_kwc == 3.0

    def test_default_lithium_per_kwh(self):
        config = IndustrialisationConfig()
        assert config.lithium_kg_par_kwh == 0.1

    def test_default_copper_per_kwc(self):
        config = IndustrialisationConfig()
        assert config.cuivre_kg_par_kwc == 4.0

    def test_custom_config(self):
        config = IndustrialisationConfig(
            capacite_usine_pv_gwc_an=10.0,
            nb_usines_pv_actuelles=5,
        )
        assert config.capacite_usine_pv_gwc_an == 10.0
        assert config.nb_usines_pv_actuelles == 5

    def test_timeline_defaults(self):
        config = IndustrialisationConfig()
        assert config.annee_debut == 2024
        assert config.annee_fin == 2050

    def test_world_production_references(self):
        config = IndustrialisationConfig()
        assert config.production_mondiale_silicium_kt > 0
        assert config.production_mondiale_lithium_kt > 0
        assert config.production_mondiale_cuivre_kt > 0

    def test_max_world_share(self):
        config = IndustrialisationConfig()
        assert 0 < config.part_max_production_mondiale <= 1.0


# =========================================================================
# Internal helper functions
# =========================================================================

class TestAjoutSolaireAnnuel:
    """Tests for annual solar additions helper."""

    def test_zero_at_start(self):
        traj = TrajectoryConfig()
        assert _ajout_solaire_annuel_gwc(traj.annee_debut, traj) == 0.0

    def test_positive_during_deployment(self):
        traj = TrajectoryConfig()
        ajout = _ajout_solaire_annuel_gwc(2035, traj)
        assert ajout > 0

    def test_non_negative(self):
        traj = TrajectoryConfig()
        for year in range(2024, 2051):
            assert _ajout_solaire_annuel_gwc(year, traj) >= 0

    def test_sum_equals_total_deployment(self):
        """Sum of annual additions should equal total capacity added."""
        traj = TrajectoryConfig()
        total = sum(_ajout_solaire_annuel_gwc(y, traj) for y in range(2024, 2051))
        expected = traj.solaire_cible_gwc - traj.solaire_actuel_gwc
        assert total == pytest.approx(expected, rel=0.01)


class TestAjoutPacAnnuel:
    """Tests for annual heat pump installations helper."""

    def test_zero_at_start(self):
        traj = TrajectoryConfig()
        assert _ajout_pac_annuel_unites(traj.annee_debut, traj) == 0.0

    def test_positive_during_deployment(self):
        traj = TrajectoryConfig()
        assert _ajout_pac_annuel_unites(2037, traj) > 0

    def test_non_negative(self):
        traj = TrajectoryConfig()
        for year in range(2024, 2051):
            assert _ajout_pac_annuel_unites(year, traj) >= 0

    def test_sum_equals_total_homes(self):
        """Sum of annual installations should equal total homes converted."""
        traj = TrajectoryConfig()
        total = sum(_ajout_pac_annuel_unites(y, traj) for y in range(2024, 2051))
        expected = (traj.pac_cible_fraction - traj.pac_actuel_fraction) * NOMBRE_MAISONS_ELIGIBLES_PAC
        assert total == pytest.approx(expected, rel=0.01)


class TestBesoinBatterie:
    """Tests for battery needs calculation."""

    def test_proportional_to_solar(self):
        config = IndustrialisationConfig()
        assert _besoin_batterie_gwh(10.0, config) == pytest.approx(
            10.0 * config.batterie_gwh_par_gwc_solaire
        )

    def test_zero_for_zero_solar(self):
        config = IndustrialisationConfig()
        assert _besoin_batterie_gwh(0.0, config) == 0.0


# =========================================================================
# Manufacturing capacity calculations
# =========================================================================

class TestAnalyserBesoinsIndustriels:
    """Tests for the main needs analysis function."""

    def test_returns_dict(self):
        result = analyser_besoins_industriels(2030)
        assert isinstance(result, dict)

    def test_year_in_result(self):
        result = analyser_besoins_industriels(2035)
        assert result['annee'] == 2035

    def test_all_keys_present(self):
        result = analyser_besoins_industriels(2035)
        expected_keys = [
            'annee', 'solaire_ajout_gwc', 'pac_ajout_unites', 'batterie_ajout_gwh',
            'usines_pv_necessaires', 'usines_batterie_necessaires', 'usines_pac_necessaires',
            'installateurs_pv_necessaires', 'installateurs_pac_necessaires',
            'silicium_kt', 'lithium_kt', 'cuivre_kt',
        ]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"

    def test_factory_needs_rounded_up(self):
        """Factory needs should always be rounded up (can't build half a factory)."""
        # Force a fractional factory need by picking a year with moderate additions
        result = analyser_besoins_industriels(2030)
        if result['solaire_ajout_gwc'] > 0:
            config = IndustrialisationConfig()
            exact = result['solaire_ajout_gwc'] / config.capacite_usine_pv_gwc_an
            assert result['usines_pv_necessaires'] >= exact
            assert isinstance(result['usines_pv_necessaires'], int)

    def test_peak_year_has_high_solar(self):
        """Around the midpoint, solar additions should be substantial."""
        result = analyser_besoins_industriels(2035)
        assert result['solaire_ajout_gwc'] > 10  # More than 10 GWc/year at peak

    def test_early_year_low_needs(self):
        result = analyser_besoins_industriels(2025)
        assert result['solaire_ajout_gwc'] < 5  # Early ramp, modest

    def test_silicon_proportional_to_solar(self):
        config = IndustrialisationConfig()
        result = analyser_besoins_industriels(2035, config=config)
        # silicium_kt = ajout_gwc * 1e6 * kg_per_kwc / 1e6
        expected_si = result['solaire_ajout_gwc'] * config.silicium_kg_par_kwc
        assert result['silicium_kt'] == pytest.approx(expected_si, abs=0.2)

    def test_lithium_proportional_to_battery(self):
        config = IndustrialisationConfig()
        result = analyser_besoins_industriels(2035, config=config)
        expected_li = result['batterie_ajout_gwh'] * 1e6 * config.lithium_kg_par_kwh / 1e6
        assert result['lithium_kt'] == pytest.approx(expected_li, abs=0.1)

    def test_copper_includes_pv_and_pac(self):
        config = IndustrialisationConfig()
        result = analyser_besoins_industriels(2035, config=config)
        cuivre_pv = result['solaire_ajout_gwc'] * 1e6 * config.cuivre_kg_par_kwc / 1e6
        cuivre_pac = result['pac_ajout_unites'] * config.cuivre_kg_par_pac / 1e6
        expected_cu = cuivre_pv + cuivre_pac
        assert result['cuivre_kt'] == pytest.approx(expected_cu, abs=0.2)

    def test_workforce_proportional_to_solar(self):
        """Workforce should be roughly proportional to solar additions."""
        config = IndustrialisationConfig()
        result = analyser_besoins_industriels(2035, config=config)
        # Allow small rounding difference (the reported solaire_ajout_gwc
        # is rounded to 2 decimals but the workforce is computed from the
        # unrounded value)
        expected = result['solaire_ajout_gwc'] * config.installateurs_pv_par_gwc
        assert result['installateurs_pv_necessaires'] == pytest.approx(expected, abs=50)

    def test_custom_configs(self):
        """Using custom configs should change the results."""
        traj1 = TrajectoryConfig(solaire_cible_gwc=500.0)
        traj2 = TrajectoryConfig(solaire_cible_gwc=200.0)
        r1 = analyser_besoins_industriels(2035, traj1)
        r2 = analyser_besoins_industriels(2035, traj2)
        assert r1['solaire_ajout_gwc'] > r2['solaire_ajout_gwc']

    def test_zero_at_start_year(self):
        traj = TrajectoryConfig()
        result = analyser_besoins_industriels(traj.annee_debut, traj_config=traj)
        assert result['solaire_ajout_gwc'] == 0.0
        assert result['pac_ajout_unites'] == 0


# =========================================================================
# Workforce scaling
# =========================================================================

class TestWorkforceScaling:
    """Tests for workforce calculations across the trajectory."""

    def test_peak_pv_workforce_exceeds_current(self):
        """At peak deployment, PV workforce needed should exceed current."""
        config = IndustrialisationConfig()
        result = analyser_besoins_industriels(2035, config=config)
        assert result['installateurs_pv_necessaires'] > config.installateurs_pv_actuels

    def test_pac_workforce_needed_during_peak(self):
        """Heat pump installers needed should be positive during peak."""
        result = analyser_besoins_industriels(2037)
        assert result['installateurs_pac_necessaires'] > 0

    def test_formation_capacity_limits_ramp(self):
        """Training capacity should create realistic workforce constraints."""
        config = IndustrialisationConfig(capacite_formation_par_an=5_000)
        plan = plan_industrialisation(config=config)
        # Workforce should increase gradually, not jump
        for i in range(1, len(plan)):
            mo_pv_delta = plan[i]['main_oeuvre_pv'] - plan[i-1]['main_oeuvre_pv']
            mo_pac_delta = plan[i]['main_oeuvre_pac'] - plan[i-1]['main_oeuvre_pac']
            assert mo_pv_delta + mo_pac_delta <= config.capacite_formation_par_an


# =========================================================================
# Bottleneck detection
# =========================================================================

class TestIdentifierGoulets:
    """Tests for bottleneck identification."""

    def test_returns_list(self):
        goulets = identifier_goulets()
        assert isinstance(goulets, list)

    def test_goulet_structure(self):
        goulets = identifier_goulets()
        if len(goulets) > 0:
            g = goulets[0]
            assert 'annee' in g
            assert 'categorie' in g
            assert 'description' in g
            assert 'severite' in g
            assert 'besoin' in g
            assert 'capacite' in g

    def test_severite_values(self):
        goulets = identifier_goulets()
        for g in goulets:
            assert g['severite'] in ('critique', 'attention')

    def test_categorie_values(self):
        valid_categories = {
            'usines_pv', 'usines_batterie', 'usines_pac',
            'main_oeuvre_pv', 'main_oeuvre_pac',
            'silicium', 'lithium', 'cuivre',
        }
        goulets = identifier_goulets()
        for g in goulets:
            assert g['categorie'] in valid_categories, f"Invalid category: {g['categorie']}"

    def test_bottleneck_year_in_range(self):
        config = IndustrialisationConfig()
        goulets = identifier_goulets(config=config)
        for g in goulets:
            assert config.annee_debut <= g['annee'] <= config.annee_fin

    def test_high_deployment_creates_bottlenecks(self):
        """Very aggressive deployment should create bottlenecks."""
        traj = TrajectoryConfig(
            solaire_cible_gwc=1000.0,  # Very high target
            solaire_steepness=0.5,     # Fast ramp
        )
        config = IndustrialisationConfig(
            nb_usines_pv_actuelles=1,
            installateurs_pv_actuels=5_000,
        )
        goulets = identifier_goulets(traj, config)
        assert len(goulets) > 0

    def test_relaxed_deployment_fewer_bottlenecks(self):
        """Modest deployment with large industrial base should have few bottlenecks."""
        traj = TrajectoryConfig(
            solaire_cible_gwc=50.0,  # Very modest
            solaire_steepness=0.1,    # Very gradual
        )
        config = IndustrialisationConfig(
            nb_usines_pv_actuelles=20,
            nb_usines_pac_actuelles=20,
            installateurs_pv_actuels=200_000,
            installateurs_pac_actuels=200_000,
        )
        goulets = identifier_goulets(traj, config)
        # Should have very few or no bottlenecks
        assert len(goulets) < 5

    def test_besoin_exceeds_capacite_in_bottleneck(self):
        """Every bottleneck should show need exceeding capacity."""
        goulets = identifier_goulets()
        for g in goulets:
            assert g['besoin'] > g['capacite']

    def test_description_is_string(self):
        goulets = identifier_goulets()
        for g in goulets:
            assert isinstance(g['description'], str)
            assert len(g['description']) > 10  # Not an empty placeholder


# =========================================================================
# Annual plan generation
# =========================================================================

class TestPlanIndustrialisation:
    """Tests for the year-by-year industrial plan."""

    def test_returns_list(self):
        plan = plan_industrialisation()
        assert isinstance(plan, list)

    def test_correct_length(self):
        config = IndustrialisationConfig()
        plan = plan_industrialisation(config=config)
        expected = config.annee_fin - config.annee_debut + 1
        assert len(plan) == expected

    def test_years_in_order(self):
        plan = plan_industrialisation()
        years = [p['annee'] for p in plan]
        assert years == sorted(years)

    def test_first_year(self):
        plan = plan_industrialisation()
        assert plan[0]['annee'] == 2024

    def test_last_year(self):
        plan = plan_industrialisation()
        assert plan[-1]['annee'] == 2050

    def test_all_keys_present(self):
        plan = plan_industrialisation()
        expected_keys = [
            'annee', 'besoins',
            'usines_pv_disponibles', 'usines_batterie_disponibles', 'usines_pac_disponibles',
            'capacite_pv_gwc', 'capacite_batterie_gwh', 'capacite_pac_unites',
            'main_oeuvre_pv', 'main_oeuvre_pac',
            'deficit_pv_gwc', 'deficit_batterie_gwh', 'deficit_pac_unites',
            'deficit_main_oeuvre_pv', 'deficit_main_oeuvre_pac',
        ]
        for key in expected_keys:
            assert key in plan[0], f"Missing key: {key}"

    def test_factories_start_at_current(self):
        config = IndustrialisationConfig()
        plan = plan_industrialisation(config=config)
        assert plan[0]['usines_pv_disponibles'] == config.nb_usines_pv_actuelles
        assert plan[0]['usines_batterie_disponibles'] == config.nb_usines_batterie_actuelles
        assert plan[0]['usines_pac_disponibles'] == config.nb_usines_pac_actuelles

    def test_factories_non_decreasing(self):
        """Number of factories should never decrease."""
        plan = plan_industrialisation()
        for i in range(1, len(plan)):
            assert plan[i]['usines_pv_disponibles'] >= plan[i-1]['usines_pv_disponibles']
            assert plan[i]['usines_batterie_disponibles'] >= plan[i-1]['usines_batterie_disponibles']
            assert plan[i]['usines_pac_disponibles'] >= plan[i-1]['usines_pac_disponibles']

    def test_workforce_non_decreasing(self):
        """Available workforce should never decrease."""
        plan = plan_industrialisation()
        for i in range(1, len(plan)):
            assert plan[i]['main_oeuvre_pv'] >= plan[i-1]['main_oeuvre_pv']
            assert plan[i]['main_oeuvre_pac'] >= plan[i-1]['main_oeuvre_pac']

    def test_workforce_starts_at_current(self):
        config = IndustrialisationConfig()
        plan = plan_industrialisation(config=config)
        assert plan[0]['main_oeuvre_pv'] == config.installateurs_pv_actuels
        assert plan[0]['main_oeuvre_pac'] == config.installateurs_pac_actuels

    def test_deficit_sign_convention(self):
        """Positive deficit means need > capacity (shortfall)."""
        plan = plan_industrialisation()
        for p in plan:
            b = p['besoins']
            assert p['deficit_pv_gwc'] == pytest.approx(
                b['solaire_ajout_gwc'] - p['capacite_pv_gwc'], abs=0.1
            )

    def test_capacity_consistent_with_factories(self):
        config = IndustrialisationConfig()
        plan = plan_industrialisation(config=config)
        for p in plan:
            assert p['capacite_pv_gwc'] == pytest.approx(
                p['usines_pv_disponibles'] * config.capacite_usine_pv_gwc_an, abs=0.1
            )


# =========================================================================
# Summary output
# =========================================================================

class TestResumeIndustrialisation:
    """Tests for the human-readable summary."""

    def test_returns_string(self):
        result = resume_industrialisation()
        assert isinstance(result, str)

    def test_contains_title(self):
        result = resume_industrialisation()
        assert "Industrialisation" in result

    def test_contains_milestone_years(self):
        result = resume_industrialisation()
        assert "2030" in result
        assert "2050" in result

    def test_contains_current_capacity(self):
        result = resume_industrialisation()
        assert "Usines PV" in result
        assert "GWc/an" in result

    def test_contains_bottleneck_count(self):
        result = resume_industrialisation()
        assert "Goulets" in result or "goulets" in result

    def test_contains_materials(self):
        result = resume_industrialisation()
        assert "Silicium" in result
        assert "Lithium" in result
        assert "Cuivre" in result

    def test_contains_peak_info(self):
        result = resume_industrialisation()
        assert "Pic" in result or "pic" in result

    def test_non_empty(self):
        result = resume_industrialisation()
        assert len(result) > 200  # Should be a substantial summary

    def test_custom_config_changes_output(self):
        """Different configs should produce different summaries."""
        r1 = resume_industrialisation()
        traj2 = TrajectoryConfig(solaire_cible_gwc=100.0)
        r2 = resume_industrialisation(traj_config=traj2)
        assert r1 != r2
