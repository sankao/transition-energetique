"""Tests for the rapport (report generation) module."""

import pytest
from src.rapport import (
    generer_rapport,
    generer_resume_executif,
    generer_tableau_hypotheses,
    generer_section_resultats,
)
from src.config import EnergyModelConfig


# ---------------------------------------------------------------------------
# Tests for generer_resume_executif
# ---------------------------------------------------------------------------

class TestResumeExecutif:
    """Tests for the executive summary generator."""

    def test_returns_non_empty_string(self):
        result = generer_resume_executif(gaz_twh=114.0)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_concise_under_500_chars(self):
        result = generer_resume_executif(gaz_twh=114.0)
        assert len(result) < 500, (
            f"Executive summary should be concise (< 500 chars), got {len(result)}"
        )

    def test_contains_gas_backup_value(self):
        result = generer_resume_executif(gaz_twh=114.0)
        assert "114" in result

    def test_custom_gas_value(self):
        result = generer_resume_executif(gaz_twh=80.0)
        assert "80" in result

    def test_french_text(self):
        result = generer_resume_executif(gaz_twh=114.0)
        # Check for key French terms
        assert "scenario" in result.lower() or "scénario" in result.lower()
        assert "emissions" in result.lower() or "émissions" in result.lower()

    def test_mentions_chauffage(self):
        result = generer_resume_executif(gaz_twh=114.0)
        assert "chauffage" in result.lower()

    def test_mentions_reduction(self):
        result = generer_resume_executif(gaz_twh=114.0)
        assert "reduction" in result.lower() or "réduction" in result.lower()


# ---------------------------------------------------------------------------
# Tests for generer_tableau_hypotheses
# ---------------------------------------------------------------------------

class TestTableauHypotheses:
    """Tests for the assumptions table generator."""

    def test_returns_non_empty_string(self):
        result = generer_tableau_hypotheses()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_solar_capacity(self):
        result = generer_tableau_hypotheses()
        assert "500" in result
        assert "GWc" in result

    def test_contains_cop(self):
        result = generer_tableau_hypotheses()
        assert "COP" in result or "cop" in result

    def test_contains_gas_cost(self):
        result = generer_tableau_hypotheses()
        assert "EUR/MWh" in result

    def test_contains_capex(self):
        result = generer_tableau_hypotheses()
        assert "CAPEX" in result or "EUR/kW" in result

    def test_table_formatting(self):
        """Table should have proper formatting with separators."""
        result = generer_tableau_hypotheses()
        assert "+" in result
        assert "|" in result

    def test_custom_config(self):
        config = EnergyModelConfig()
        config.production.solar_capacity_gwc = 700.0
        result = generer_tableau_hypotheses(config)
        assert "700" in result

    def test_contains_nuclear(self):
        result = generer_tableau_hypotheses()
        assert "Nucleaire" in result or "nucleaire" in result or "nucléaire" in result.lower()


# ---------------------------------------------------------------------------
# Tests for generer_section_resultats
# ---------------------------------------------------------------------------

class TestSectionResultats:
    """Tests for the results section generator."""

    def test_returns_non_empty_string(self):
        result = generer_section_resultats(gaz_twh=114.0)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_gas_backup(self):
        result = generer_section_resultats(gaz_twh=114.0)
        assert "114" in result

    def test_contains_emissions(self):
        result = generer_section_resultats(gaz_twh=114.0)
        assert "MtCO2" in result

    def test_contains_reduction(self):
        result = generer_section_resultats(gaz_twh=114.0)
        assert "Reduction" in result or "reduction" in result or "Réduction" in result

    def test_contains_snbc_targets(self):
        result = generer_section_resultats(gaz_twh=114.0)
        assert "SNBC" in result

    def test_custom_gas_value(self):
        result = generer_section_resultats(gaz_twh=50.0)
        assert "50" in result

    def test_contains_chauffage_energy(self):
        result = generer_section_resultats(gaz_twh=114.0)
        assert "TWh" in result
        assert "chauffage" in result.lower() or "Chauffage" in result


# ---------------------------------------------------------------------------
# Tests for generer_rapport (full report)
# ---------------------------------------------------------------------------

class TestGenererRapport:
    """Tests for the full report generator."""

    def test_returns_non_empty_string(self):
        result = generer_rapport(gaz_twh=114.0)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_all_sections_present(self):
        """All nine report sections should be present."""
        result = generer_rapport(gaz_twh=114.0)
        assert "Resume executif" in result
        assert "Contexte et objectifs" in result
        assert "Hypotheses principales" in result
        assert "Resultats cles" in result
        assert "Chauffage" in result
        assert "Bilan carbone" in result
        assert "Trajectoire" in result
        assert "Limites et incertitudes" in result
        assert "Recommandations" in result

    def test_report_title_present(self):
        result = generer_rapport(gaz_twh=114.0)
        assert "RAPPORT DE SYNTHESE" in result

    def test_report_footer_present(self):
        result = generer_rapport(gaz_twh=114.0)
        assert "Fin du rapport" in result

    def test_custom_gas_value(self):
        result = generer_rapport(gaz_twh=80.0)
        assert "80" in result

    def test_explicit_gas_value(self):
        result = generer_rapport(gaz_twh=114.0)
        assert "114" in result

    def test_custom_config(self):
        config = EnergyModelConfig()
        config.production.solar_capacity_gwc = 700.0
        result = generer_rapport(gaz_twh=114.0, config=config)
        assert "700" in result

    def test_french_content(self):
        """Report should be written in French."""
        result = generer_rapport(gaz_twh=114.0)
        french_terms = [
            "neutralite carbone",
            "electrification",
            "solaire",
            "nucleaire",
            "investissement",
            "emissions",
        ]
        for term in french_terms:
            assert term in result.lower(), f"French term '{term}' not found in report"

    def test_report_mentions_conservative_assumptions(self):
        result = generer_rapport(gaz_twh=114.0)
        assert "conservative" in result.lower() or "conservateur" in result.lower()

    def test_report_mentions_limitations(self):
        result = generer_rapport(gaz_twh=114.0)
        assert "eolien" in result.lower() or "éolien" in result.lower()
        assert "stockage" in result.lower()
        assert "interconnexion" in result.lower()

    def test_report_substantial_length(self):
        """A decision-maker report should be substantial."""
        result = generer_rapport(gaz_twh=114.0)
        assert len(result) > 2000, (
            f"Report should be substantial (> 2000 chars), got {len(result)}"
        )

    def test_contains_numbers(self):
        """Report should include quantitative data, not just prose."""
        result = generer_rapport(gaz_twh=114.0)
        # Check for key numbers (TWh, GWc, MtCO2, EUR)
        assert "TWh" in result
        assert "GWc" in result
        assert "MtCO2" in result
        assert "EUR" in result
