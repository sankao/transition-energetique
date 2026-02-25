"""Tests for consumption module — SDES 2023 reference and electrification."""
import pytest
from src.consumption import UsageReference, SectorReference


class TestUsageReference:
    def test_vectors_sum_to_total(self):
        u = UsageReference(
            name="chauffage", total_twh=312,
            elec_twh=50, gaz_twh=94, petrole_twh=31,
            charbon_twh=0, enr_twh=125, reseau_twh=12,
        )
        assert u.total_twh == 312

    def test_vectors_mismatch_raises(self):
        with pytest.raises(ValueError):
            UsageReference(
                name="bad", total_twh=100,
                elec_twh=10, gaz_twh=10, petrole_twh=10,
                charbon_twh=0, enr_twh=10, reseau_twh=10,
            )  # sum=50, total=100 -> error


class TestSectorReference:
    def test_usages_sum_to_sector_total(self):
        usages = [
            UsageReference("a", 200, 200, 0, 0, 0, 0, 0),
            UsageReference("b", 100, 50, 50, 0, 0, 0, 0),
        ]
        s = SectorReference(name="test", usages=usages)
        assert s.total_twh == 300

    def test_sector_total_property(self):
        usages = [
            UsageReference("x", 50, 50, 0, 0, 0, 0, 0),
        ]
        s = SectorReference(name="test", usages=usages)
        assert s.total_twh == 50
