"""Tests for the detailed heating module."""

import pytest
from src.heating import (
    HeatingConfig,
    interpoler_cop,
    besoin_thermique_maison_w,
    besoin_electrique_maison_w,
    besoin_national_chauffage_kw,
    energie_chauffage_mensuelle_twh,
    bilan_chauffage_annuel,
    resume_chauffage,
    TEMPERATURES_EXTERIEURES,
    COEFFICIENTS_PLAGE,
)


class TestHeatingConfig:
    """Tests for HeatingConfig defaults and properties."""

    def test_default_values(self):
        config = HeatingConfig()
        assert config.nombre_maisons == 20_000_000
        assert config.surface_moyenne_m2 == 120.0
        assert config.hauteur_plafond_m == 2.5
        assert config.coefficient_g == 0.65
        assert config.temperature_interieure == 19.0
        assert config.avec_pompe_a_chaleur is True

    def test_volume_moyen(self):
        config = HeatingConfig()
        assert config.volume_moyen_m3 == 300.0

    def test_custom_volume(self):
        config = HeatingConfig(surface_moyenne_m2=100.0, hauteur_plafond_m=3.0)
        assert config.volume_moyen_m3 == 300.0

    def test_temperatures_all_months_present(self):
        config = HeatingConfig()
        mois = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
        for m in mois:
            assert m in config.temperatures_exterieures

    def test_cop_table_has_entries(self):
        config = HeatingConfig()
        assert len(config.cop_par_temperature) >= 5


class TestInterpolerCop:
    """Tests for COP interpolation."""

    def test_exact_match(self):
        table = {0.0: 2.5, 5.0: 3.0, 10.0: 3.5}
        assert interpoler_cop(5.0, table) == 3.0

    def test_interpolation_midpoint(self):
        table = {0.0: 2.0, 10.0: 4.0}
        assert interpoler_cop(5.0, table) == pytest.approx(3.0)

    def test_interpolation_quarter(self):
        table = {0.0: 2.0, 10.0: 4.0}
        assert interpoler_cop(2.5, table) == pytest.approx(2.5)

    def test_below_range_clamps(self):
        table = {0.0: 2.0, 10.0: 4.0}
        assert interpoler_cop(-20.0, table) == 2.0

    def test_above_range_clamps(self):
        table = {0.0: 2.0, 10.0: 4.0}
        assert interpoler_cop(30.0, table) == 4.0

    def test_default_cop_table(self):
        """COP decreases as temperature drops."""
        config = HeatingConfig()
        cop_cold = interpoler_cop(-10.0, config.cop_par_temperature)
        cop_mild = interpoler_cop(10.0, config.cop_par_temperature)
        assert cop_cold < cop_mild

    def test_cop_at_5c(self):
        """COP at 5°C should be 3.0 in default table."""
        config = HeatingConfig()
        assert interpoler_cop(5.0, config.cop_par_temperature) == 3.0


class TestBesoinThermique:
    """Tests for thermal power calculation."""

    def test_known_calculation(self):
        """G × V × ΔT for January: 0.65 × 300 × (19 - 5.2) = 2691 W."""
        config = HeatingConfig()
        p = besoin_thermique_maison_w(config, 5.2)
        assert p == pytest.approx(0.65 * 300 * 13.8, rel=1e-6)

    def test_no_heating_above_setpoint(self):
        """No heating needed when outdoor temp >= indoor temp."""
        config = HeatingConfig()
        assert besoin_thermique_maison_w(config, 19.0) == 0.0
        assert besoin_thermique_maison_w(config, 25.0) == 0.0

    def test_higher_g_more_heat(self):
        """Worse insulation (higher G) needs more heating."""
        config_good = HeatingConfig(coefficient_g=0.35)
        config_bad = HeatingConfig(coefficient_g=0.65)
        t = 5.0
        assert besoin_thermique_maison_w(config_bad, t) > besoin_thermique_maison_w(config_good, t)

    def test_larger_volume_more_heat(self):
        """Larger house needs more heating."""
        config_small = HeatingConfig(surface_moyenne_m2=80.0)
        config_large = HeatingConfig(surface_moyenne_m2=150.0)
        t = 5.0
        assert besoin_thermique_maison_w(config_large, t) > besoin_thermique_maison_w(config_small, t)


class TestBesoinElectrique:
    """Tests for electrical power calculation."""

    def test_with_heat_pump_divides_by_cop(self):
        """Heat pump reduces electrical need by COP factor."""
        config = HeatingConfig(avec_pompe_a_chaleur=True)
        t = 5.0  # COP = 3.0 at 5°C
        p_th = besoin_thermique_maison_w(config, t)
        p_el = besoin_electrique_maison_w(config, t)
        cop = interpoler_cop(t, config.cop_par_temperature)
        assert p_el == pytest.approx(p_th / cop, rel=1e-6)

    def test_without_heat_pump_equals_thermal(self):
        """Without heat pump, electrical = thermal (resistance heating)."""
        config = HeatingConfig(avec_pompe_a_chaleur=False)
        t = 5.0
        p_th = besoin_thermique_maison_w(config, t)
        p_el = besoin_electrique_maison_w(config, t)
        assert p_el == p_th

    def test_heat_pump_saves_energy(self):
        """Heat pump uses less electricity than resistance heating."""
        t = 5.0
        config_pac = HeatingConfig(avec_pompe_a_chaleur=True)
        config_res = HeatingConfig(avec_pompe_a_chaleur=False)
        assert besoin_electrique_maison_w(config_pac, t) < besoin_electrique_maison_w(config_res, t)


class TestBesoinNational:
    """Tests for national-level heating demand."""

    def test_scales_with_houses(self):
        """Demand should scale linearly with number of houses."""
        config_1m = HeatingConfig(nombre_maisons=1_000_000)
        config_2m = HeatingConfig(nombre_maisons=2_000_000)
        p_1m = besoin_national_chauffage_kw(config_1m, 'Janvier', '8h-13h')
        p_2m = besoin_national_chauffage_kw(config_2m, 'Janvier', '8h-13h')
        assert p_2m == pytest.approx(2 * p_1m, rel=1e-6)

    def test_night_slot_reduced(self):
        """Night slot has lower coefficient than daytime."""
        config = HeatingConfig()
        p_day = besoin_national_chauffage_kw(config, 'Janvier', '8h-13h')
        p_night = besoin_national_chauffage_kw(config, 'Janvier', '23h-8h')
        assert p_night < p_day

    def test_summer_near_zero(self):
        """Summer heating demand should be near zero."""
        config = HeatingConfig()
        p = besoin_national_chauffage_kw(config, 'Juillet', '8h-13h')
        assert p == 0.0  # T_ext 22.1 > T_int 19.0

    def test_winter_positive(self):
        """Winter heating demand should be significant."""
        config = HeatingConfig()
        p = besoin_national_chauffage_kw(config, 'Janvier', '8h-13h')
        assert p > 0


class TestEnergieMensuelle:
    """Tests for monthly energy calculation."""

    def test_summer_zero(self):
        """No heating energy in summer when T_ext > T_int."""
        config = HeatingConfig()
        e = energie_chauffage_mensuelle_twh(config, 'Juillet')
        assert e == 0.0

    def test_january_positive(self):
        """January should have significant heating energy."""
        config = HeatingConfig()
        e = energie_chauffage_mensuelle_twh(config, 'Janvier')
        assert e > 0

    def test_january_order_of_magnitude(self):
        """January heating should be in the range of 5-25 TWh."""
        config = HeatingConfig()
        e = energie_chauffage_mensuelle_twh(config, 'Janvier')
        assert 5 < e < 25


class TestBilanAnnuel:
    """Tests for annual heating balance."""

    def test_all_months_present(self):
        bilan = bilan_chauffage_annuel()
        mois = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
        for m in mois:
            assert m in bilan
        assert '_total' in bilan

    def test_annual_total_reasonable(self):
        """Annual heating should be between 50 and 200 TWh."""
        bilan = bilan_chauffage_annuel()
        total = bilan['_total']['energie_annuelle_twh']
        assert 50 < total < 200

    def test_winter_higher_than_summer(self):
        """Winter months should have higher heating than summer."""
        bilan = bilan_chauffage_annuel()
        assert bilan['Janvier']['energie_mensuelle_twh'] > bilan['Juin']['energie_mensuelle_twh']

    def test_cop_varies_by_month(self):
        """COP should vary between months (temperature-dependent)."""
        bilan = bilan_chauffage_annuel()
        cop_jan = bilan['Janvier']['cop']
        cop_jun = bilan['Juin']['cop']
        assert cop_jan < cop_jun  # Colder month has lower COP


class TestResumeChauffage:
    """Tests for the summary output."""

    def test_returns_string(self):
        result = resume_chauffage()
        assert isinstance(result, str)

    def test_contains_key_info(self):
        result = resume_chauffage()
        assert "20,000,000" in result or "20 000 000" in result
        assert "TOTAL ANNUEL" in result
        assert "TWh" in result

    def test_comparison_with_old_model(self):
        """Summary should compare with fixed COP=2 model."""
        result = resume_chauffage()
        assert "COP fixe=2" in result
