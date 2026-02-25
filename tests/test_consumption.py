"""Tests for consumption module — SDES 2023 reference and electrification."""
import pytest
from src.consumption import UsageReference, SectorReference, ReferenceData, sdes_2023


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


class TestReferenceData:
    def test_grand_total_is_1615(self):
        ref = sdes_2023()
        assert ref.total_twh == pytest.approx(1615, abs=1)

    def test_residential_is_422(self):
        ref = sdes_2023()
        assert ref.residential.total_twh == pytest.approx(422, abs=1)

    def test_tertiary_is_229(self):
        ref = sdes_2023()
        assert ref.tertiary.total_twh == pytest.approx(229, abs=1)

    def test_industry_is_283(self):
        ref = sdes_2023()
        assert ref.industry.total_twh == pytest.approx(283, abs=1)

    def test_transport_is_513(self):
        ref = sdes_2023()
        assert ref.transport.total_twh == pytest.approx(513, abs=1)

    def test_agriculture_is_55(self):
        ref = sdes_2023()
        assert ref.agriculture.total_twh == pytest.approx(55, abs=1)

    def test_non_energy_is_113(self):
        ref = sdes_2023()
        assert ref.non_energy.total_twh == pytest.approx(113, abs=1)

    def test_residential_has_5_usages(self):
        ref = sdes_2023()
        assert len(ref.residential.usages) == 5
        names = [u.name for u in ref.residential.usages]
        assert "chauffage" in names
        assert "ecs" in names

    def test_transport_has_10_modes(self):
        ref = sdes_2023()
        assert len(ref.transport.usages) == 10

    def test_national_electricity_is_393(self):
        ref = sdes_2023()
        total_elec = sum(s.elec_twh for s in ref.all_sectors)
        assert total_elec == pytest.approx(393, abs=5)
