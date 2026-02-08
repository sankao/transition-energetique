"""
Industrialisation module for the Energy Transition Model.

Models the SUPPLY SIDE constraints for reaching the target scenario:
- Manufacturing capacity for PV panels, batteries, heat pumps
- Workforce requirements (installers, electricians)
- Raw materials (silicon, lithium, copper)
- Factory construction lead times
- Bottleneck analysis to identify deployment-limiting factors

This module complements trajectory.py (which models the S-curve deployment
and learning curves) by checking whether the industrial base can actually
deliver at the rates implied by the trajectory.

Sources:
- IRENA: Renewable Energy Statistics 2024 (manufacturing capacity)
- IEA: Energy Technology Perspectives 2024 (supply chain analysis)
- France 2030 industrial plan (factory announcements)
- RTE Futurs Energetiques 2050 (workforce estimates)
- ADEME: Employment in energy transition sectors
- CRE / DGEC: French energy industrial policy reports
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import math

from src.trajectory import (
    TrajectoryConfig,
    capacite_solaire_gwc,
    penetration_pac,
    calculer_trajectoire,
)


# ---------------------------------------------------------------------------
# Number of eligible homes for heat pumps
# Source: INSEE -- ~20 million individual houses in mainland France
# Same value used in heating.py
# ---------------------------------------------------------------------------
NOMBRE_MAISONS_ELIGIBLES_PAC: int = 20_000_000


@dataclass
class IndustrialisationConfig:
    """
    Configuration for the industrial capacity model.

    All parameters are documented with units and data sources.
    """

    # --- PV panel manufacturing ---
    # Typical modern PV gigafactory output
    # Source: IRENA 2024 / industry benchmarks (5 GWc/year for a large plant)
    capacite_usine_pv_gwc_an: float = 5.0  # GWc/year per factory

    # Current French PV manufacturing (Carbon, Voltec Solar)
    # Source: France 2030 plan
    nb_usines_pv_actuelles: int = 2

    # Lead time to build a new PV factory
    # Source: IEA Energy Technology Perspectives 2024
    delai_construction_usine_pv_ans: float = 2.0  # Years to build a factory

    # --- Battery manufacturing ---
    # Typical gigafactory output (e.g. ACC Douvrin/Billy-Berclau)
    # Source: ACC, Verkor, AESC press releases / IEA
    capacite_usine_batterie_gwh_an: float = 30.0  # GWh/year per gigafactory

    # Current French battery gigafactories (ACC, Verkor, AESC Douai)
    # Source: France 2030 plan
    nb_usines_batterie_actuelles: int = 3

    # Lead time for a battery gigafactory
    # Source: IEA / industry data
    delai_construction_usine_batterie_ans: float = 3.0

    # Battery deployment assumption: GWh of battery per GWc of solar installed
    # Source: Model assumption -- at 500 GWc solar, ~150 GWh storage needed
    # (from config sensitivity analysis: 122 GWh optimal at 700 GWc)
    batterie_gwh_par_gwc_solaire: float = 0.3

    # --- Heat pump manufacturing ---
    # Large heat pump factory output
    # Source: ADEME / industry data (e.g. Atlantic, Daikin France)
    capacite_usine_pac_unites_an: int = 500_000  # Units/year per factory

    # Current French heat pump factories
    # Source: DGEC / industry census
    nb_usines_pac_actuelles: int = 5

    # Lead time for heat pump factory
    delai_construction_usine_pac_ans: float = 1.5

    # --- Workforce ---
    # Full-time equivalent installers needed per GWc of annual solar installation
    # Source: ADEME / RTE -- includes project managers, electricians, roofers
    installateurs_pv_par_gwc: int = 5_000  # FTE per GWc installed per year

    # Current installer workforce (solar PV)
    # Source: Observatoire des ENR / ADEME 2024
    installateurs_pv_actuels: int = 30_000

    # Training time for a new solar installer
    # Source: ADEME / Qualit'EnR
    formation_installateur_pv_mois: int = 6

    # Heat pump installers per 100,000 units installed per year
    # Source: ADEME / RTE workforce study
    installateurs_pac_par_100k_unites: int = 8_000

    # Current heat pump installer workforce
    installateurs_pac_actuels: int = 25_000

    # Training time for heat pump installer (QualiPAC certification)
    formation_installateur_pac_mois: int = 9

    # Maximum annual training throughput (new workers per year)
    # Source: Model assumption based on training center capacity
    capacite_formation_par_an: int = 20_000

    # --- Raw materials ---
    # Silicon needed per kWc of PV panels
    # Source: IRENA / Fraunhofer ISE -- polysilicon consumption
    silicium_kg_par_kwc: float = 3.0  # kg silicon per kWc

    # Lithium needed per kWh of battery
    # Source: IEA Critical Minerals 2024 -- LFP chemistry
    lithium_kg_par_kwh: float = 0.1  # kg lithium per kWh battery

    # Copper needed per kWc of solar (cabling, inverters, grid connection)
    # Source: IEA / Copper Alliance
    cuivre_kg_par_kwc: float = 4.0  # kg copper per kWc

    # Copper for heat pump (unit basis)
    # Source: IEA / industry data
    cuivre_kg_par_pac: float = 10.0  # kg copper per heat pump unit

    # World production references for supply constraint check (kt/year)
    # Source: USGS Mineral Commodity Summaries 2024
    production_mondiale_silicium_kt: float = 8_500.0  # Solar-grade silicon
    production_mondiale_lithium_kt: float = 180.0
    production_mondiale_cuivre_kt: float = 22_000.0

    # Maximum share of world production France can secure
    # Source: Model assumption (France ~1% of world economy)
    part_max_production_mondiale: float = 0.05  # 5% max

    # --- General ---
    annee_debut: int = 2024
    annee_fin: int = 2050


# ---------------------------------------------------------------------------
# Core analysis functions
# ---------------------------------------------------------------------------


def _ajout_solaire_annuel_gwc(
    year: int,
    traj_config: Optional[TrajectoryConfig] = None,
) -> float:
    """Calculate annual solar PV additions in GWc for a given year."""
    if traj_config is None:
        traj_config = TrajectoryConfig()

    if year <= traj_config.annee_debut:
        return 0.0

    current = capacite_solaire_gwc(year, traj_config)
    previous = capacite_solaire_gwc(year - 1, traj_config)
    return max(0.0, current - previous)


def _ajout_pac_annuel_unites(
    year: int,
    traj_config: Optional[TrajectoryConfig] = None,
    nb_maisons: int = NOMBRE_MAISONS_ELIGIBLES_PAC,
) -> float:
    """Calculate annual heat pump installations (units) for a given year."""
    if traj_config is None:
        traj_config = TrajectoryConfig()

    if year <= traj_config.annee_debut:
        return 0.0

    current_fraction = penetration_pac(year, traj_config)
    previous_fraction = penetration_pac(year - 1, traj_config)
    delta = max(0.0, current_fraction - previous_fraction)
    return delta * nb_maisons


def _besoin_batterie_gwh(ajout_solaire_gwc: float, config: IndustrialisationConfig) -> float:
    """Battery GWh needed for a given annual solar addition."""
    return ajout_solaire_gwc * config.batterie_gwh_par_gwc_solaire


def analyser_besoins_industriels(
    year: int,
    traj_config: Optional[TrajectoryConfig] = None,
    config: Optional[IndustrialisationConfig] = None,
) -> Dict:
    """
    Analyse industrial needs for a single year.

    Returns a dict with manufacturing, workforce, and material needs
    for the given year based on the deployment trajectory.

    Args:
        year: Year to analyse
        traj_config: Trajectory configuration (deployment targets)
        config: Industrialisation configuration (supply-side parameters)

    Returns:
        Dict with keys:
        - annee: year
        - solaire_ajout_gwc: annual solar additions
        - pac_ajout_unites: annual heat pump installations
        - batterie_ajout_gwh: annual battery deployment
        - usines_pv_necessaires: number of PV factories needed
        - usines_batterie_necessaires: number of battery factories needed
        - usines_pac_necessaires: number of heat pump factories needed
        - installateurs_pv_necessaires: PV installer workforce needed
        - installateurs_pac_necessaires: heat pump installer workforce needed
        - silicium_kt: silicon demand in kt
        - lithium_kt: lithium demand in kt
        - cuivre_kt: copper demand in kt
    """
    if traj_config is None:
        traj_config = TrajectoryConfig()
    if config is None:
        config = IndustrialisationConfig()

    ajout_pv = _ajout_solaire_annuel_gwc(year, traj_config)
    ajout_pac = _ajout_pac_annuel_unites(year, traj_config)
    ajout_batterie = _besoin_batterie_gwh(ajout_pv, config)

    # Factory needs (rounded up)
    usines_pv = math.ceil(ajout_pv / config.capacite_usine_pv_gwc_an) if ajout_pv > 0 else 0
    usines_bat = math.ceil(ajout_batterie / config.capacite_usine_batterie_gwh_an) if ajout_batterie > 0 else 0
    usines_pac = math.ceil(ajout_pac / config.capacite_usine_pac_unites_an) if ajout_pac > 0 else 0

    # Workforce needs
    installateurs_pv = int(ajout_pv * config.installateurs_pv_par_gwc)
    installateurs_pac = int(ajout_pac / 100_000 * config.installateurs_pac_par_100k_unites)

    # Raw material needs (convert to kt)
    silicium_kt = ajout_pv * 1e6 * config.silicium_kg_par_kwc / 1e6  # GWc -> kWc -> kg -> kt
    lithium_kt = ajout_batterie * 1e6 * config.lithium_kg_par_kwh / 1e6  # GWh -> kWh -> kg -> kt
    cuivre_pv_kt = ajout_pv * 1e6 * config.cuivre_kg_par_kwc / 1e6
    cuivre_pac_kt = ajout_pac * config.cuivre_kg_par_pac / 1e6
    cuivre_kt = cuivre_pv_kt + cuivre_pac_kt

    return {
        'annee': year,
        'solaire_ajout_gwc': round(ajout_pv, 2),
        'pac_ajout_unites': int(ajout_pac),
        'batterie_ajout_gwh': round(ajout_batterie, 2),
        'usines_pv_necessaires': usines_pv,
        'usines_batterie_necessaires': usines_bat,
        'usines_pac_necessaires': usines_pac,
        'installateurs_pv_necessaires': installateurs_pv,
        'installateurs_pac_necessaires': installateurs_pac,
        'silicium_kt': round(silicium_kt, 1),
        'lithium_kt': round(lithium_kt, 2),
        'cuivre_kt': round(cuivre_kt, 1),
    }


def identifier_goulets(
    traj_config: Optional[TrajectoryConfig] = None,
    config: Optional[IndustrialisationConfig] = None,
) -> List[Dict]:
    """
    Identify bottlenecks that could limit the deployment rate.

    Scans the full trajectory and flags years where industrial needs
    exceed current or projected capacity.

    Args:
        traj_config: Trajectory configuration
        config: Industrialisation configuration

    Returns:
        List of dicts, each describing a bottleneck:
        - annee: year when bottleneck occurs
        - categorie: one of 'usines_pv', 'usines_batterie', 'usines_pac',
                     'main_oeuvre_pv', 'main_oeuvre_pac',
                     'silicium', 'lithium', 'cuivre'
        - description: human-readable description (in French)
        - severite: 'critique' or 'attention'
        - besoin: numeric value of the need
        - capacite: numeric value of current/available capacity
    """
    if traj_config is None:
        traj_config = TrajectoryConfig()
    if config is None:
        config = IndustrialisationConfig()

    goulets: List[Dict] = []

    # Track factory construction (cumulative factories built over time)
    usines_pv_disponibles = config.nb_usines_pv_actuelles
    usines_bat_disponibles = config.nb_usines_batterie_actuelles
    usines_pac_disponibles = config.nb_usines_pac_actuelles

    # Track workforce availability
    main_oeuvre_pv_disponible = config.installateurs_pv_actuels
    main_oeuvre_pac_disponible = config.installateurs_pac_actuels

    for year in range(config.annee_debut, config.annee_fin + 1):
        besoins = analyser_besoins_industriels(year, traj_config, config)

        # -- Manufacturing capacity bottlenecks --

        # PV factories
        capacite_pv_gwc = usines_pv_disponibles * config.capacite_usine_pv_gwc_an
        if besoins['solaire_ajout_gwc'] > capacite_pv_gwc and besoins['solaire_ajout_gwc'] > 0:
            severite = 'critique' if besoins['solaire_ajout_gwc'] > capacite_pv_gwc * 2 else 'attention'
            goulets.append({
                'annee': year,
                'categorie': 'usines_pv',
                'description': (
                    f"Capacite PV insuffisante: besoin {besoins['solaire_ajout_gwc']:.1f} GWc/an "
                    f"vs {capacite_pv_gwc:.1f} GWc/an disponible "
                    f"({usines_pv_disponibles} usines)"
                ),
                'severite': severite,
                'besoin': besoins['solaire_ajout_gwc'],
                'capacite': capacite_pv_gwc,
            })

        # Battery factories
        capacite_bat_gwh = usines_bat_disponibles * config.capacite_usine_batterie_gwh_an
        if besoins['batterie_ajout_gwh'] > capacite_bat_gwh and besoins['batterie_ajout_gwh'] > 0:
            severite = 'critique' if besoins['batterie_ajout_gwh'] > capacite_bat_gwh * 2 else 'attention'
            goulets.append({
                'annee': year,
                'categorie': 'usines_batterie',
                'description': (
                    f"Capacite batterie insuffisante: besoin {besoins['batterie_ajout_gwh']:.1f} GWh/an "
                    f"vs {capacite_bat_gwh:.1f} GWh/an disponible "
                    f"({usines_bat_disponibles} usines)"
                ),
                'severite': severite,
                'besoin': besoins['batterie_ajout_gwh'],
                'capacite': capacite_bat_gwh,
            })

        # Heat pump factories
        capacite_pac = usines_pac_disponibles * config.capacite_usine_pac_unites_an
        if besoins['pac_ajout_unites'] > capacite_pac and besoins['pac_ajout_unites'] > 0:
            severite = 'critique' if besoins['pac_ajout_unites'] > capacite_pac * 2 else 'attention'
            goulets.append({
                'annee': year,
                'categorie': 'usines_pac',
                'description': (
                    f"Capacite PAC insuffisante: besoin {besoins['pac_ajout_unites']:,} unites/an "
                    f"vs {capacite_pac:,} unites/an disponible "
                    f"({usines_pac_disponibles} usines)"
                ),
                'severite': severite,
                'besoin': besoins['pac_ajout_unites'],
                'capacite': capacite_pac,
            })

        # -- Workforce bottlenecks --

        if besoins['installateurs_pv_necessaires'] > main_oeuvre_pv_disponible and besoins['installateurs_pv_necessaires'] > 0:
            severite = 'critique' if besoins['installateurs_pv_necessaires'] > main_oeuvre_pv_disponible * 1.5 else 'attention'
            goulets.append({
                'annee': year,
                'categorie': 'main_oeuvre_pv',
                'description': (
                    f"Main d'oeuvre PV insuffisante: besoin {besoins['installateurs_pv_necessaires']:,} "
                    f"vs {main_oeuvre_pv_disponible:,} disponibles"
                ),
                'severite': severite,
                'besoin': besoins['installateurs_pv_necessaires'],
                'capacite': main_oeuvre_pv_disponible,
            })

        if besoins['installateurs_pac_necessaires'] > main_oeuvre_pac_disponible and besoins['installateurs_pac_necessaires'] > 0:
            severite = 'critique' if besoins['installateurs_pac_necessaires'] > main_oeuvre_pac_disponible * 1.5 else 'attention'
            goulets.append({
                'annee': year,
                'categorie': 'main_oeuvre_pac',
                'description': (
                    f"Main d'oeuvre PAC insuffisante: besoin {besoins['installateurs_pac_necessaires']:,} "
                    f"vs {main_oeuvre_pac_disponible:,} disponibles"
                ),
                'severite': severite,
                'besoin': besoins['installateurs_pac_necessaires'],
                'capacite': main_oeuvre_pac_disponible,
            })

        # -- Raw material bottlenecks --

        seuil_si = config.production_mondiale_silicium_kt * config.part_max_production_mondiale
        if besoins['silicium_kt'] > seuil_si and besoins['silicium_kt'] > 0:
            goulets.append({
                'annee': year,
                'categorie': 'silicium',
                'description': (
                    f"Silicium: besoin {besoins['silicium_kt']:.0f} kt/an "
                    f"depasse {config.part_max_production_mondiale*100:.0f}% de la production "
                    f"mondiale ({seuil_si:.0f} kt)"
                ),
                'severite': 'critique',
                'besoin': besoins['silicium_kt'],
                'capacite': seuil_si,
            })

        seuil_li = config.production_mondiale_lithium_kt * config.part_max_production_mondiale
        if besoins['lithium_kt'] > seuil_li and besoins['lithium_kt'] > 0:
            goulets.append({
                'annee': year,
                'categorie': 'lithium',
                'description': (
                    f"Lithium: besoin {besoins['lithium_kt']:.1f} kt/an "
                    f"depasse {config.part_max_production_mondiale*100:.0f}% de la production "
                    f"mondiale ({seuil_li:.1f} kt)"
                ),
                'severite': 'critique',
                'besoin': besoins['lithium_kt'],
                'capacite': seuil_li,
            })

        seuil_cu = config.production_mondiale_cuivre_kt * config.part_max_production_mondiale
        if besoins['cuivre_kt'] > seuil_cu and besoins['cuivre_kt'] > 0:
            goulets.append({
                'annee': year,
                'categorie': 'cuivre',
                'description': (
                    f"Cuivre: besoin {besoins['cuivre_kt']:.0f} kt/an "
                    f"depasse {config.part_max_production_mondiale*100:.0f}% de la production "
                    f"mondiale ({seuil_cu:.0f} kt)"
                ),
                'severite': 'critique',
                'besoin': besoins['cuivre_kt'],
                'capacite': seuil_cu,
            })

        # -- Update available capacity for next year --

        # Factory ramp-up: add one new factory when the need exceeds current
        # capacity, subject to construction lead time (simplified model:
        # factories ordered when deficit appears, come online after lead time)
        if besoins['usines_pv_necessaires'] > usines_pv_disponibles:
            # Factory will come online after lead time; we model a gradual
            # ramp by adding 1 factory/year when under pressure
            usines_pv_disponibles += 1

        if besoins['usines_batterie_necessaires'] > usines_bat_disponibles:
            usines_bat_disponibles += 1

        if besoins['usines_pac_necessaires'] > usines_pac_disponibles:
            usines_pac_disponibles += 1

        # Workforce ramp-up: train up to capacite_formation_par_an new workers/year
        deficit_pv = max(0, besoins['installateurs_pv_necessaires'] - main_oeuvre_pv_disponible)
        deficit_pac = max(0, besoins['installateurs_pac_necessaires'] - main_oeuvre_pac_disponible)

        # Split training capacity proportionally between PV and PAC
        total_deficit = deficit_pv + deficit_pac
        if total_deficit > 0:
            ratio_pv = deficit_pv / total_deficit
            formation_pv = min(deficit_pv, int(config.capacite_formation_par_an * ratio_pv))
            formation_pac = min(deficit_pac, config.capacite_formation_par_an - formation_pv)
        else:
            formation_pv = 0
            formation_pac = 0

        main_oeuvre_pv_disponible += formation_pv
        main_oeuvre_pac_disponible += formation_pac

    return goulets


def plan_industrialisation(
    traj_config: Optional[TrajectoryConfig] = None,
    config: Optional[IndustrialisationConfig] = None,
) -> List[Dict]:
    """
    Generate a year-by-year industrial plan.

    For each year, shows what needs to be built/trained and what is available.

    Args:
        traj_config: Trajectory configuration
        config: Industrialisation configuration

    Returns:
        List of dicts (one per year) with industrial plan data:
        - annee: year
        - besoins: output of analyser_besoins_industriels
        - usines_pv_disponibles: PV factories available
        - usines_batterie_disponibles: battery factories available
        - usines_pac_disponibles: heat pump factories available
        - capacite_pv_gwc: total PV manufacturing capacity
        - capacite_batterie_gwh: total battery manufacturing capacity
        - capacite_pac_unites: total heat pump manufacturing capacity
        - main_oeuvre_pv: PV workforce available
        - main_oeuvre_pac: heat pump workforce available
        - deficit_pv_gwc: manufacturing gap (negative = surplus)
        - deficit_pac_unites: manufacturing gap
        - deficit_main_oeuvre_pv: workforce gap
        - deficit_main_oeuvre_pac: workforce gap
    """
    if traj_config is None:
        traj_config = TrajectoryConfig()
    if config is None:
        config = IndustrialisationConfig()

    plan: List[Dict] = []

    usines_pv = config.nb_usines_pv_actuelles
    usines_bat = config.nb_usines_batterie_actuelles
    usines_pac = config.nb_usines_pac_actuelles

    main_oeuvre_pv = config.installateurs_pv_actuels
    main_oeuvre_pac = config.installateurs_pac_actuels

    for year in range(config.annee_debut, config.annee_fin + 1):
        besoins = analyser_besoins_industriels(year, traj_config, config)

        capacite_pv = usines_pv * config.capacite_usine_pv_gwc_an
        capacite_bat = usines_bat * config.capacite_usine_batterie_gwh_an
        capacite_pac = usines_pac * config.capacite_usine_pac_unites_an

        deficit_pv_gwc = besoins['solaire_ajout_gwc'] - capacite_pv
        deficit_bat_gwh = besoins['batterie_ajout_gwh'] - capacite_bat
        deficit_pac_unites = besoins['pac_ajout_unites'] - capacite_pac
        deficit_mo_pv = besoins['installateurs_pv_necessaires'] - main_oeuvre_pv
        deficit_mo_pac = besoins['installateurs_pac_necessaires'] - main_oeuvre_pac

        plan.append({
            'annee': year,
            'besoins': besoins,
            'usines_pv_disponibles': usines_pv,
            'usines_batterie_disponibles': usines_bat,
            'usines_pac_disponibles': usines_pac,
            'capacite_pv_gwc': round(capacite_pv, 1),
            'capacite_batterie_gwh': round(capacite_bat, 1),
            'capacite_pac_unites': capacite_pac,
            'main_oeuvre_pv': main_oeuvre_pv,
            'main_oeuvre_pac': main_oeuvre_pac,
            'deficit_pv_gwc': round(deficit_pv_gwc, 2),
            'deficit_batterie_gwh': round(deficit_bat_gwh, 2),
            'deficit_pac_unites': int(deficit_pac_unites),
            'deficit_main_oeuvre_pv': deficit_mo_pv,
            'deficit_main_oeuvre_pac': deficit_mo_pac,
        })

        # Ramp up supply for next year
        if besoins['usines_pv_necessaires'] > usines_pv:
            usines_pv += 1
        if besoins['usines_batterie_necessaires'] > usines_bat:
            usines_bat += 1
        if besoins['usines_pac_necessaires'] > usines_pac:
            usines_pac += 1

        # Workforce training
        deficit_pv_workers = max(0, besoins['installateurs_pv_necessaires'] - main_oeuvre_pv)
        deficit_pac_workers = max(0, besoins['installateurs_pac_necessaires'] - main_oeuvre_pac)
        total_deficit = deficit_pv_workers + deficit_pac_workers
        if total_deficit > 0:
            ratio_pv = deficit_pv_workers / total_deficit
            formation_pv = min(deficit_pv_workers, int(config.capacite_formation_par_an * ratio_pv))
            formation_pac = min(deficit_pac_workers, config.capacite_formation_par_an - formation_pv)
        else:
            formation_pv = 0
            formation_pac = 0
        main_oeuvre_pv += formation_pv
        main_oeuvre_pac += formation_pac

    return plan


def resume_industrialisation(
    traj_config: Optional[TrajectoryConfig] = None,
    config: Optional[IndustrialisationConfig] = None,
) -> str:
    """
    Generate a human-readable summary of the industrialisation analysis.

    Shows key milestones, peak needs, and bottleneck warnings.

    Args:
        traj_config: Trajectory configuration
        config: Industrialisation configuration

    Returns:
        Formatted summary string (in French)
    """
    if traj_config is None:
        traj_config = TrajectoryConfig()
    if config is None:
        config = IndustrialisationConfig()

    plan = plan_industrialisation(traj_config, config)
    goulets = identifier_goulets(traj_config, config)

    # Find peak year for solar additions
    peak_pv = max(plan, key=lambda p: p['besoins']['solaire_ajout_gwc'])
    peak_pac = max(plan, key=lambda p: p['besoins']['pac_ajout_unites'])

    # Count bottlenecks by category
    goulets_par_categorie: Dict[str, int] = {}
    goulets_critiques = 0
    for g in goulets:
        cat = g['categorie']
        goulets_par_categorie[cat] = goulets_par_categorie.get(cat, 0) + 1
        if g['severite'] == 'critique':
            goulets_critiques += 1

    # Milestone years
    milestones = [2024, 2030, 2035, 2040, 2045, 2050]
    by_year = {p['annee']: p for p in plan}

    lines = [
        "Plan d'Industrialisation - Transition Energetique France",
        "=" * 60,
        "",
        "Capacites actuelles:",
        f"  Usines PV:        {config.nb_usines_pv_actuelles} "
        f"({config.nb_usines_pv_actuelles * config.capacite_usine_pv_gwc_an:.0f} GWc/an)",
        f"  Gigafactories:    {config.nb_usines_batterie_actuelles} "
        f"({config.nb_usines_batterie_actuelles * config.capacite_usine_batterie_gwh_an:.0f} GWh/an)",
        f"  Usines PAC:       {config.nb_usines_pac_actuelles} "
        f"({config.nb_usines_pac_actuelles * config.capacite_usine_pac_unites_an:,} unites/an)",
        f"  Installateurs PV: {config.installateurs_pv_actuels:,}",
        f"  Installateurs PAC:{config.installateurs_pac_actuels:,}",
        "",
        "Pic de deploiement:",
        f"  Solaire: {peak_pv['besoins']['solaire_ajout_gwc']:.1f} GWc/an "
        f"en {peak_pv['annee']} "
        f"({peak_pv['besoins']['usines_pv_necessaires']} usines necessaires)",
        f"  PAC:     {peak_pac['besoins']['pac_ajout_unites']:,} unites/an "
        f"en {peak_pac['annee']} "
        f"({peak_pac['besoins']['usines_pac_necessaires']} usines necessaires)",
        "",
        "Trajectoire industrielle:",
        f"  {'Annee':>5} {'PV GWc/an':>10} {'Usines PV':>10} {'PAC k/an':>10} "
        f"{'Usines PAC':>10} {'MO PV':>8} {'MO PAC':>8}",
    ]

    for year in milestones:
        if year in by_year:
            p = by_year[year]
            b = p['besoins']
            lines.append(
                f"  {year:>5} {b['solaire_ajout_gwc']:>10.1f} "
                f"{p['usines_pv_disponibles']:>10} "
                f"{b['pac_ajout_unites']/1000:>10.0f} "
                f"{p['usines_pac_disponibles']:>10} "
                f"{p['main_oeuvre_pv']:>8,} "
                f"{p['main_oeuvre_pac']:>8,}"
            )

    lines.extend([
        "",
        f"Goulets d'etranglement identifies: {len(goulets)} "
        f"(dont {goulets_critiques} critiques)",
    ])

    if goulets_par_categorie:
        lines.append("  Par categorie:")
        category_labels = {
            'usines_pv': 'Usines PV',
            'usines_batterie': 'Gigafactories batteries',
            'usines_pac': 'Usines PAC',
            'main_oeuvre_pv': "Main d'oeuvre PV",
            'main_oeuvre_pac': "Main d'oeuvre PAC",
            'silicium': 'Silicium',
            'lithium': 'Lithium',
            'cuivre': 'Cuivre',
        }
        for cat, count in sorted(goulets_par_categorie.items()):
            label = category_labels.get(cat, cat)
            lines.append(f"    {label}: {count} annees")

    # Materials summary at peak
    peak_materials = max(plan, key=lambda p: p['besoins']['silicium_kt'])
    pm = peak_materials['besoins']
    lines.extend([
        "",
        f"Besoins materiaux au pic ({peak_materials['annee']}):",
        f"  Silicium: {pm['silicium_kt']:.0f} kt "
        f"({pm['silicium_kt']/config.production_mondiale_silicium_kt*100:.1f}% prod. mondiale)",
        f"  Lithium:  {pm['lithium_kt']:.1f} kt "
        f"({pm['lithium_kt']/config.production_mondiale_lithium_kt*100:.1f}% prod. mondiale)",
        f"  Cuivre:   {pm['cuivre_kt']:.0f} kt "
        f"({pm['cuivre_kt']/config.production_mondiale_cuivre_kt*100:.1f}% prod. mondiale)",
    ])

    return '\n'.join(lines)
