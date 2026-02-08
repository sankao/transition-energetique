"""Tests for the steady-state pricing model."""

import pytest
from src.tarification import (
    TarificationConfig,
    cout_production_annuel,
    cout_systeme_annuel,
    tarif_equilibre_eur_mwh,
    flux_financiers,
    comparaison_cout_consommateur,
    analyse_sensibilite_tarif,
    resume_tarification,
)


class TestTarificationConfig:
    """Tests for TarificationConfig defaults."""

    def test_lcoe_ordering(self):
        """Hydro < Solar < Nuclear < Gas LCOE."""
        config = TarificationConfig()
        assert config.hydro_lcoe_eur_mwh < config.solaire_lcoe_eur_mwh
        assert config.solaire_lcoe_eur_mwh < config.nucleaire_lcoe_eur_mwh
        assert config.nucleaire_lcoe_eur_mwh < config.gaz_lcoe_eur_mwh

    def test_production_volumes_positive(self):
        config = TarificationConfig()
        assert config.solaire_twh > 0
        assert config.nucleaire_twh > 0
        assert config.hydro_twh > 0
        assert config.gaz_twh > 0

    def test_consumer_shares_sum_to_one(self):
        config = TarificationConfig()
        total = config.part_menages + config.part_industrie + config.part_tertiaire
        assert total == pytest.approx(1.0)

    def test_current_prices_reasonable(self):
        config = TarificationConfig()
        assert 150 < config.prix_actuel_menage_eur_mwh < 350
        assert 80 < config.prix_actuel_industrie_eur_mwh < 200


class TestCoutProduction:
    """Tests for production cost calculation."""

    def test_all_sources_present(self):
        result = cout_production_annuel()
        for key in ['solaire_eur_b', 'nucleaire_eur_b', 'hydro_eur_b',
                     'gaz_eur_b', 'stockage_eur_b', 'total_production_eur_b']:
            assert key in result

    def test_total_is_sum(self):
        result = cout_production_annuel()
        expected = (result['solaire_eur_b'] + result['nucleaire_eur_b'] +
                    result['hydro_eur_b'] + result['gaz_eur_b'] +
                    result['stockage_eur_b'])
        assert result['total_production_eur_b'] == pytest.approx(expected)

    def test_all_positive(self):
        result = cout_production_annuel()
        for v in result.values():
            assert v > 0

    def test_nucleaire_largest_cost(self):
        """Nuclear should be largest cost due to high volume × moderate LCOE."""
        result = cout_production_annuel()
        assert result['nucleaire_eur_b'] > result['solaire_eur_b']

    def test_total_order_of_magnitude(self):
        """Total production cost should be 40-80 €B/year."""
        result = cout_production_annuel()
        assert 40 < result['total_production_eur_b'] < 80


class TestCoutSysteme:
    """Tests for system cost calculation."""

    def test_all_components_present(self):
        result = cout_systeme_annuel()
        assert 'reseau_eur_b' in result
        assert 'services_systeme_eur_b' in result
        assert 'total_systeme_eur_b' in result

    def test_reseau_dominates(self):
        result = cout_systeme_annuel()
        assert result['reseau_eur_b'] > result['services_systeme_eur_b']

    def test_total_reasonable(self):
        result = cout_systeme_annuel()
        assert 15 < result['total_systeme_eur_b'] < 30


class TestTarifEquilibre:
    """Tests for break-even tariff calculation."""

    def test_all_components(self):
        result = tarif_equilibre_eur_mwh()
        assert 'composante_production_eur_mwh' in result
        assert 'composante_reseau_eur_mwh' in result
        assert 'total_ht_eur_mwh' in result
        assert 'total_ttc_eur_mwh' in result

    def test_ttc_higher_than_ht(self):
        result = tarif_equilibre_eur_mwh()
        assert result['total_ttc_eur_mwh'] > result['total_ht_eur_mwh']

    def test_tarif_reasonable(self):
        """Tariff should be in realistic range (100-300 €/MWh TTC)."""
        result = tarif_equilibre_eur_mwh()
        assert 100 < result['total_ttc_eur_mwh'] < 300

    def test_production_largest_component(self):
        result = tarif_equilibre_eur_mwh()
        assert result['composante_production_eur_mwh'] > result['composante_reseau_eur_mwh']

    def test_ht_sum_consistent(self):
        result = tarif_equilibre_eur_mwh()
        expected = (result['composante_production_eur_mwh'] +
                    result['composante_reseau_eur_mwh'] +
                    result['composante_services_eur_mwh'])
        assert result['total_ht_eur_mwh'] == pytest.approx(expected)


class TestFluxFinanciers:
    """Tests for financial flows."""

    def test_balance_near_zero(self):
        """Revenue should approximately equal expenditure."""
        result = flux_financiers()
        assert abs(result['balance_eur_b']) < 0.01

    def test_revenues_positive(self):
        result = flux_financiers()
        assert result['revenus_totaux_eur_b'] > 0

    def test_consumer_shares_sum_to_total(self):
        result = flux_financiers()
        consumer_sum = (result['revenus_menages_eur_b'] +
                        result['revenus_industrie_eur_b'] +
                        result['revenus_tertiaire_eur_b'])
        assert consumer_sum == pytest.approx(result['revenus_totaux_eur_b'])

    def test_expenditure_matches_revenue(self):
        result = flux_financiers()
        expenditure = (result['vers_producteurs_eur_b'] +
                       result['vers_reseau_eur_b'] +
                       result['vers_services_eur_b'] +
                       result['vers_etat_eur_b'])
        assert expenditure == pytest.approx(result['revenus_totaux_eur_b'], rel=1e-6)

    def test_menages_largest_payer(self):
        result = flux_financiers()
        assert result['revenus_menages_eur_b'] > result['revenus_tertiaire_eur_b']


class TestComparaisonConsommateur:
    """Tests for consumer cost comparison."""

    def test_household_savings(self):
        """Households should save money (no more gas bill)."""
        result = comparaison_cout_consommateur()
        assert result['menage_economie_eur'] > 0

    def test_electrified_consumption_higher(self):
        result = comparaison_cout_consommateur()
        assert result['menage_conso_electrifiee_mwh'] > result['menage_conso_actuelle_mwh']

    def test_industry_impact_present(self):
        result = comparaison_cout_consommateur()
        assert 'industrie_variation_pct' in result

    def test_tarif_comparison_present(self):
        result = comparaison_cout_consommateur()
        assert 'tarif_actuel_menage_eur_mwh' in result
        assert 'tarif_transition_eur_mwh' in result


class TestSensibilite:
    """Tests for tariff sensitivity analysis."""

    def test_all_parameters_tested(self):
        result = analyse_sensibilite_tarif()
        assert 'solaire_lcoe' in result
        assert 'nucleaire_lcoe' in result
        assert 'gaz_lcoe' in result
        assert 'reseau' in result
        assert 'gaz_volume' in result

    def test_impacts_positive(self):
        """Higher costs should increase tariff (positive impact)."""
        result = analyse_sensibilite_tarif()
        for name, data in result.items():
            assert data['high_eur_mwh'] > data['low_eur_mwh']

    def test_nucleaire_high_sensitivity(self):
        """Nuclear LCOE should have significant impact (largest volume)."""
        result = analyse_sensibilite_tarif()
        assert result['nucleaire_lcoe']['impact_pct'] > 1.0


class TestResumeTarification:
    """Tests for summary output."""

    def test_returns_string(self):
        assert isinstance(resume_tarification(), str)

    def test_contains_sections(self):
        result = resume_tarification()
        assert "PRODUCTION" in result
        assert "TARIF" in result
        assert "FLUX" in result
        assert "CONSOMMATEUR" in result
        assert "SENSIBILITE" in result

    def test_contains_tariff(self):
        result = resume_tarification()
        assert "EUR/MWh" in result
        assert "c/kWh" in result

    def test_contains_balance(self):
        result = resume_tarification()
        assert "EUR B" in result
