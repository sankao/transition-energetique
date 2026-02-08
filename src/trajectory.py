"""
Deployment trajectory module for the Energy Transition Model.

Models the year-by-year deployment path from 2024 to 2050:
- Solar PV capacity ramp-up (S-curve deployment)
- Heat pump adoption rate
- Cost learning curves (Swanson's law for solar, Wright's law for batteries)
- Annual investment requirements
- Cumulative emissions avoided

Sources:
- IRENA: Solar cost learning rate (~20% per doubling)
- BNEF: Battery cost learning rate (~18% per doubling)
- RTE Futurs Énergétiques 2050: deployment trajectory references
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import math


@dataclass
class TrajectoryConfig:
    """Configuration for the deployment trajectory."""

    # --- Timeline ---
    annee_debut: int = 2024
    annee_fin: int = 2050

    # --- Solar PV deployment ---
    # Current installed capacity (GWc)
    # Source: RTE Panorama ENR 2024
    solaire_actuel_gwc: float = 20.0

    # Target capacity (GWc)
    solaire_cible_gwc: float = 500.0

    # S-curve midpoint year (year when deployment rate is fastest)
    solaire_midpoint: int = 2035

    # S-curve steepness (higher = sharper transition)
    solaire_steepness: float = 0.35

    # --- Heat pump deployment ---
    # Current heat pump penetration (fraction of eligible homes)
    # Source: ADEME / Observatoire des ENR
    pac_actuel_fraction: float = 0.15

    # Target penetration
    pac_cible_fraction: float = 1.0

    # S-curve midpoint
    pac_midpoint: int = 2037

    pac_steepness: float = 0.30

    # --- Cost learning curves ---
    # Solar PV learning rate: cost reduction per doubling of cumulative capacity
    # Source: IRENA, Swanson's law (~20% historical)
    solaire_learning_rate: float = 0.20

    # Current solar cost (€/kW installed)
    # Source: IRENA 2024
    solaire_cout_actuel_eur_kw: float = 600.0

    # Battery learning rate
    # Source: BNEF (~18% historical)
    batterie_learning_rate: float = 0.18

    # Current battery cost (€/kWh)
    # Source: BNEF 2024
    batterie_cout_actuel_eur_kwh: float = 200.0

    # Global cumulative solar capacity reference for learning curve (GWc)
    # Source: IRENA 2024
    solaire_cumul_mondial_gwc: float = 1500.0

    # Global cumulative battery capacity reference (GWh)
    # Source: BNEF 2024
    batterie_cumul_mondial_gwh: float = 2000.0

    # --- Gas cost ---
    # Source: Market assumption, constant in real terms
    gaz_cout_eur_mwh: float = 90.0

    # --- Gas backup relationship ---
    # Gas backup as function of solar capacity (linear approximation)
    # From sensitivity analysis: ~114 TWh at 500 GWc, ~0 TWh at 950 GWc
    # gas_twh ≈ max(0, gaz_a * solar_gwc + gaz_b)
    gaz_a: float = -0.253  # TWh per GWc
    gaz_b: float = 240.5   # TWh intercept


def logistic(year: int, midpoint: int, steepness: float) -> float:
    """
    Logistic (S-curve) function for deployment modeling.

    Returns a value between 0 and 1.

    Args:
        year: Current year
        midpoint: Year of maximum deployment rate (inflection point)
        steepness: Rate of transition (higher = sharper)

    Returns:
        Fraction of deployment completed (0 to 1)
    """
    return 1.0 / (1.0 + math.exp(-steepness * (year - midpoint)))


def capacite_solaire_gwc(year: int, config: Optional[TrajectoryConfig] = None) -> float:
    """
    Calculate installed solar capacity for a given year.

    Uses logistic S-curve between current and target capacity.

    Args:
        year: Year
        config: Trajectory configuration

    Returns:
        Installed solar capacity in GWc
    """
    if config is None:
        config = TrajectoryConfig()

    if year <= config.annee_debut:
        return config.solaire_actuel_gwc
    if year >= config.annee_fin:
        return config.solaire_cible_gwc

    # Normalize logistic to map from actual to target
    s_start = logistic(config.annee_debut, config.solaire_midpoint, config.solaire_steepness)
    s_end = logistic(config.annee_fin, config.solaire_midpoint, config.solaire_steepness)
    s_now = logistic(year, config.solaire_midpoint, config.solaire_steepness)

    fraction = (s_now - s_start) / (s_end - s_start)
    return config.solaire_actuel_gwc + fraction * (config.solaire_cible_gwc - config.solaire_actuel_gwc)


def penetration_pac(year: int, config: Optional[TrajectoryConfig] = None) -> float:
    """
    Calculate heat pump penetration fraction for a given year.

    Args:
        year: Year
        config: Trajectory configuration

    Returns:
        Fraction of eligible homes with heat pumps (0 to 1)
    """
    if config is None:
        config = TrajectoryConfig()

    if year <= config.annee_debut:
        return config.pac_actuel_fraction
    if year >= config.annee_fin:
        return config.pac_cible_fraction

    s_start = logistic(config.annee_debut, config.pac_midpoint, config.pac_steepness)
    s_end = logistic(config.annee_fin, config.pac_midpoint, config.pac_steepness)
    s_now = logistic(year, config.pac_midpoint, config.pac_steepness)

    fraction = (s_now - s_start) / (s_end - s_start)
    return config.pac_actuel_fraction + fraction * (config.pac_cible_fraction - config.pac_actuel_fraction)


def cout_solaire_eur_kw(year: int, config: Optional[TrajectoryConfig] = None) -> float:
    """
    Calculate solar PV cost for a given year using learning curve.

    Wright's law: cost reduces by learning_rate for each doubling of
    cumulative production.

    Args:
        year: Year
        config: Trajectory configuration

    Returns:
        Solar cost in €/kW
    """
    if config is None:
        config = TrajectoryConfig()

    # Cumulative French additions (rough proxy: half deployed by midpoint)
    additions_gwc = capacite_solaire_gwc(year, config) - config.solaire_actuel_gwc

    # Global cumulative grows proportionally (France is ~5% of world market)
    global_cumul = config.solaire_cumul_mondial_gwc + additions_gwc / 0.05

    # Learning curve: cost = initial × (cumul/initial_cumul)^log2(1-learning_rate)
    exponent = math.log2(1 - config.solaire_learning_rate)
    ratio = global_cumul / config.solaire_cumul_mondial_gwc
    return config.solaire_cout_actuel_eur_kw * (ratio ** exponent)


def cout_batterie_eur_kwh(year: int, config: Optional[TrajectoryConfig] = None) -> float:
    """
    Calculate battery storage cost for a given year using learning curve.

    Args:
        year: Year
        config: Trajectory configuration

    Returns:
        Battery cost in €/kWh
    """
    if config is None:
        config = TrajectoryConfig()

    # Global battery deployment grows ~25% per year
    years_elapsed = max(0, year - config.annee_debut)
    global_cumul = config.batterie_cumul_mondial_gwh * (1.25 ** years_elapsed)

    exponent = math.log2(1 - config.batterie_learning_rate)
    ratio = global_cumul / config.batterie_cumul_mondial_gwh
    return config.batterie_cout_actuel_eur_kwh * (ratio ** exponent)


def gaz_backup_twh(solar_gwc: float, config: Optional[TrajectoryConfig] = None) -> float:
    """
    Estimate gas backup need from installed solar capacity.

    Linear approximation from sensitivity analysis.

    Args:
        solar_gwc: Installed solar capacity in GWc
        config: Trajectory configuration

    Returns:
        Annual gas backup in TWh
    """
    if config is None:
        config = TrajectoryConfig()

    return max(0.0, config.gaz_a * solar_gwc + config.gaz_b)


def calculer_trajectoire(
    config: Optional[TrajectoryConfig] = None,
) -> List[Dict]:
    """
    Calculate the full deployment trajectory year by year.

    Args:
        config: Trajectory configuration

    Returns:
        List of dicts, one per year, with all trajectory metrics
    """
    if config is None:
        config = TrajectoryConfig()

    trajectory = []
    cumul_invest_eur_b = 0.0
    cumul_emissions_evitees_mt = 0.0
    prev_solar = config.solaire_actuel_gwc

    # Reference: current gas use for sectors being electrified
    # Transport: ~50 Mtep fossil → ~580 TWh; Buildings: ~40 Mtep → ~465 TWh
    facteur_gaz_tco2_mwh = 0.227  # tCO2/MWh from emissions module

    for year in range(config.annee_debut, config.annee_fin + 1):
        solar = capacite_solaire_gwc(year, config)
        pac = penetration_pac(year, config)
        cout_sol = cout_solaire_eur_kw(year, config)
        cout_bat = cout_batterie_eur_kwh(year, config)
        gaz = gaz_backup_twh(solar, config)

        # Annual solar additions
        solar_ajout = solar - prev_solar
        prev_solar = solar

        # Annual investment: solar additions × cost
        invest_solaire = solar_ajout * cout_sol / 1000  # €B (GWc × €/kW = €M, /1000 = €B)
        cumul_invest_eur_b += invest_solaire

        # Annual gas cost
        cout_gaz_annuel = gaz * config.gaz_cout_eur_mwh / 1000  # €B

        # Emissions from gas backup
        emissions_gaz = gaz * facteur_gaz_tco2_mwh

        # Emissions avoided vs "do nothing" (current ~175 MtCO2 from transport+buildings)
        reference_emissions = 175.0  # MtCO2 from transport + buildings fossil
        # Proportional to electrification progress (solar deployment as proxy)
        progress = (solar - config.solaire_actuel_gwc) / (config.solaire_cible_gwc - config.solaire_actuel_gwc)
        evitees_annuelles = reference_emissions * progress - emissions_gaz
        cumul_emissions_evitees_mt += max(0, evitees_annuelles)

        trajectory.append({
            'annee': year,
            'solaire_gwc': round(solar, 1),
            'solaire_ajout_gwc': round(solar_ajout, 1),
            'pac_fraction': round(pac, 3),
            'cout_solaire_eur_kw': round(cout_sol, 0),
            'cout_batterie_eur_kwh': round(cout_bat, 0),
            'gaz_backup_twh': round(gaz, 1),
            'invest_solaire_eur_b': round(invest_solaire, 1),
            'cout_gaz_annuel_eur_b': round(cout_gaz_annuel, 1),
            'cumul_invest_eur_b': round(cumul_invest_eur_b, 1),
            'emissions_gaz_mt': round(emissions_gaz, 1),
            'emissions_evitees_mt': round(max(0, evitees_annuelles), 1),
            'cumul_emissions_evitees_mt': round(cumul_emissions_evitees_mt, 0),
        })

    return trajectory


def resume_trajectoire(config: Optional[TrajectoryConfig] = None) -> str:
    """
    Generate a human-readable trajectory summary.

    Shows key milestones and metrics.

    Args:
        config: Trajectory configuration

    Returns:
        Formatted summary string
    """
    if config is None:
        config = TrajectoryConfig()

    traj = calculer_trajectoire(config)

    # Key milestones
    milestones = [2024, 2030, 2035, 2040, 2045, 2050]
    by_year = {t['annee']: t for t in traj}

    lines = [
        "Trajectoire de Déploiement 2024-2050",
        "=" * 50,
        "",
        f"  {'Année':>5} {'Solaire':>8} {'Ajout':>7} {'PAC':>5} {'€/kW':>6} {'Gaz TWh':>8} {'Invest':>8} {'CO2 évité':>10}",
        f"  {'':─>5} {'GWc':─>8} {'GWc/an':─>7} {'':─>5} {'':─>6} {'':─>8} {'€B/an':─>8} {'Mt cum.':─>10}",
    ]

    for year in milestones:
        if year in by_year:
            t = by_year[year]
            lines.append(
                f"  {t['annee']:>5} {t['solaire_gwc']:>7.0f} {t['solaire_ajout_gwc']:>7.1f}"
                f" {t['pac_fraction']:>5.0%} {t['cout_solaire_eur_kw']:>5.0f}"
                f" {t['gaz_backup_twh']:>8.0f} {t['invest_solaire_eur_b']:>8.1f}"
                f" {t['cumul_emissions_evitees_mt']:>10.0f}"
            )

    # Summary
    final = traj[-1]
    total_invest = final['cumul_invest_eur_b']
    total_co2 = final['cumul_emissions_evitees_mt']

    lines.extend([
        "",
        f"  Investissement cumulé: {total_invest:.0f} €B",
        f"  Émissions évitées cumulées: {total_co2:.0f} MtCO2",
        "",
        "  Courbes d'apprentissage:",
        f"    Solaire: {config.solaire_cout_actuel_eur_kw:.0f} → {final['cout_solaire_eur_kw']:.0f} €/kW"
        f" (-{(1 - final['cout_solaire_eur_kw']/config.solaire_cout_actuel_eur_kw)*100:.0f}%)",
        f"    Batterie: {config.batterie_cout_actuel_eur_kwh:.0f} → {final['cout_batterie_eur_kwh']:.0f} €/kWh"
        f" (-{(1 - final['cout_batterie_eur_kwh']/config.batterie_cout_actuel_eur_kwh)*100:.0f}%)",
    ])

    return '\n'.join(lines)
