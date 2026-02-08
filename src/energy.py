"""
Core energy calculation module for the Energy Transition Model.

Contains the fundamental energy formula and related utilities.
"""

from typing import Optional
from .config import EnergyModelConfig, DEFAULT_CONFIG


def calculer_energie_twh(
    deficit_kw: float,
    duree_h: float,
    config: Optional[EnergyModelConfig] = None
) -> float:
    """
    Calculate energy in TWh from power deficit and duration.

    This implements the core formula from the spreadsheet model:
        S (TWh) = Q (kW) × R (hours/day) × days_per_month / 1e9

    Args:
        deficit_kw: Power deficit in kW (consumption - production)
        duree_h: Duration of the time slot in hours per day
        config: Model configuration (uses DEFAULT_CONFIG if None)

    Returns:
        Energy in TWh. Returns 0 if deficit is <= 0.

    Examples:
        >>> calculer_energie_twh(85_300_000, 5)  # 85.3 GW deficit, 5h slot
        12.795  # ~12.8 TWh

    Formula derivation:
        - deficit_kw: Power deficit during the time slot (kW)
        - duree_h: Hours per day this slot lasts
        - 30: Days per month (approximation)
        - 1e9: Conversion from kWh to TWh

        Energy (kWh/month) = deficit (kW) × duration (h/day) × 30 (days/month)
        Energy (TWh/month) = Energy (kWh/month) / 1e9
    """
    if deficit_kw <= 0:
        return 0.0

    if config is None:
        config = DEFAULT_CONFIG

    jours = config.temporal.jours_par_mois
    return deficit_kw * duree_h * jours / 1e9


def calculer_deficit_kw(production_kw: float, consommation_kw: float) -> float:
    """
    Calculate power deficit (gas backup need).

    Args:
        production_kw: Total power production in kW
        consommation_kw: Total power consumption in kW

    Returns:
        Deficit in kW (positive if consumption > production, else 0)
    """
    return max(0, consommation_kw - production_kw)


def calculer_surplus_kw(production_kw: float, consommation_kw: float) -> float:
    """
    Calculate power surplus (available for storage or export).

    Args:
        production_kw: Total power production in kW
        consommation_kw: Total power consumption in kW

    Returns:
        Surplus in kW (positive if production > consumption, else 0)
    """
    return max(0, production_kw - consommation_kw)


def kw_to_gw(kw: float) -> float:
    """Convert kilowatts to gigawatts."""
    return kw / 1e6


def gw_to_kw(gw: float) -> float:
    """Convert gigawatts to kilowatts."""
    return gw * 1e6


def twh_to_gwh(twh: float) -> float:
    """Convert terawatt-hours to gigawatt-hours."""
    return twh * 1000


def gwh_to_twh(gwh: float) -> float:
    """Convert gigawatt-hours to terawatt-hours."""
    return gwh / 1000
