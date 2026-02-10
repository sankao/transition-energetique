"""Data consistency tests — verify synthesis matches individual modules."""

import pytest
from src.config import EnergyModelConfig
from src.transport import consommation_electrifiee_twh, demande_recharge_par_plage, TransportConfig
from src.secteurs import bilan_industrie, bilan_tertiaire, IndustrieConfig, TertiaireConfig
from src.agriculture import consommation_mensuelle_twh, AgricultureConfig


PLAGES = ('8h-13h', '13h-18h', '18h-20h', '20h-23h', '23h-8h')
DUREES = {'8h-13h': 5.0, '13h-18h': 5.0, '18h-20h': 2.0, '20h-23h': 3.0, '23h-8h': 9.0}
MOIS_ORDRE = (
    'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
    'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
)


class TestTransportConsistency:
    """Verify transport kW in synthesis matches module total_elec_twh."""

    def test_total_transport_matches_module(self):
        """Sum of per-slot transport kW (charging + rail/SAF) should match total_elec_twh."""
        config = TransportConfig()
        electrifie = consommation_electrifiee_twh(config)
        total_elec_twh = electrifie['total_elec_twh']

        # Reproduce the store_sector_data logic
        rail_saf_kw = (electrifie['rail_elec_twh'] + electrifie['aviation_elec_saf_twh']) * 1e9 / 8760

        total_energy_kwh = 0.0
        for plage in PLAGES:
            duree = DUREES[plage]
            slot_twh = demande_recharge_par_plage(plage, config)
            charging_kw = slot_twh * 1e9 / (duree * 365)
            transport_kw = charging_kw + rail_saf_kw
            # Energy per year for this slot: kW * hours/day * 365 days
            total_energy_kwh += transport_kw * duree * 365

        total_twh = total_energy_kwh / 1e9
        assert abs(total_twh - total_elec_twh) / total_elec_twh < 0.01, (
            f"Transport total {total_twh:.1f} TWh != module {total_elec_twh:.1f} TWh"
        )

    def test_charging_profile_subset(self):
        """demande_recharge_par_plage should sum to direct_elec (road+maritime+fluvial)."""
        config = TransportConfig()
        electrifie = consommation_electrifiee_twh(config)
        direct_elec = (electrifie['routier_passagers_elec_twh']
                       + electrifie['routier_fret_elec_twh']
                       + electrifie['maritime_elec_twh']
                       + electrifie['fluvial_elec_twh'])

        slot_sum = sum(demande_recharge_par_plage(p, config) for p in PLAGES)
        assert abs(slot_sum - direct_elec) < 0.01, (
            f"Slot sum {slot_sum:.2f} != direct_elec {direct_elec:.2f}"
        )


class TestPVConfigConsistency:
    """Verify PV params are centralized in config."""

    def test_config_has_pv_breakdown(self):
        config = EnergyModelConfig()
        p = config.production
        assert p.solar_gwc_maisons == 200.0
        assert p.solar_gwc_collectif == 50.0
        assert p.solar_gwc_centrales == 250.0
        assert p.nombre_maisons == 20_000_000
        assert p.nombre_collectifs == 10_000_000
        assert p.kwc_par_maison == 10.0
        assert p.kwc_par_collectif == 5.0

    def test_pv_breakdown_sums_to_total(self):
        """Individual GWc should sum to total solar capacity."""
        config = EnergyModelConfig()
        p = config.production
        maisons_gwc = p.kwc_par_maison * p.nombre_maisons / 1e6
        collectif_gwc = p.kwc_par_collectif * p.nombre_collectifs / 1e6
        total = maisons_gwc + collectif_gwc + p.solar_gwc_centrales
        assert abs(total - p.solar_capacity_gwc) < 0.1, (
            f"PV breakdown {total:.1f} GWc != total {p.solar_capacity_gwc:.1f} GWc"
        )


class TestRapportRequiresGaz:
    """Verify rapport functions require explicit gaz_twh."""

    def test_resume_executif_requires_gaz(self):
        from src.rapport import generer_resume_executif
        with pytest.raises(TypeError):
            generer_resume_executif()

    def test_section_resultats_requires_gaz(self):
        from src.rapport import generer_section_resultats
        with pytest.raises(TypeError):
            generer_section_resultats()

    def test_rapport_requires_gaz(self):
        from src.rapport import generer_rapport
        with pytest.raises(TypeError):
            generer_rapport()


class TestAgricultureProfile:
    """Verify agriculture profile has no duplicate keys."""

    def test_profile_has_12_months(self):
        config = AgricultureConfig()
        assert len(config.profil_mensuel) == 12

    def test_all_months_present(self):
        config = AgricultureConfig()
        for mois in MOIS_ORDRE:
            assert mois in config.profil_mensuel, f"Missing month: {mois}"
