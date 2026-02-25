"""
Transport sector module for the Energy Transition Model.

Detailed modal breakdown of French transport energy consumption
and electrification pathways: road passenger, road freight, rail,
aviation, and maritime/fluvial.

Sources:
- SDES Bilan energetique de la France 2022
- ADEME: transport energy efficiency studies
- CITEPA/SECTEN: transport CO2 emissions
- DGAC: aviation fuel consumption
- RTE Futurs Energetiques 2050
"""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class TransportConfig:
    """French transport sector energy parameters."""

    # --- Road passenger (TWh/year) ---
    # Source: SDES Bilan energetique 2022 / CCFA

    # Voitures particulieres: ~38M vehicles
    voitures_twh: float = 200.0

    # 2-roues motorises
    deux_roues_twh: float = 10.0

    # Bus et cars (urban + interurban)
    bus_cars_twh: float = 15.0

    # EV motor efficiency vs ICE (~90% vs ~30%)
    # Source: ADEME
    voitures_facteur_electrification: float = 0.33
    deux_roues_facteur_electrification: float = 0.33
    bus_facteur_electrification: float = 0.40

    # Modal shift: fraction of car-km redirected to rail/bus/bike
    # Source: ADEME ZEN 2050, RTE M23
    report_modal_fraction: float = 0.15

    # --- Road freight (TWh/year) ---
    # Source: SDES / CGDD Comptes des transports 2022

    # Poids lourds (>3.5t)
    poids_lourds_twh: float = 140.0

    # Vehicules utilitaires legers (<3.5t)
    vul_twh: float = 30.0

    # PL electrification pathways
    # Source: ADEME / France Hydrogene / RTE FE2050
    pl_batterie_fraction: float = 0.40
    pl_batterie_facteur: float = 0.35

    pl_hydrogene_fraction: float = 0.30
    pl_hydrogene_facteur: float = 0.55  # Electrolysis + fuel cell chain

    pl_fossile_residuel_fraction: float = 0.30  # Biofuel / e-diesel

    # VUL: mostly electrifiable (urban delivery)
    vul_facteur_electrification: float = 0.35
    vul_electrifiable_fraction: float = 0.90

    # --- Rail (TWh/year) ---
    # Source: SDES / SNCF Rapport annuel 2022
    rail_total_twh: float = 15.0
    rail_electrique_fraction: float = 0.80
    rail_diesel_electrifiable_fraction: float = 0.90
    rail_efficacite_electrique: float = 0.50

    # --- Aviation (TWh/year) ---
    # Source: DGAC / CITEPA
    aviation_domestique_twh: float = 8.0
    aviation_international_twh: float = 52.0

    # Domestic short-haul modal shift to TGV
    # Source: Loi Climat et Resilience 2021
    aviation_domestique_report_tgv_fraction: float = 0.40

    # Synthetic aviation fuel (e-kerosene / SAF)
    # Efficiency: electricity -> H2 -> Fischer-Tropsch
    # Source: ADEME, ICCT
    aviation_saf_fraction: float = 0.30
    aviation_saf_facteur_elec: float = 3.5  # kWh_elec per kWh_kerosene

    # --- Maritime and fluvial (TWh/year) ---
    # Source: SDES / DGITM
    maritime_twh: float = 7.0
    fluvial_twh: float = 3.0

    maritime_electrifiable_fraction: float = 0.30
    maritime_electrique_facteur: float = 0.40

    fluvial_electrifiable_fraction: float = 0.70
    fluvial_electrique_facteur: float = 0.40

    # --- Sobriety gains ---
    # Source: ADEME scenario "sufficiency", negaWatt 2022
    # Telecommuting, 110 km/h limit, vehicle downsizing
    gain_sobriete_fraction: float = 0.10

    # --- Charging profile (distribution across time slots) ---
    # Source: ENEDIS / RTE FE2050 managed charging
    profil_recharge: Dict[str, float] = field(default_factory=lambda: {
        '8h-13h': 0.15,
        '13h-18h': 0.25,
        '18h-20h': 0.20,
        '20h-23h': 0.15,
        '23h-8h': 0.25,
    })


def consommation_actuelle_twh(
    config: Optional[TransportConfig] = None,
) -> Dict[str, float]:
    """
    Current transport energy consumption breakdown by mode.

    Args:
        config: Transport configuration

    Returns:
        Dict with consumption per mode and subtotals (TWh)
    """
    if config is None:
        config = TransportConfig()

    routier_passagers = config.voitures_twh + config.deux_roues_twh + config.bus_cars_twh
    routier_fret = config.poids_lourds_twh + config.vul_twh
    aviation = config.aviation_domestique_twh + config.aviation_international_twh
    maritime_fluvial = config.maritime_twh + config.fluvial_twh

    total = routier_passagers + routier_fret + config.rail_total_twh + aviation + maritime_fluvial

    return {
        'voitures_twh': config.voitures_twh,
        'deux_roues_twh': config.deux_roues_twh,
        'bus_cars_twh': config.bus_cars_twh,
        'routier_passagers_twh': routier_passagers,
        'poids_lourds_twh': config.poids_lourds_twh,
        'vul_twh': config.vul_twh,
        'routier_fret_twh': routier_fret,
        'rail_twh': config.rail_total_twh,
        'aviation_domestique_twh': config.aviation_domestique_twh,
        'aviation_international_twh': config.aviation_international_twh,
        'aviation_twh': aviation,
        'maritime_twh': config.maritime_twh,
        'fluvial_twh': config.fluvial_twh,
        'maritime_fluvial_twh': maritime_fluvial,
        'total_twh': total,
    }


def consommation_electrifiee_twh(
    config: Optional[TransportConfig] = None,
) -> Dict[str, float]:
    """
    Electricity consumption after transport electrification.

    For each mode, applies efficiency gains, modal shift, and
    electrification factors. Separates direct grid electricity
    from residual fossil.

    Args:
        config: Transport configuration

    Returns:
        Dict with electrified consumption and residual fossil (TWh)
    """
    if config is None:
        config = TransportConfig()

    # --- Road passenger ---
    # Voitures: sobriety -> modal shift -> EV efficiency
    voitures_apres_sobriete = config.voitures_twh * (1 - config.gain_sobriete_fraction)
    voitures_apres_report = voitures_apres_sobriete * (1 - config.report_modal_fraction)
    voitures_elec = voitures_apres_report * config.voitures_facteur_electrification

    deux_roues_elec = config.deux_roues_twh * config.deux_roues_facteur_electrification

    bus_elec = config.bus_cars_twh * config.bus_facteur_electrification

    routier_passagers_elec = voitures_elec + deux_roues_elec + bus_elec

    # --- Road freight ---
    # Poids lourds: three pathways
    pl_elec_batterie = (config.poids_lourds_twh * config.pl_batterie_fraction
                        * config.pl_batterie_facteur)
    pl_elec_hydrogene = (config.poids_lourds_twh * config.pl_hydrogene_fraction
                         * config.pl_hydrogene_facteur)
    pl_fossile = config.poids_lourds_twh * config.pl_fossile_residuel_fraction

    # VUL: mostly electrifiable
    vul_elec = (config.vul_twh * config.vul_electrifiable_fraction
                * config.vul_facteur_electrification)
    vul_fossile = config.vul_twh * (1 - config.vul_electrifiable_fraction)

    routier_fret_elec = pl_elec_batterie + pl_elec_hydrogene + vul_elec
    routier_fret_fossile = pl_fossile + vul_fossile

    # --- Rail ---
    # Already electric portion unchanged, electrify diesel
    rail_deja_elec = config.rail_total_twh * config.rail_electrique_fraction
    rail_diesel = config.rail_total_twh * (1 - config.rail_electrique_fraction)
    rail_diesel_elec = (rail_diesel * config.rail_diesel_electrifiable_fraction
                        * config.rail_efficacite_electrique)
    rail_diesel_restant = rail_diesel * (1 - config.rail_diesel_electrifiable_fraction)
    rail_elec = rail_deja_elec + rail_diesel_elec + rail_diesel_restant

    # --- Aviation ---
    # Domestic: partial shift to TGV
    aviation_dom_restant = config.aviation_domestique_twh * (1 - config.aviation_domestique_report_tgv_fraction)
    aviation_kerosene_total = aviation_dom_restant + config.aviation_international_twh

    # SAF: electricity-intensive synthetic fuel
    aviation_saf_elec = (aviation_kerosene_total * config.aviation_saf_fraction
                         * config.aviation_saf_facteur_elec)
    aviation_fossile = aviation_kerosene_total * (1 - config.aviation_saf_fraction)

    # --- Maritime / fluvial ---
    maritime_elec = (config.maritime_twh * config.maritime_electrifiable_fraction
                     * config.maritime_electrique_facteur)
    maritime_fossile = config.maritime_twh * (1 - config.maritime_electrifiable_fraction)

    fluvial_elec = (config.fluvial_twh * config.fluvial_electrifiable_fraction
                    * config.fluvial_electrique_facteur)
    fluvial_fossile = config.fluvial_twh * (1 - config.fluvial_electrifiable_fraction)

    # --- Totals ---
    total_elec = (routier_passagers_elec + routier_fret_elec + rail_elec
                  + aviation_saf_elec + maritime_elec + fluvial_elec)
    total_fossile = (routier_fret_fossile + aviation_fossile
                     + maritime_fossile + fluvial_fossile)

    return {
        'voitures_elec_twh': voitures_elec,
        'deux_roues_elec_twh': deux_roues_elec,
        'bus_elec_twh': bus_elec,
        'routier_passagers_elec_twh': routier_passagers_elec,
        'pl_elec_batterie_twh': pl_elec_batterie,
        'pl_elec_hydrogene_twh': pl_elec_hydrogene,
        'pl_fossile_residuel_twh': pl_fossile,
        'vul_elec_twh': vul_elec,
        'vul_fossile_residuel_twh': vul_fossile,
        'routier_fret_elec_twh': routier_fret_elec,
        'routier_fret_fossile_twh': routier_fret_fossile,
        'rail_elec_twh': rail_elec,
        'aviation_elec_saf_twh': aviation_saf_elec,
        'aviation_fossile_residuel_twh': aviation_fossile,
        'maritime_elec_twh': maritime_elec,
        'maritime_fossile_residuel_twh': maritime_fossile,
        'fluvial_elec_twh': fluvial_elec,
        'fluvial_fossile_residuel_twh': fluvial_fossile,
        'total_elec_twh': total_elec,
        'total_fossile_residuel_twh': total_fossile,
    }


def facteurs_effectifs(
    config: Optional[TransportConfig] = None,
) -> Dict[str, float]:
    """
    Compute effective electrification factors for backward compatibility
    with the legacy transport_passenger_factor and transport_freight_factor.

    Args:
        config: Transport configuration

    Returns:
        Dict with effective factors per segment and global
    """
    if config is None:
        config = TransportConfig()

    actuel = consommation_actuelle_twh(config)
    electrifie = consommation_electrifiee_twh(config)

    facteur_passagers = electrifie['routier_passagers_elec_twh'] / actuel['routier_passagers_twh']
    facteur_fret = electrifie['routier_fret_elec_twh'] / actuel['routier_fret_twh']
    facteur_global = electrifie['total_elec_twh'] / actuel['total_twh']

    return {
        'facteur_passagers_effectif': facteur_passagers,
        'facteur_fret_effectif': facteur_fret,
        'facteur_global_effectif': facteur_global,
    }


def demande_recharge_par_plage(
    plage: str,
    config: Optional[TransportConfig] = None,
) -> float:
    """
    EV charging electricity demand for a given time slot (TWh/year).

    Distributes direct road transport electricity (excluding SAF
    industrial process) across time slots using the charging profile.

    Args:
        plage: Time slot name (e.g. '8h-13h')
        config: Transport configuration

    Returns:
        Charging demand for this slot (TWh/year)
    """
    if config is None:
        config = TransportConfig()

    electrifie = consommation_electrifiee_twh(config)

    # Direct grid electricity: road + rail (exclude SAF which is industrial)
    direct_elec = (electrifie['routier_passagers_elec_twh']
                   + electrifie['routier_fret_elec_twh']
                   + electrifie['maritime_elec_twh']
                   + electrifie['fluvial_elec_twh'])

    coefficient = config.profil_recharge.get(plage, 0.0)
    return direct_elec * coefficient


def bilan_transport(
    config: Optional[TransportConfig] = None,
) -> Dict[str, float]:
    """
    Complete transport sector energy balance.

    Args:
        config: Transport configuration

    Returns:
        Dict with current, electrified, residual fossil, and reduction
    """
    if config is None:
        config = TransportConfig()

    actuel = consommation_actuelle_twh(config)
    electrifie = consommation_electrifiee_twh(config)
    facteurs = facteurs_effectifs(config)

    reduction = (actuel['total_twh'] - electrifie['total_elec_twh']
                 - electrifie['total_fossile_residuel_twh'])

    return {
        'conso_actuelle_total_twh': actuel['total_twh'],
        'conso_electrifiee_twh': electrifie['total_elec_twh'],
        'fossile_residuel_twh': electrifie['total_fossile_residuel_twh'],
        'reduction_conso_twh': reduction,
        'facteur_passagers_effectif': facteurs['facteur_passagers_effectif'],
        'facteur_fret_effectif': facteurs['facteur_fret_effectif'],
        'fraction_fossile_evitee': 1 - (electrifie['total_fossile_residuel_twh']
                                         / actuel['total_twh']),
    }


def resume_transport(
    config: Optional[TransportConfig] = None,
) -> str:
    """
    Generate human-readable transport sector summary.

    Args:
        config: Transport configuration

    Returns:
        Formatted summary string
    """
    if config is None:
        config = TransportConfig()

    actuel = consommation_actuelle_twh(config)
    electrifie = consommation_electrifiee_twh(config)
    bilan = bilan_transport(config)
    facteurs = facteurs_effectifs(config)

    lines = [
        "Secteur Transport",
        "=" * 50,
        "",
        "CONSOMMATION ACTUELLE",
        f"  Routier passagers:     {actuel['routier_passagers_twh']:>6.1f} TWh",
        f"    Voitures:            {actuel['voitures_twh']:>6.1f} TWh",
        f"    2-roues:             {actuel['deux_roues_twh']:>6.1f} TWh",
        f"    Bus/cars:            {actuel['bus_cars_twh']:>6.1f} TWh",
        f"  Routier fret:          {actuel['routier_fret_twh']:>6.1f} TWh",
        f"    Poids lourds:        {actuel['poids_lourds_twh']:>6.1f} TWh",
        f"    VUL:                 {actuel['vul_twh']:>6.1f} TWh",
        f"  Rail:                  {actuel['rail_twh']:>6.1f} TWh",
        f"  Aviation:              {actuel['aviation_twh']:>6.1f} TWh",
        f"    Domestique:          {actuel['aviation_domestique_twh']:>6.1f} TWh",
        f"    International:       {actuel['aviation_international_twh']:>6.1f} TWh",
        f"  Maritime/fluvial:      {actuel['maritime_fluvial_twh']:>6.1f} TWh",
        f"  TOTAL:                 {actuel['total_twh']:>6.1f} TWh",
        "",
        "APRES ELECTRIFICATION",
        f"  Routier passagers:     {electrifie['routier_passagers_elec_twh']:>6.1f} TWh (elec)",
        f"    Voitures (EV):       {electrifie['voitures_elec_twh']:>6.1f} TWh",
        f"    2-roues (elec):      {electrifie['deux_roues_elec_twh']:>6.1f} TWh",
        f"    Bus (elec):          {electrifie['bus_elec_twh']:>6.1f} TWh",
        f"  Routier fret:          {electrifie['routier_fret_elec_twh']:>6.1f} TWh (elec)"
        f" + {electrifie['routier_fret_fossile_twh']:>5.1f} TWh (fossile res.)",
        f"    PL batterie:         {electrifie['pl_elec_batterie_twh']:>6.1f} TWh",
        f"    PL hydrogene:        {electrifie['pl_elec_hydrogene_twh']:>6.1f} TWh",
        f"    PL fossile res.:     {electrifie['pl_fossile_residuel_twh']:>6.1f} TWh",
        f"    VUL (elec):          {electrifie['vul_elec_twh']:>6.1f} TWh",
        f"  Rail:                  {electrifie['rail_elec_twh']:>6.1f} TWh (elec)",
        f"  Aviation (SAF):        {electrifie['aviation_elec_saf_twh']:>6.1f} TWh (elec)"
        f" + {electrifie['aviation_fossile_residuel_twh']:>5.1f} TWh (kerosene res.)",
        f"  Maritime/fluvial:      {electrifie['maritime_elec_twh'] + electrifie['fluvial_elec_twh']:>6.1f} TWh (elec)"
        f" + {electrifie['maritime_fossile_residuel_twh'] + electrifie['fluvial_fossile_residuel_twh']:>5.1f} TWh (fossile res.)",
        "",
        "SYNTHESE",
        f"  Consommation actuelle: {bilan['conso_actuelle_total_twh']:>6.1f} TWh",
        f"  Electricite requise:   {bilan['conso_electrifiee_twh']:>6.1f} TWh",
        f"  Fossile residuel:      {bilan['fossile_residuel_twh']:>6.1f} TWh",
        f"  Reduction (efficacite):{bilan['reduction_conso_twh']:>6.1f} TWh",
        f"  Facteur passagers:     {facteurs['facteur_passagers_effectif']:>6.2f} (ancien: 0.20)",
        f"  Facteur fret:          {facteurs['facteur_fret_effectif']:>6.2f} (ancien: 0.40)",
    ]

    return '\n'.join(lines)


def profil_recharge_normalise(
    config: Optional[TransportConfig] = None,
) -> list[list[float]]:
    """Return a 12x5 normalized EV charging profile.

    12 months x 5 time slots, all 60 values summing to 1.0.
    Uses the charging profile from TransportConfig for daily distribution
    and assumes flat monthly variation (transport is roughly constant
    year-round). The TOTAL TWh comes from consumption.py, not from
    this function.

    Time slots: 8h-13h(0), 13h-18h(1), 18h-20h(2), 20h-23h(3), 23h-8h(4)

    Args:
        config: Transport configuration (uses defaults if None)

    Returns:
        List of 12 lists, each with 5 floats; grand total = 1.0
    """
    if config is None:
        config = TransportConfig()

    # Extract daily slot distribution from config
    slot_keys = ['8h-13h', '13h-18h', '18h-20h', '20h-23h', '23h-8h']
    daily_raw = [config.profil_recharge.get(k, 0.0) for k in slot_keys]

    # Normalize daily profile to sum to 1.0 (should already be ~1.0)
    daily_total = sum(daily_raw)
    if daily_total == 0:
        daily_norm = [0.2] * 5
    else:
        daily_norm = [v / daily_total for v in daily_raw]

    # Flat monthly distribution: each month gets 1/12 of the year
    monthly_weight = 1.0 / 12.0

    # Build 12x5 matrix: each cell = monthly_weight * daily_slot_fraction
    return [
        [monthly_weight * slot for slot in daily_norm]
        for _ in range(12)
    ]
