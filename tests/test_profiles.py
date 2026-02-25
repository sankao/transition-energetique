"""Tests for temporal profile functions."""
import pytest
from src.heating import profil_chauffage_normalise


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
