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


def calculate_system_balance(
    ref: ReferenceData | None = None,
    params: ElectrificationParams | None = None,
) -> SystemBalance:
    """Calculate complete system balance from reference data and parameters.

    This is the single source of truth for all consumption figures.
    """
    if ref is None:
        ref = sdes_2023()
    if params is None:
        params = ElectrificationParams()

    sectors = {
        "residential": convert_residential(ref.residential, params),
        "tertiary": convert_tertiary(ref.tertiary, params),
        "industry": convert_industry(ref.industry, params),
        "transport": convert_transport(ref.transport, params),
        "agriculture": convert_agriculture(ref.agriculture, params),
        "non_energy": convert_non_energy(ref.non_energy, params),
    }
    return SystemBalance.from_sectors(sectors, params.electrolyse_efficiency)


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


def convert_tertiary(sector: SectorReference, params: ElectrificationParams) -> SectorBalance:
    """Convert tertiary sector to electrified scenario.

    229 TWh current -> ~130 TWh target.
    Renovation reduces heating demand. Fossil heating -> PAC.
    LED lighting, efficient appliances, induction cooking.
    """
    usages = {u.name: u for u in sector.usages}

    # Chauffage: renovation -30%, then fossil -> PAC
    ch = usages["chauffage"]
    reno = 1 - params.ter_renovation_gain
    ch_fossil = (ch.gaz_twh + ch.petrole_twh) * reno
    ch_elec = ch_fossil / params.ter_chauffage_cop + ch.elec_twh * reno
    ch_enr = ch.enr_twh * reno  # biomass reduced by renovation

    # Clim/ventilation: efficiency gains
    cv = usages["clim_ventilation"]
    cv_elec = cv.elec_twh * (1 - params.ter_clim_gain)

    # Eclairage: LED replacement
    ec = usages["eclairage"]
    ec_elec = ec.elec_twh * (1 - params.ter_led_gain)

    # Elec specifique: efficiency gains
    es = usages["elec_specifique"]
    es_elec = es.elec_twh * (1 - params.ter_elec_specifique_gain)

    # ECS: fossil -> PAC thermodynamique
    ecs = usages["ecs"]
    ecs_fossil = ecs.gaz_twh + ecs.petrole_twh
    ecs_elec = ecs_fossil / params.ter_ecs_cop + ecs.elec_twh

    # Cuisson: gas+oil -> induction
    cu = usages["cuisson"]
    cu_fossil = cu.gaz_twh + cu.petrole_twh
    cu_elec = cu.elec_twh + cu_fossil * 0.80

    # Autres: general efficiency, some fossil residual
    au = usages["autres"]
    au_reduced = au.total_twh * (1 - params.ter_autres_gain)
    au_fossil = params.ter_autres_fossil_residual_twh
    au_elec = au_reduced - au_fossil

    total_elec = ch_elec + cv_elec + ec_elec + es_elec + ecs_elec + cu_elec + au_elec
    total_enr = ch_enr

    return SectorBalance(
        name="tertiary",
        current_twh=sector.total_twh,
        elec_twh=round(total_elec, 1),
        h2_twh=0,
        bio_enr_twh=round(total_enr, 1),
        fossil_residual_twh=round(au_fossil, 1),
    )


def convert_industry(sector: SectorReference, params: ElectrificationParams) -> SectorBalance:
    """Convert industry sector to electrified scenario.

    283 TWh current -> ~222 TWh target.
    Three temperature tiers (HT/MT/BT) with different conversion strategies.
    HT uses fraction-based allocation (electric arcs, H2 burners).
    MT/BT use heat pumps (COP). Plus force motrice, electrochimie, etc.
    """
    usages = {u.name: u for u in sector.usages}

    # --- Chaleur haute temperature (HT): fraction-based ---
    ht = usages["chaleur_ht"]
    ht_need = ht.total_twh * (1 - params.ind_ht_efficiency_gain)
    ht_elec = ht_need * params.ind_ht_elec_fraction
    ht_h2 = ht_need * params.ind_ht_h2_fraction
    ht_fossil = params.ind_ht_fossil_residual_twh
    ht_enr = ht.enr_twh  # biomass maintained at original level

    # --- Chaleur moyenne temperature (MT): COP-based ---
    mt = usages["chaleur_mt"]
    mt_fossil = mt.gaz_twh + mt.petrole_twh + mt.charbon_twh
    mt_elec = mt_fossil / params.ind_mt_cop + mt.reseau_twh / params.ind_mt_cop + mt.elec_twh
    mt_h2 = params.ind_mt_h2_twh
    mt_enr = mt.enr_twh  # biomass maintained

    # --- Chaleur basse temperature (BT): COP-based ---
    bt = usages["chaleur_bt"]
    bt_fossil = bt.gaz_twh + bt.petrole_twh + bt.charbon_twh
    bt_elec = bt_fossil / params.ind_bt_cop + bt.reseau_twh / params.ind_bt_cop + bt.elec_twh
    bt_enr = bt.enr_twh  # biomass maintained

    # --- Force motrice: mostly already electric, efficiency gains ---
    fm = usages["force_motrice"]
    fm_elec = fm.total_twh * (1 - params.ind_force_motrice_gain)

    # --- Electrochimie: 100% electric, no change ---
    ec_elec = usages["electrochimie"].elec_twh

    # --- Eclairage industriel: all -> electric with LED gains ---
    ei = usages["eclairage_it"]
    ei_elec = ei.total_twh * (1 - params.ind_eclairage_gain)

    # --- Autres: efficiency gains, mostly electric ---
    au = usages["autres"]
    au_reduced = au.total_twh * (1 - params.ind_autres_gain)
    au_enr = au.enr_twh  # biomass maintained
    au_elec = au_reduced - au_enr

    total_elec = ht_elec + mt_elec + bt_elec + fm_elec + ec_elec + ei_elec + au_elec
    total_h2 = ht_h2 + mt_h2
    total_enr = ht_enr + mt_enr + bt_enr + au_enr
    total_fossil = ht_fossil

    return SectorBalance(
        name="industry",
        current_twh=sector.total_twh,
        elec_twh=round(total_elec, 1),
        h2_twh=round(total_h2, 1),
        bio_enr_twh=round(total_enr, 1),
        fossil_residual_twh=round(total_fossil, 1),
    )


def convert_transport(sector: SectorReference, params: ElectrificationParams) -> SectorBalance:
    """Convert transport sector to electrified scenario.

    513 TWh current -> ~245 TWh target.
    Modal shift, sobriety, EV conversion for cars/trucks/vans.
    H2 for heavy-duty and aviation. Biocarburants for residual.
    """
    usages = {u.name: u for u in sector.usages}

    # --- Voitures (200 TWh) ---
    vp = usages["voitures"]
    vp_demand = vp.total_twh * (1 - params.tpt_vp_modal_shift) * (1 - params.tpt_vp_sobriety)
    vp_ev = vp_demand * params.tpt_vp_ev_fraction
    vp_elec = vp_ev * params.tpt_vp_ev_factor
    vp_non_ev = vp_demand - vp_ev
    vp_bio = vp_non_ev * 0.58
    vp_fossil = vp_non_ev - vp_bio

    # --- Poids lourds (140 TWh) ---
    pl = usages["poids_lourds"]
    pl_demand = pl.total_twh * (1 - params.tpt_pl_rail_shift)
    pl_elec = pl_demand * params.tpt_pl_battery_fraction * params.tpt_pl_battery_factor
    pl_h2 = pl_demand * params.tpt_pl_h2_fraction * params.tpt_pl_h2_factor
    pl_bio = pl_demand * params.tpt_pl_biocarb_fraction
    pl_fossil = pl_demand * params.tpt_pl_fossil_fraction

    # --- VUL (40 TWh) ---
    vul = usages["vul"]
    vul_demand = vul.total_twh * (1 - params.tpt_vul_sobriety)
    vul_elec = vul_demand * params.tpt_vul_ev_factor
    vul_bio = 0.5  # small residual biocarb

    # --- Deux roues (10 TWh) ---
    dr_elec = usages["deux_roues"].total_twh * params.tpt_deux_roues_ev_factor

    # --- Bus/cars (15 TWh): from params ---
    bus_elec = params.tpt_bus_elec_twh
    bus_h2 = params.tpt_bus_h2_twh
    bus_bio = 1.0  # residual biogas buses

    # --- Ferroviaire (15 TWh): from params ---
    rail_elec = params.tpt_rail_elec_twh
    rail_h2 = params.tpt_rail_h2_twh

    # --- Aviation domestique (10 TWh) ---
    avd = usages["aviation_dom"]
    avd_demand = avd.total_twh * (1 - params.tpt_avia_dom_modal_shift)
    avd_elec = params.tpt_avia_dom_elec_twh
    avd_bio = params.tpt_avia_dom_biocarb_twh

    # --- Aviation internationale (55 TWh) ---
    avi = usages["aviation_intl"]
    avi_demand = avi.total_twh * (1 - params.tpt_avia_intl_sobriety)
    avi_h2 = params.tpt_avia_intl_h2_twh
    avi_bio = params.tpt_avia_intl_biocarb_twh
    avi_fossil = params.tpt_avia_intl_fossil_twh

    # --- Maritime/fluvial (18 TWh): from params ---
    mar_elec = params.tpt_maritime_elec_twh
    mar_h2 = params.tpt_maritime_h2_twh
    mar_bio = params.tpt_maritime_biocarb_twh
    mar_fossil = params.tpt_maritime_fossil_twh

    # --- Autres (10 TWh): from params ---
    aut_elec = params.tpt_autres_elec_twh

    total_elec = (vp_elec + pl_elec + vul_elec + dr_elec + bus_elec
                  + rail_elec + avd_elec + mar_elec + aut_elec)
    total_h2 = pl_h2 + bus_h2 + rail_h2 + avi_h2 + mar_h2
    total_bio = (vp_bio + pl_bio + vul_bio + bus_bio
                 + avd_bio + avi_bio + mar_bio)
    total_fossil = vp_fossil + pl_fossil + avi_fossil + mar_fossil

    return SectorBalance(
        name="transport",
        current_twh=sector.total_twh,
        elec_twh=round(total_elec, 1),
        h2_twh=round(total_h2, 1),
        bio_enr_twh=round(total_bio, 1),
        fossil_residual_twh=round(total_fossil, 1),
    )


def convert_agriculture(sector: SectorReference, params: ElectrificationParams) -> SectorBalance:
    """Convert agriculture sector to electrified scenario.

    55 TWh current -> ~36 TWh target.
    Machinisme: EV tractors, H2 harvesters, biocarburants for remaining.
    Serres/elevage: PAC for heating. Irrigation: already electric.
    """
    usages = {u.name: u for u in sector.usages}

    # --- Machinisme (30 TWh) ---
    ma = usages["machinisme"]
    ma_elec = ma.total_twh * params.agr_machinisme_ev_fraction * params.agr_machinisme_ev_factor
    # H2 fuel cells more efficient than ICE (factor ~0.70)
    ma_h2 = ma.total_twh * params.agr_machinisme_h2_fraction * 0.70
    # Biocarb: some efficiency gain from modern engines
    ma_bio = ma.total_twh * params.agr_machinisme_biocarb_fraction * 0.78
    ma_fossil = ma.total_twh * params.agr_machinisme_fossil_fraction

    # --- Serres (7 TWh): fossil -> PAC ---
    se = usages["serres"]
    se_fossil = se.gaz_twh + se.petrole_twh
    se_elec = se_fossil / params.agr_serres_cop + se.elec_twh
    se_enr = se.enr_twh

    # --- Irrigation (3 TWh): already electric ---
    ir_elec = usages["irrigation"].elec_twh

    # --- Elevage (5 TWh): fossil -> PAC + efficiency ---
    el = usages["elevage"]
    el_fossil = el.petrole_twh
    el_elec = el_fossil / params.agr_elevage_cop + el.elec_twh * (1 - params.agr_elevage_efficiency_gain)
    el_enr = el.enr_twh

    # --- Sechage (3 TWh): from params ---
    se2_elec = params.agr_sechage_elec_twh
    se2_enr = usages["sechage"].enr_twh

    # --- Peche (4 TWh): from params ---
    pe_elec = params.agr_peche_elec_twh
    pe_h2 = params.agr_peche_h2_twh
    pe_fossil = params.agr_peche_fossil_twh

    # --- Autres (3 TWh): from params ---
    au_elec = params.agr_autres_elec_twh

    total_elec = ma_elec + se_elec + ir_elec + el_elec + se2_elec + pe_elec + au_elec
    total_h2 = ma_h2 + pe_h2
    total_bio = ma_bio + se_enr + el_enr + se2_enr
    total_fossil = ma_fossil + pe_fossil

    return SectorBalance(
        name="agriculture",
        current_twh=sector.total_twh,
        elec_twh=round(total_elec, 1),
        h2_twh=round(total_h2, 1),
        bio_enr_twh=round(total_bio, 1),
        fossil_residual_twh=round(total_fossil, 1),
    )


def convert_non_energy(sector: SectorReference, params: ElectrificationParams) -> SectorBalance:
    """Convert non-energy sector to electrified scenario.

    113 TWh current -> ~95 TWh target.
    Feedstock substitution: recycling, bio-based, H2-based chemistry.
    No COP — these are material inputs, not heat.
    """
    usages = {u.name: u for u in sector.usages}

    # --- Petrochimie (60 TWh): recycling + bio + H2 + elec ---
    pc = usages["petrochimie"]
    pc_reduced = pc.total_twh * (1 - params.ne_petrochimie_recycling_gain)
    pc_bio = pc_reduced * params.ne_petrochimie_bio_fraction
    pc_h2 = pc_reduced * params.ne_petrochimie_h2_fraction
    pc_elec = params.ne_petrochimie_elec_twh
    pc_fossil = pc_reduced - pc_bio - pc_h2 - pc_elec

    # --- Engrais (18 TWh): H2 vert replaces gas ---
    en_h2 = params.ne_engrais_h2_twh
    en_fossil = params.ne_engrais_fossil_twh

    # --- Bitumes (15 TWh): recycling + bio ---
    bi = usages["bitumes"]
    bi_reduced = bi.total_twh * (1 - params.ne_bitumes_recycling_gain)
    bi_bio = bi_reduced * params.ne_bitumes_bio_fraction
    bi_fossil = bi_reduced - bi_bio

    # --- Lubrifiants (5 TWh): bio substitution ---
    lu = usages["lubrifiants"]
    lu_bio = lu.total_twh * params.ne_lubrifiants_bio_fraction
    lu_fossil = lu.total_twh - lu_bio

    # --- Solvants (5 TWh): green chemistry ---
    so = usages["solvants"]
    so_bio = so.total_twh * params.ne_solvants_green_fraction
    so_fossil = so.total_twh - so_bio

    # --- Autres (10 TWh): from params ---
    au_elec = params.ne_autres_elec_twh
    au_h2 = params.ne_autres_h2_twh
    au_bio = params.ne_autres_bio_twh
    au_fossil = params.ne_autres_fossil_twh

    total_elec = pc_elec + au_elec
    total_h2 = pc_h2 + en_h2 + au_h2
    total_bio = pc_bio + bi_bio + lu_bio + so_bio + au_bio
    total_fossil = pc_fossil + en_fossil + bi_fossil + lu_fossil + so_fossil + au_fossil

    return SectorBalance(
        name="non_energy",
        current_twh=sector.total_twh,
        elec_twh=round(total_elec, 1),
        h2_twh=round(total_h2, 1),
        bio_enr_twh=round(total_bio, 1),
        fossil_residual_twh=round(total_fossil, 1),
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
