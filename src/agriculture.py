"""
Agriculture sector module for the Energy Transition Model.

Models agricultural energy consumption and production opportunities:
- Consumption: machinery, greenhouses, irrigation, livestock buildings
- Production: agrivoltaics, methanization (biogas)

Sources:
- Agreste (Ministère de l'Agriculture): agricultural energy statistics
- ADEME: agricultural energy efficiency studies
- RTE: agricultural electricity consumption
"""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class AgricultureConfig:
    """Agricultural sector energy parameters."""

    # --- Current consumption (TWh/year) ---
    # Source: Agreste / SDES Bilan énergétique 2022
    # Total agriculture energy: ~50 TWh (all fuels)
    # Electricity: ~12 TWh

    # Machinery (tractors, harvesters) - currently fossil
    # Source: Agreste, ~30 TWh fossil fuel
    machinisme_twh: float = 30.0

    # Greenhouses heating
    # Source: ADEME, ~10 TWh (gas + electricity)
    serres_twh: float = 10.0

    # Irrigation pumping
    # Source: Agreste, ~3 TWh electricity
    irrigation_twh: float = 3.0

    # Livestock buildings (ventilation, heating, milking)
    # Source: ADEME, ~5 TWh electricity
    elevage_twh: float = 5.0

    # Other (storage, drying, processing)
    autres_twh: float = 2.0

    # --- Electrification potential ---
    # Fraction of machinery that can be electrified (electric tractors, etc.)
    # Conservative: battery tractors for small/medium farms
    machinisme_electrifiable_fraction: float = 0.50

    # Efficiency gain from electrification (electric motors vs diesel)
    machinisme_efficacite_electrique: float = 0.35  # 35% of fossil energy needed

    # Greenhouse heat pump potential (replace gas heating)
    serres_pac_fraction: float = 0.80
    serres_pac_cop: float = 3.0

    # --- Production opportunities ---
    # Agrivoltaics: solar panels above crops
    # Source: ADEME study 2023, potential 50-100 GWc on agricultural land
    agrivoltaisme_potentiel_gwc: float = 50.0

    # Methanization: biogas from agricultural waste
    # Source: ADEME, current ~5 TWh, potential ~30 TWh
    methanisation_actuel_twh: float = 5.0
    methanisation_potentiel_twh: float = 30.0

    # --- Seasonal profile ---
    # Agriculture consumption peaks in summer (irrigation, machinery)
    # This is opposite to heating — beneficial for solar matching
    profil_mensuel: Dict[str, float] = field(default_factory=lambda: {
        'Janvier': 0.5,
        'Février': 0.6,
        'Mars': 0.8,
        'Avril': 1.0,
        'Mai': 1.3,
        'Juin': 1.5,
        'Juillet': 1.5,
        'Août': 1.3,
        'Septembre': 1.0,
        'Octobre': 0.8,
        'Novembre': 0.6,
        'Décembre': 0.5,
    })


def consommation_actuelle_twh(config: Optional[AgricultureConfig] = None) -> Dict[str, float]:
    """
    Current agricultural energy consumption breakdown.

    Args:
        config: Agriculture configuration

    Returns:
        Dict with consumption by sub-sector (TWh)
    """
    if config is None:
        config = AgricultureConfig()

    total = (config.machinisme_twh + config.serres_twh +
             config.irrigation_twh + config.elevage_twh + config.autres_twh)

    return {
        'machinisme_twh': config.machinisme_twh,
        'serres_twh': config.serres_twh,
        'irrigation_twh': config.irrigation_twh,
        'elevage_twh': config.elevage_twh,
        'autres_twh': config.autres_twh,
        'total_twh': total,
    }


def consommation_electrifiee_twh(config: Optional[AgricultureConfig] = None) -> Dict[str, float]:
    """
    Agricultural electricity consumption after electrification.

    Calculates the electricity needed when fossil uses are electrified.

    Args:
        config: Agriculture configuration

    Returns:
        Dict with electrified consumption by sub-sector (TWh)
    """
    if config is None:
        config = AgricultureConfig()

    # Machinery: electrifiable fraction × efficiency gain
    machinisme_elec = (
        config.machinisme_twh * config.machinisme_electrifiable_fraction
        * config.machinisme_efficacite_electrique
    )
    # Non-electrified machinery remains fossil
    machinisme_fossile_residuel = (
        config.machinisme_twh * (1 - config.machinisme_electrifiable_fraction)
    )

    # Greenhouses: PAC replaces gas heating
    serres_elec = (
        config.serres_twh * config.serres_pac_fraction / config.serres_pac_cop
        + config.serres_twh * (1 - config.serres_pac_fraction)
    )

    # Already electric: unchanged
    irrigation = config.irrigation_twh
    elevage = config.elevage_twh
    autres = config.autres_twh

    total_elec = machinisme_elec + serres_elec + irrigation + elevage + autres

    return {
        'machinisme_elec_twh': machinisme_elec,
        'machinisme_fossile_residuel_twh': machinisme_fossile_residuel,
        'serres_elec_twh': serres_elec,
        'irrigation_twh': irrigation,
        'elevage_twh': elevage,
        'autres_twh': autres,
        'total_elec_twh': total_elec,
    }


def production_agricole_twh(config: Optional[AgricultureConfig] = None) -> Dict[str, float]:
    """
    Agricultural energy production potential.

    Args:
        config: Agriculture configuration

    Returns:
        Dict with production by type (TWh)
    """
    if config is None:
        config = AgricultureConfig()

    # Agrivoltaics: assume 15% average capacity factor
    agrivoltaisme_twh = config.agrivoltaisme_potentiel_gwc * 0.15 * 8760 / 1000

    return {
        'agrivoltaisme_twh': agrivoltaisme_twh,
        'methanisation_actuel_twh': config.methanisation_actuel_twh,
        'methanisation_potentiel_twh': config.methanisation_potentiel_twh,
        'total_production_twh': agrivoltaisme_twh + config.methanisation_potentiel_twh,
    }


def consommation_mensuelle_twh(
    mois: str,
    config: Optional[AgricultureConfig] = None,
) -> float:
    """
    Monthly agricultural electricity consumption (electrified scenario).

    Uses seasonal profile to distribute annual consumption.

    Args:
        mois: Month name
        config: Agriculture configuration

    Returns:
        Monthly consumption in TWh
    """
    if config is None:
        config = AgricultureConfig()

    elec = consommation_electrifiee_twh(config)
    annual = elec['total_elec_twh']

    coeff = config.profil_mensuel.get(mois, 1.0)
    total_coeffs = sum(config.profil_mensuel.values())

    return annual * coeff / total_coeffs


def bilan_agriculture(config: Optional[AgricultureConfig] = None) -> Dict[str, float]:
    """
    Complete agricultural sector energy balance.

    Args:
        config: Agriculture configuration

    Returns:
        Dict with current vs electrified consumption and production
    """
    if config is None:
        config = AgricultureConfig()

    actuel = consommation_actuelle_twh(config)
    electrifie = consommation_electrifiee_twh(config)
    production = production_agricole_twh(config)

    return {
        'conso_actuelle_total_twh': actuel['total_twh'],
        'conso_electrifiee_twh': electrifie['total_elec_twh'],
        'fossile_residuel_twh': electrifie['machinisme_fossile_residuel_twh'],
        'reduction_conso_twh': actuel['total_twh'] - electrifie['total_elec_twh'] - electrifie['machinisme_fossile_residuel_twh'],
        'production_potentielle_twh': production['total_production_twh'],
        'bilan_net_twh': production['total_production_twh'] - electrifie['total_elec_twh'],
    }


def resume_agriculture(config: Optional[AgricultureConfig] = None) -> str:
    """
    Generate human-readable agriculture sector summary.

    Args:
        config: Agriculture configuration

    Returns:
        Formatted summary string
    """
    if config is None:
        config = AgricultureConfig()

    actuel = consommation_actuelle_twh(config)
    electrifie = consommation_electrifiee_twh(config)
    production = production_agricole_twh(config)
    bilan = bilan_agriculture(config)

    lines = [
        "Secteur Agriculture",
        "=" * 40,
        "",
        "Consommation actuelle (toutes énergies):",
        f"  Machinisme:   {actuel['machinisme_twh']:>6.1f} TWh (fossile)",
        f"  Serres:       {actuel['serres_twh']:>6.1f} TWh (gaz+élec)",
        f"  Irrigation:   {actuel['irrigation_twh']:>6.1f} TWh (élec)",
        f"  Élevage:      {actuel['elevage_twh']:>6.1f} TWh (élec)",
        f"  Autres:       {actuel['autres_twh']:>6.1f} TWh",
        f"  TOTAL:        {actuel['total_twh']:>6.1f} TWh",
        "",
        "Après électrification:",
        f"  Machinisme:   {electrifie['machinisme_elec_twh']:>6.1f} TWh (élec, {config.machinisme_electrifiable_fraction*100:.0f}% du parc)",
        f"  Fossile rés.: {electrifie['machinisme_fossile_residuel_twh']:>6.1f} TWh (non-électrifiable)",
        f"  Serres (PAC): {electrifie['serres_elec_twh']:>6.1f} TWh (COP {config.serres_pac_cop})",
        f"  Irrigation:   {electrifie['irrigation_twh']:>6.1f} TWh",
        f"  Élevage:      {electrifie['elevage_twh']:>6.1f} TWh",
        f"  TOTAL élec:   {electrifie['total_elec_twh']:>6.1f} TWh",
        "",
        "Production agricole:",
        f"  Agrivoltaïsme ({config.agrivoltaisme_potentiel_gwc:.0f} GWc): {production['agrivoltaisme_twh']:>6.1f} TWh",
        f"  Méthanisation:       {production['methanisation_potentiel_twh']:>6.1f} TWh",
        f"  TOTAL production:    {production['total_production_twh']:>6.1f} TWh",
        "",
        f"  Bilan net: {bilan['bilan_net_twh']:+.1f} TWh (positif = producteur net)",
    ]

    return '\n'.join(lines)
