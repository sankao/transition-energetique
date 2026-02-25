"""Tests for temporal profile functions."""
import pytest
from src.heating import profil_chauffage_normalise
from src.transport import profil_recharge_normalise
from src.agriculture import profil_agriculture_normalise


class TestHeatingProfile:
    def test_sums_to_one(self):
        profil = profil_chauffage_normalise()
        assert sum(profil) == pytest.approx(1.0, abs=0.001)

    def test_returns_12_months(self):
        profil = profil_chauffage_normalise()
        assert len(profil) == 12

    def test_january_greater_than_july(self):
        profil = profil_chauffage_normalise()
        assert profil[0] > profil[6]  # jan > jul

    def test_winter_dominant(self):
        profil = profil_chauffage_normalise()
        winter = profil[0] + profil[1] + profil[10] + profil[11]  # jan,feb,nov,dec
        summer = profil[5] + profil[6] + profil[7] + profil[8]    # jun,jul,aug,sep
        assert winter > 2 * summer


class TestTransportProfile:
    def test_sums_to_one(self):
        profil = profil_recharge_normalise()
        total = sum(sum(month) for month in profil)
        assert total == pytest.approx(1.0, abs=0.001)

    def test_shape_12x5(self):
        profil = profil_recharge_normalise()
        assert len(profil) == 12
        for month in profil:
            assert len(month) == 5

    def test_night_slot_dominant(self):
        """Nighttime charging (23h-8h, slot 4) should be largest."""
        profil = profil_recharge_normalise()
        jan = profil[0]
        assert jan[4] > jan[0]  # night > morning


class TestAgricultureProfile:
    def test_sums_to_one(self):
        profil = profil_agriculture_normalise()
        assert sum(profil) == pytest.approx(1.0, abs=0.001)

    def test_returns_12_months(self):
        profil = profil_agriculture_normalise()
        assert len(profil) == 12

    def test_summer_dominant(self):
        """Agriculture peaks in summer (irrigation, harvest)."""
        profil = profil_agriculture_normalise()
        summer = profil[5] + profil[6] + profil[7]  # jun,jul,aug
        winter = profil[0] + profil[1] + profil[11]  # jan,feb,dec
        assert summer > winter
