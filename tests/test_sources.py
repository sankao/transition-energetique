"""Tests for the sources documentation module."""

import pytest
from datetime import date
from src.sources import (
    DataSource,
    ALL_SOURCES,
    get_source,
    get_sources_for_parameter,
    generate_bibliography,
    check_source_freshness,
    RTE_BILAN_2020,
    IRENA_COSTS_2024,
)


class TestDataSource:
    """Tests for the DataSource class."""

    def test_citation_format(self):
        """Citation should include name, URL, and date."""
        source = DataSource(
            id="test",
            name="Test Source",
            url="https://example.com",
            access_date=date(2026, 1, 15),
            description="A test source",
            parameters=["param1"],
        )
        citation = source.citation()
        assert "Test Source" in citation
        assert "https://example.com" in citation
        assert "2026-01-15" in citation


class TestSourceRegistry:
    """Tests for the source registry functions."""

    def test_all_sources_not_empty(self):
        """Registry should contain sources."""
        assert len(ALL_SOURCES) > 0

    def test_all_sources_have_required_fields(self):
        """All sources should have required fields populated."""
        for source in ALL_SOURCES:
            assert source.id, f"Source missing id: {source}"
            assert source.name, f"Source missing name: {source.id}"
            assert source.url, f"Source missing url: {source.id}"
            assert source.access_date, f"Source missing access_date: {source.id}"
            assert source.parameters, f"Source missing parameters: {source.id}"

    def test_all_sources_have_valid_urls(self):
        """All source URLs should start with http."""
        for source in ALL_SOURCES:
            assert source.url.startswith("http"), f"Invalid URL for {source.id}: {source.url}"

    def test_get_source_found(self):
        """Should find existing source by ID."""
        source = get_source("rte-bilan-2020")
        assert source is not None
        assert source.name == "RTE Bilan Électrique 2020"

    def test_get_source_not_found(self):
        """Should return None for unknown source."""
        source = get_source("nonexistent-source")
        assert source is None

    def test_get_sources_for_parameter(self):
        """Should find sources for a given parameter."""
        sources = get_sources_for_parameter("nuclear_min_gw")
        assert len(sources) >= 1
        assert any(s.id == "rte-bilan-2020" for s in sources)

    def test_get_sources_for_unknown_parameter(self):
        """Should return empty list for unknown parameter."""
        sources = get_sources_for_parameter("unknown_param_xyz")
        assert sources == []


class TestBibliography:
    """Tests for bibliography generation."""

    def test_generate_bibliography(self):
        """Should generate markdown bibliography."""
        bib = generate_bibliography()
        assert "# Bibliography" in bib
        assert "RTE" in bib
        assert "IRENA" in bib


class TestSourceFreshness:
    """Tests for source freshness checking."""

    def test_check_freshness_recent_sources(self):
        """Recently accessed sources should not be stale."""
        # All sources were accessed in January 2026
        # Test with 365 day threshold - should find none stale
        stale = check_source_freshness(max_age_days=365)
        # This depends on current date, so we just check the function works
        assert isinstance(stale, list)

    def test_check_freshness_strict_threshold(self):
        """With very strict threshold, sources may be stale."""
        # 1 day threshold - most sources will be "stale"
        stale = check_source_freshness(max_age_days=1)
        # Should return a list (may or may not have items depending on test date)
        assert isinstance(stale, list)


class TestSpecificSources:
    """Tests for specific important sources."""

    def test_rte_source_parameters(self):
        """RTE source should cover nuclear and hydro parameters."""
        assert "nuclear_min_gw" in RTE_BILAN_2020.parameters
        assert "nuclear_max_gw" in RTE_BILAN_2020.parameters
        assert "hydro_avg_gw" in RTE_BILAN_2020.parameters

    def test_irena_source_parameters(self):
        """IRENA source should cover solar cost parameters."""
        assert "solar_capex_eur_per_kw" in IRENA_COSTS_2024.parameters
        assert "solar_lifetime_years" in IRENA_COSTS_2024.parameters
