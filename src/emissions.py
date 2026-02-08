"""
CO2 emissions and decarbonization metrics module.

Calculates greenhouse gas emissions for energy scenarios and compares
with current French emissions to quantify decarbonization progress.

Sources:
- ADEME Base Carbone: emission factors by energy source
- CITEPA/SECTEN: French national emissions inventory
- Haut Conseil pour le Climat: annual reports
"""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class EmissionsConfig:
    """
    CO2 emission factors and reference data.

    All emission factors in tCO2/MWh (= MtCO2/TWh).
    """

    # --- Emission factors by energy source (tCO2/MWh) ---
    # Source: ADEME Base Carbone 2024

    # Natural gas CCGT (Combined Cycle Gas Turbine)
    # Direct combustion: ~0.227 tCO2/MWh_elec (including upstream: ~0.243)
    facteur_gaz_tco2_par_mwh: float = 0.227

    # Coal power plant (for reference/comparison)
    facteur_charbon_tco2_par_mwh: float = 0.986

    # Oil/diesel power plant
    facteur_fioul_tco2_par_mwh: float = 0.730

    # Nuclear (lifecycle, very low)
    facteur_nucleaire_tco2_par_mwh: float = 0.006

    # Solar PV (lifecycle: manufacturing, transport, installation)
    facteur_solaire_tco2_par_mwh: float = 0.032

    # Hydro (lifecycle)
    facteur_hydro_tco2_par_mwh: float = 0.006

    # --- Current French emissions by sector (MtCO2eq/year) ---
    # Source: CITEPA/SECTEN 2023 (data for 2022)

    # Transport (largest emitting sector)
    emissions_transport_mt: float = 130.0

    # Residential/tertiary buildings (heating, hot water)
    emissions_batiments_mt: float = 75.0

    # Industry
    emissions_industrie_mt: float = 72.0

    # Agriculture
    emissions_agriculture_mt: float = 81.0

    # Energy production/transformation
    emissions_energie_mt: float = 44.0

    # Waste treatment
    emissions_dechets_mt: float = 15.0

    # --- Reference: France total (2022) ---
    # Source: Haut Conseil pour le Climat, rapport annuel 2023
    emissions_france_total_mt: float = 408.0

    # --- Targets ---
    # Source: Stratégie Nationale Bas Carbone (SNBC)
    objectif_2030_mt: float = 270.0   # -40% vs 1990
    objectif_2050_mt: float = 80.0    # Neutralité carbone (hors puits)


def emissions_gaz_backup_mt(
    gaz_twh: float,
    config: Optional[EmissionsConfig] = None,
) -> float:
    """
    Calculate CO2 emissions from gas backup generation.

    Args:
        gaz_twh: Gas-fired electricity generation in TWh
        config: Emissions configuration

    Returns:
        CO2 emissions in MtCO2
    """
    if config is None:
        config = EmissionsConfig()

    # TWh × 1000 = GWh × 1000 = MWh; factor is tCO2/MWh = MtCO2/TWh
    return gaz_twh * config.facteur_gaz_tco2_par_mwh


def emissions_parc_production_mt(
    nucleaire_twh: float,
    solaire_twh: float,
    hydro_twh: float,
    gaz_twh: float,
    config: Optional[EmissionsConfig] = None,
) -> Dict[str, float]:
    """
    Calculate CO2 emissions for the full electricity production mix.

    Args:
        nucleaire_twh: Nuclear generation (TWh)
        solaire_twh: Solar generation (TWh)
        hydro_twh: Hydro generation (TWh)
        gaz_twh: Gas backup generation (TWh)
        config: Emissions configuration

    Returns:
        Dict with emissions by source and total (MtCO2)
    """
    if config is None:
        config = EmissionsConfig()

    emissions = {
        'nucleaire_mt': nucleaire_twh * config.facteur_nucleaire_tco2_par_mwh,
        'solaire_mt': solaire_twh * config.facteur_solaire_tco2_par_mwh,
        'hydro_mt': hydro_twh * config.facteur_hydro_tco2_par_mwh,
        'gaz_mt': gaz_twh * config.facteur_gaz_tco2_par_mwh,
    }
    emissions['total_mt'] = sum(emissions.values())

    return emissions


def emissions_evitees_mt(
    gaz_twh: float,
    config: Optional[EmissionsConfig] = None,
) -> Dict[str, float]:
    """
    Calculate avoided emissions from electrification of heating and transport.

    Compares the scenario's residual gas emissions against current sector emissions
    that would be eliminated by electrification.

    Args:
        gaz_twh: Residual gas backup in TWh
        config: Emissions configuration

    Returns:
        Dict with:
        - emissions_residuelles_mt: remaining emissions from gas backup
        - emissions_evitees_transport_mt: avoided transport emissions
        - emissions_evitees_batiments_mt: avoided building emissions
        - total_evitees_mt: net avoided emissions
    """
    if config is None:
        config = EmissionsConfig()

    residuelles = emissions_gaz_backup_mt(gaz_twh, config)

    # Electrification of transport eliminates most fossil fuel emissions
    # Fraction computed from detailed transport module (aviation + heavy trucking remain)
    from src.transport import bilan_transport
    bilan_t = bilan_transport()
    fraction_transport_evitee = bilan_t['fraction_fossile_evitee']
    evitees_transport = config.emissions_transport_mt * fraction_transport_evitee

    # Electrification of heating eliminates fossil fuel heating emissions
    # Conservative: 90% of building emissions avoided
    evitees_batiments = config.emissions_batiments_mt * 0.90

    total_evitees = evitees_transport + evitees_batiments - residuelles

    return {
        'emissions_residuelles_mt': residuelles,
        'emissions_evitees_transport_mt': evitees_transport,
        'emissions_evitees_batiments_mt': evitees_batiments,
        'total_evitees_mt': total_evitees,
    }


def bilan_carbone(
    gaz_twh: float,
    nucleaire_twh: float = 400.0,
    solaire_twh: float = 300.0,
    hydro_twh: float = 65.0,
    config: Optional[EmissionsConfig] = None,
) -> Dict[str, float]:
    """
    Complete carbon balance for the energy transition scenario.

    Args:
        gaz_twh: Gas backup generation (TWh)
        nucleaire_twh: Nuclear generation (TWh), default ~current level
        solaire_twh: Solar generation (TWh)
        hydro_twh: Hydro generation (TWh)
        config: Emissions configuration

    Returns:
        Comprehensive carbon balance dict
    """
    if config is None:
        config = EmissionsConfig()

    # Production emissions
    prod = emissions_parc_production_mt(nucleaire_twh, solaire_twh, hydro_twh, gaz_twh, config)

    # Avoided emissions
    evitees = emissions_evitees_mt(gaz_twh, config)

    # Current France total for comparison
    france_actuelle = config.emissions_france_total_mt

    # Scenario total: current emissions - avoided + residual electricity emissions
    # (but residual is already subtracted in evitees calculation)
    scenario_total = france_actuelle - evitees['total_evitees_mt']

    return {
        # Production mix emissions
        'emissions_production_mt': prod['total_mt'],
        'emissions_gaz_mt': prod['gaz_mt'],
        'emissions_nucleaire_mt': prod['nucleaire_mt'],
        'emissions_solaire_mt': prod['solaire_mt'],
        'emissions_hydro_mt': prod['hydro_mt'],

        # Avoided emissions
        'evitees_transport_mt': evitees['emissions_evitees_transport_mt'],
        'evitees_batiments_mt': evitees['emissions_evitees_batiments_mt'],
        'total_evitees_mt': evitees['total_evitees_mt'],

        # Overall balance
        'france_actuelle_mt': france_actuelle,
        'scenario_total_mt': scenario_total,
        'reduction_mt': france_actuelle - scenario_total,
        'reduction_pct': (france_actuelle - scenario_total) / france_actuelle * 100,

        # vs targets
        'vs_objectif_2030_mt': scenario_total - config.objectif_2030_mt,
        'vs_objectif_2050_mt': scenario_total - config.objectif_2050_mt,
    }


def resume_emissions(
    gaz_twh: float = 114.0,
    config: Optional[EmissionsConfig] = None,
) -> str:
    """
    Generate a human-readable CO2 emissions summary.

    Args:
        gaz_twh: Gas backup in TWh (default: 114 TWh from baseline scenario)
        config: Emissions configuration

    Returns:
        Formatted summary string
    """
    if config is None:
        config = EmissionsConfig()

    bilan = bilan_carbone(gaz_twh, config=config)

    lines = [
        "Bilan Carbone - Transition Énergétique",
        "=" * 45,
        "",
        f"Gaz de backup: {gaz_twh:.0f} TWh/an",
        "",
        "Émissions du mix électrique:",
        f"  Gaz:       {bilan['emissions_gaz_mt']:>6.1f} MtCO2",
        f"  Nucléaire: {bilan['emissions_nucleaire_mt']:>6.1f} MtCO2",
        f"  Solaire:   {bilan['emissions_solaire_mt']:>6.1f} MtCO2",
        f"  Hydro:     {bilan['emissions_hydro_mt']:>6.1f} MtCO2",
        f"  TOTAL:     {bilan['emissions_production_mt']:>6.1f} MtCO2",
        "",
        "Émissions évitées par l'électrification:",
        f"  Transport:  {bilan['evitees_transport_mt']:>6.1f} MtCO2 (80% du secteur)",
        f"  Bâtiments:  {bilan['evitees_batiments_mt']:>6.1f} MtCO2 (90% du secteur)",
        f"  - Résiduel gaz: -{bilan['emissions_gaz_mt']:>4.1f} MtCO2",
        f"  NET ÉVITÉ:  {bilan['total_evitees_mt']:>6.1f} MtCO2",
        "",
        "Bilan national:",
        f"  France actuelle:    {bilan['france_actuelle_mt']:>6.0f} MtCO2/an",
        f"  Après transition:   {bilan['scenario_total_mt']:>6.0f} MtCO2/an",
        f"  Réduction:          {bilan['reduction_mt']:>6.0f} MtCO2 ({bilan['reduction_pct']:.0f}%)",
        "",
        "Vs objectifs SNBC:",
        f"  Objectif 2030 (270 Mt): {bilan['vs_objectif_2030_mt']:>+6.0f} MtCO2",
        f"  Objectif 2050 (80 Mt):  {bilan['vs_objectif_2050_mt']:>+6.0f} MtCO2",
    ]

    return '\n'.join(lines)
