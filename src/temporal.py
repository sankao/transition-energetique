"""
Temporal utilities for the Energy Transition Model.

Functions for parsing time periods and calculating solar availability.
"""

from typing import Optional
from .config import EnergyModelConfig, DEFAULT_CONFIG


# Month name mappings (French with accents)
MOIS_MAP = {
    'janvier': 'Janvier',
    'fevrier': 'Février',
    'février': 'Février',
    'mars': 'Mars',
    'avril': 'Avril',
    'mai': 'Mai',
    'juin': 'Juin',
    'juillet': 'Juillet',
    'aout': 'Août',
    'août': 'Août',
    'septembre': 'Septembre',
    'octobre': 'Octobre',
    'novembre': 'Novembre',
    'decembre': 'Décembre',
    'décembre': 'Décembre',
}


def extraire_mois(periode: str) -> str:
    """
    Extract the month name from a period string.

    Args:
        periode: Period string like "Janvier 8 heures - 13 heures"

    Returns:
        Normalized month name (e.g., "Janvier") or "Inconnu"
    """
    periode_lower = periode.lower()
    for key, val in MOIS_MAP.items():
        if key in periode_lower:
            return val
    return 'Inconnu'


def extraire_plage(periode: str) -> str:
    """
    Extract the time slot from a period string.

    Args:
        periode: Period string like "Janvier 8 heures - 13 heures"

    Returns:
        Time slot identifier (e.g., "8h-13h") or "Autre"
    """
    periode_lower = periode.lower()

    # Note: '18 heures' contains '8 heure', so check for absence of '18'
    if '8 heure' in periode_lower and '13' in periode_lower and '18' not in periode_lower:
        return '8h-13h'
    elif '13 heure' in periode_lower and '18' in periode_lower:
        return '13h-18h'
    elif '18 heure' in periode_lower and '20' in periode_lower:
        return '18h-20h'
    elif '20 heure' in periode_lower and '23' in periode_lower:
        return '20h-23h'
    elif '23 heure' in periode_lower:
        return '23h-8h'
    return 'Autre'


def est_plage_nocturne(
    mois: str,
    plage: str,
    config: Optional[EnergyModelConfig] = None
) -> bool:
    """
    Determine if a time slot is nocturnal (no sun) for a given month.

    Args:
        mois: Month name (e.g., "Janvier")
        plage: Time slot (e.g., "18h-20h")
        config: Model configuration (uses DEFAULT_CONFIG if None)

    Returns:
        True if the time slot has no sunlight
    """
    if config is None:
        config = DEFAULT_CONFIG

    sunset = config.temporal.sunset_times.get(mois, 18.0)

    if plage == '23h-8h':
        return True  # Always nocturnal
    elif plage == '20h-23h':
        return sunset < 20
    elif plage == '18h-20h':
        return sunset < 18
    return False


def fraction_solaire_attendue(
    mois: str,
    plage: str,
    config: Optional[EnergyModelConfig] = None
) -> float:
    """
    Estimate the fraction of a time slot with sunlight (0 to 1).

    This is used to detect anomalies and calculate expected solar production.

    Args:
        mois: Month name (e.g., "Janvier")
        plage: Time slot (e.g., "18h-20h")
        config: Model configuration (uses DEFAULT_CONFIG if None)

    Returns:
        Fraction between 0.0 (full night) and 1.0 (full sun)

    Examples:
        >>> fraction_solaire_attendue("Juin", "8h-13h")
        1.0
        >>> fraction_solaire_attendue("Janvier", "18h-20h")
        0.0
        >>> fraction_solaire_attendue("Avril", "18h-20h")  # Sunset at 20:43
        1.0
    """
    if config is None:
        config = DEFAULT_CONFIG

    sunset = config.temporal.sunset_times.get(mois, 18.0)

    if plage == '8h-13h' or plage == '13h-18h':
        return 1.0  # Full daylight
    elif plage == '18h-20h':
        if sunset >= 20:
            return 1.0
        elif sunset <= 18:
            return 0.0
        else:
            return (sunset - 18) / 2
    elif plage == '20h-23h':
        if sunset >= 23:
            return 1.0
        elif sunset <= 20:
            return 0.0
        else:
            return (sunset - 20) / 3
    elif plage == '23h-8h':
        return 0.0  # Always night
    return 0.5  # Unknown - assume partial


def get_plage_duration(plage: str, config: Optional[EnergyModelConfig] = None) -> float:
    """
    Get the duration of a time slot in hours.

    Args:
        plage: Time slot identifier
        config: Model configuration

    Returns:
        Duration in hours
    """
    if config is None:
        config = DEFAULT_CONFIG

    return config.temporal.time_slots.get(plage, 0.0)
