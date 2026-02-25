"""Central consumption module — SDES 2023 reference and electrification balance.

This module is the single source of truth for all consumption figures.
Existing modules (heating, transport, agriculture) provide temporal profiles;
this module provides the annual totals.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class UsageReference:
    """One end-use within a sector (e.g. residential heating, 312 TWh).

    All vector fields are in TWh and must sum to total_twh.
    """
    name: str
    total_twh: float
    elec_twh: float
    gaz_twh: float
    petrole_twh: float
    charbon_twh: float
    enr_twh: float
    reseau_twh: float

    def __post_init__(self) -> None:
        vector_sum = (
            self.elec_twh + self.gaz_twh + self.petrole_twh
            + self.charbon_twh + self.enr_twh + self.reseau_twh
        )
        if abs(vector_sum - self.total_twh) > 0.5:
            raise ValueError(
                f"{self.name}: vectors sum to {vector_sum:.1f}, "
                f"expected {self.total_twh:.1f}"
            )

    @property
    def fossil_twh(self) -> float:
        return self.gaz_twh + self.petrole_twh + self.charbon_twh


@dataclass(frozen=True)
class SectorReference:
    """One sector (e.g. residential, 422 TWh) with its end-use breakdown."""
    name: str
    usages: tuple[UsageReference, ...] | list[UsageReference]

    @property
    def total_twh(self) -> float:
        return sum(u.total_twh for u in self.usages)

    @property
    def elec_twh(self) -> float:
        return sum(u.elec_twh for u in self.usages)

    @property
    def fossil_twh(self) -> float:
        return sum(u.fossil_twh for u in self.usages)

    @property
    def enr_twh(self) -> float:
        return sum(u.enr_twh for u in self.usages)

    @property
    def reseau_twh(self) -> float:
        return sum(u.reseau_twh for u in self.usages)


@dataclass(frozen=True)
class ReferenceData:
    """SDES 2023 complete reference: 6 sectors, 1615 TWh."""
    residential: SectorReference
    tertiary: SectorReference
    industry: SectorReference
    transport: SectorReference
    agriculture: SectorReference
    non_energy: SectorReference

    @property
    def all_sectors(self) -> list[SectorReference]:
        return [
            self.residential, self.tertiary, self.industry,
            self.transport, self.agriculture, self.non_energy,
        ]

    @property
    def total_twh(self) -> float:
        return sum(s.total_twh for s in self.all_sectors)

    def __post_init__(self) -> None:
        if abs(self.total_twh - 1615) > 2:
            raise ValueError(
                f"Grand total {self.total_twh:.1f} TWh != 1615 TWh"
            )


def sdes_2023() -> ReferenceData:
    """Return the SDES 2023 reference data for France (1615 TWh)."""
    residential = SectorReference("residential", [
        UsageReference("chauffage",        292, 50,  94, 31, 0, 105, 12),
        UsageReference("ecs",               38, 15,  15,  5, 0,   2,  1),
        UsageReference("elec_specifique",   68, 68,   0,  0, 0,   0,  0),
        UsageReference("cuisson",           22, 12,  10,  0, 0,   0,  0),
        UsageReference("climatisation",      2,  2,   0,  0, 0,   0,  0),
    ])
    tertiary = SectorReference("tertiary", [
        UsageReference("chauffage",         85, 12,  42, 10, 0,  11, 10),
        UsageReference("clim_ventilation",  20, 20,   0,  0, 0,   0,  0),
        UsageReference("eclairage",         28, 28,   0,  0, 0,   0,  0),
        UsageReference("elec_specifique",   48, 48,   0,  0, 0,   0,  0),
        UsageReference("ecs",               18,  6,  10,  2, 0,   0,  0),
        UsageReference("cuisson",           10,  3,   6,  1, 0,   0,  0),
        UsageReference("autres",            20,  7,   4,  8, 0,   0,  1),
    ])
    industry = SectorReference("industry", [
        UsageReference("chaleur_ht",        75, 10,  35, 10, 6,   5,  9),
        UsageReference("chaleur_mt",        55,  4,  30,  8, 0,   8,  5),
        UsageReference("chaleur_bt",        40,  4,  20,  5, 0,   8,  3),
        UsageReference("force_motrice",     65, 60,   3,  2, 0,   0,  0),
        UsageReference("electrochimie",     18, 18,   0,  0, 0,   0,  0),
        UsageReference("eclairage_it",      15,  3,   7,  2, 0,   3,  0),
        UsageReference("autres",            15,  3,   7,  1, 0,   1,  3),
    ])
    transport = SectorReference("transport", [
        UsageReference("voitures",         200, 2, 1, 180, 0, 17, 0),
        UsageReference("poids_lourds",     140, 0, 4, 126, 0, 10, 0),
        UsageReference("vul",               40, 0, 0,  36, 0,  4, 0),
        UsageReference("deux_roues",        10, 0, 0,  10, 0,  0, 0),
        UsageReference("bus_cars",          15, 1, 0,  13, 0,  1, 0),
        UsageReference("ferroviaire",       15, 10, 0,  5, 0,  0, 0),
        UsageReference("aviation_dom",      10, 0, 0,   9, 0,  1, 0),
        UsageReference("aviation_intl",     55, 0, 0,  50, 0,  5, 0),
        UsageReference("maritime_fluvial",  18, 0, 0,  18, 0,  0, 0),
        UsageReference("autres",            10, 0, 0,  10, 0,  0, 0),
    ])
    agriculture = SectorReference("agriculture", [
        UsageReference("machinisme",        30, 0, 0, 29, 0, 1, 0),
        UsageReference("serres",             7, 1, 3,  1, 0, 2, 0),
        UsageReference("irrigation",         3, 3, 0,  0, 0, 0, 0),
        UsageReference("elevage",            5, 2, 0,  2, 0, 1, 0),
        UsageReference("sechage",            3, 0, 0,  2, 0, 1, 0),
        UsageReference("peche",              4, 0, 0,  4, 0, 0, 0),
        UsageReference("autres",             3, 1, 0,  2, 0, 0, 0),
    ])
    non_energy = SectorReference("non_energy", [
        UsageReference("petrochimie",       60, 0, 5, 55, 0, 0, 0),
        UsageReference("engrais",           18, 0, 18, 0, 0, 0, 0),
        UsageReference("bitumes",           15, 0, 0, 15, 0, 0, 0),
        UsageReference("lubrifiants",        5, 0, 0,  5, 0, 0, 0),
        UsageReference("solvants",           5, 0, 0,  5, 0, 0, 0),
        UsageReference("autres",            10, 0, 2,  8, 0, 0, 0),
    ])
    return ReferenceData(
        residential=residential,
        tertiary=tertiary,
        industry=industry,
        transport=transport,
        agriculture=agriculture,
        non_energy=non_energy,
    )


@dataclass
class ElectrificationParams:
    """Conversion knobs — all adjustable for sensitivity analysis."""
    # Residential
    res_chauffage_cop: float = 3.5
    res_ecs_cop: float = 3.0
    res_elec_specifique_gain: float = 0.15
    res_cuisson_gain_induction: float = 0.20
    res_clim_growth_twh: float = 2.0

    # Tertiary
    ter_renovation_gain: float = 0.30
    ter_chauffage_cop: float = 3.0
    ter_clim_gain: float = 0.20
    ter_led_gain: float = 0.50
    ter_elec_specifique_gain: float = 0.15
    ter_ecs_cop: float = 3.0
    ter_autres_gain: float = 0.30
    ter_autres_fossil_residual_twh: float = 2.0

    # Industry
    ind_ht_efficiency_gain: float = 0.10
    ind_ht_elec_fraction: float = 0.30
    ind_ht_h2_fraction: float = 0.24
    ind_ht_fossil_residual_twh: float = 15.0
    ind_mt_cop: float = 2.25
    ind_mt_h2_twh: float = 5.0
    ind_mt_efficiency_gain: float = 0.15
    ind_bt_cop: float = 3.25
    ind_bt_efficiency_gain: float = 0.15
    ind_force_motrice_gain: float = 0.12
    ind_eclairage_gain: float = 0.20
    ind_autres_gain: float = 0.15

    # Transport
    tpt_vp_modal_shift: float = 0.10
    tpt_vp_sobriety: float = 0.05
    tpt_vp_ev_factor: float = 0.33
    tpt_vp_ev_fraction: float = 0.95
    tpt_pl_rail_shift: float = 0.10
    tpt_pl_battery_fraction: float = 0.50
    tpt_pl_battery_factor: float = 0.35
    tpt_pl_h2_fraction: float = 0.25
    tpt_pl_h2_factor: float = 0.70
    tpt_pl_biocarb_fraction: float = 0.15
    tpt_pl_fossil_fraction: float = 0.10
    tpt_vul_ev_factor: float = 0.33
    tpt_vul_sobriety: float = 0.05
    tpt_deux_roues_ev_factor: float = 0.30
    tpt_bus_elec_twh: float = 4.0
    tpt_bus_h2_twh: float = 2.0
    tpt_rail_elec_twh: float = 13.0
    tpt_rail_h2_twh: float = 1.0
    tpt_avia_dom_modal_shift: float = 0.50
    tpt_avia_dom_elec_twh: float = 1.0
    tpt_avia_dom_biocarb_twh: float = 4.0
    tpt_avia_intl_sobriety: float = 0.10
    tpt_avia_intl_h2_twh: float = 5.0
    tpt_avia_intl_biocarb_twh: float = 15.0
    tpt_avia_intl_fossil_twh: float = 25.0
    tpt_maritime_elec_twh: float = 2.0
    tpt_maritime_h2_twh: float = 3.0
    tpt_maritime_biocarb_twh: float = 3.0
    tpt_maritime_fossil_twh: float = 8.0
    tpt_autres_elec_twh: float = 8.0

    # Agriculture
    agr_machinisme_ev_fraction: float = 0.40
    agr_machinisme_ev_factor: float = 0.35
    agr_machinisme_h2_fraction: float = 0.20
    agr_machinisme_biocarb_fraction: float = 0.30
    agr_machinisme_fossil_fraction: float = 0.10
    agr_serres_cop: float = 3.0
    agr_elevage_cop: float = 3.0
    agr_elevage_efficiency_gain: float = 0.10
    agr_peche_elec_twh: float = 1.0
    agr_peche_h2_twh: float = 1.0
    agr_peche_fossil_twh: float = 1.0
    agr_sechage_elec_twh: float = 1.0
    agr_autres_elec_twh: float = 2.0

    # Non-energy
    ne_petrochimie_recycling_gain: float = 0.20
    ne_petrochimie_bio_fraction: float = 0.30
    ne_petrochimie_h2_fraction: float = 0.20
    ne_petrochimie_elec_twh: float = 3.0
    ne_engrais_h2_twh: float = 16.0
    ne_engrais_fossil_twh: float = 2.0
    ne_bitumes_recycling_gain: float = 0.20
    ne_bitumes_bio_fraction: float = 0.30
    ne_lubrifiants_bio_fraction: float = 0.50
    ne_solvants_green_fraction: float = 0.60
    ne_autres_elec_twh: float = 2.0
    ne_autres_h2_twh: float = 2.0
    ne_autres_bio_twh: float = 2.0
    ne_autres_fossil_twh: float = 2.0

    # System
    electrolyse_efficiency: float = 0.65
    ccgt_efficiency: float = 0.55


def convert_residential(sector: SectorReference, params: ElectrificationParams) -> SectorBalance:
    """Convert residential sector to electrified scenario.

    422 TWh current -> ~282 TWh target.
    Fossil heating/ECS replaced by PAC (heat pumps).
    Some wood heating also switches to PAC.
    Cooking switches to induction. Efficiency gains on appliances.
    """
    usages = {u.name: u for u in sector.usages}

    # Chauffage: fossil -> PAC, most bois maintained, reseau maintained
    ch = usages["chauffage"]
    ch_fossil = ch.gaz_twh + ch.petrole_twh + ch.charbon_twh
    # A fraction of wood heating also switches to PAC
    bois_to_pac = ch.enr_twh * 0.12
    ch_elec = (ch_fossil / params.res_chauffage_cop
               + ch.elec_twh * 0.7
               + bois_to_pac / params.res_chauffage_cop)
    ch_enr = (ch.enr_twh - bois_to_pac) + ch.reseau_twh

    # ECS: fossil -> PAC thermodynamique
    ecs = usages["ecs"]
    ecs_fossil = ecs.gaz_twh + ecs.petrole_twh
    ecs_elec = ecs_fossil / params.res_ecs_cop + ecs.elec_twh
    ecs_enr = ecs.enr_twh + ecs.reseau_twh

    # Elec specifique: efficiency gains
    es = usages["elec_specifique"]
    es_elec = es.elec_twh * (1 - params.res_elec_specifique_gain)

    # Cuisson: gas -> induction
    cu = usages["cuisson"]
    cu_elec = cu.elec_twh + cu.gaz_twh * (1 - params.res_cuisson_gain_induction)

    # Climatisation: maintained + growth
    cl_elec = usages["climatisation"].elec_twh + params.res_clim_growth_twh

    total_elec = ch_elec + ecs_elec + es_elec + cu_elec + cl_elec
    total_enr = ch_enr + ecs_enr

    return SectorBalance(
        name="residential",
        current_twh=sector.total_twh,
        elec_twh=round(total_elec, 1),
        h2_twh=0,
        bio_enr_twh=round(total_enr, 1),
        fossil_residual_twh=0,
    )


@dataclass(frozen=True)
class SectorBalance:
    """Electrification result for one sector."""
    name: str
    current_twh: float
    elec_twh: float
    h2_twh: float
    bio_enr_twh: float
    fossil_residual_twh: float

    @property
    def total_target_twh(self) -> float:
        return self.elec_twh + self.h2_twh + self.bio_enr_twh + self.fossil_residual_twh

    @property
    def reduction_pct(self) -> float:
        if self.current_twh == 0:
            return 0.0
        return (self.current_twh - self.total_target_twh) / self.current_twh


@dataclass(frozen=True)
class SystemBalance:
    """Complete system balance across all sectors."""
    sectors: dict[str, SectorBalance]
    current_total_twh: float
    direct_electricity_twh: float
    h2_demand_twh: float
    h2_production_elec_twh: float
    total_electricity_twh: float
    bio_enr_twh: float
    fossil_residual_twh: float

    @classmethod
    def from_sectors(
        cls, sectors: dict[str, SectorBalance], electrolyse_efficiency: float,
    ) -> SystemBalance:
        current = sum(s.current_twh for s in sectors.values())
        elec = sum(s.elec_twh for s in sectors.values())
        h2 = sum(s.h2_twh for s in sectors.values())
        h2_elec = h2 / electrolyse_efficiency
        bio = sum(s.bio_enr_twh for s in sectors.values())
        fossil = sum(s.fossil_residual_twh for s in sectors.values())
        return cls(
            sectors=sectors,
            current_total_twh=current,
            direct_electricity_twh=elec,
            h2_demand_twh=h2,
            h2_production_elec_twh=h2_elec,
            total_electricity_twh=elec + h2_elec,
            bio_enr_twh=bio,
            fossil_residual_twh=fossil,
        )
