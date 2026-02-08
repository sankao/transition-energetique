"""
Storage module for the Energy Transition Model.

Calculates battery/STEP storage requirements.
"""

from typing import Dict, Optional, Tuple
import pandas as pd

from .config import EnergyModelConfig, DEFAULT_CONFIG


def calculate_storage_need(
    extra_solar_gwc: float,
    solar_cf: Dict[Tuple[str, str], Dict],
    df: pd.DataFrame,
    config: Optional[EnergyModelConfig] = None
) -> float:
    """
    Calculate the daily storage capacity needed for a given solar level.

    Storage requirement is the minimum of daily surplus and deficit,
    representing how much energy needs to be shifted within each day.

    Args:
        extra_solar_gwc: Additional solar capacity beyond baseline
        solar_cf: Capacity factor data
        df: Original DataFrame
        config: Model configuration

    Returns:
        Maximum required storage capacity in GWh (across all months)
    """
    if config is None:
        config = DEFAULT_CONFIG

    baseline = config.production.solar_capacity_gwc
    new_capacity = max(0, baseline + extra_solar_gwc)
    new_capacity_kw = new_capacity * 1e6

    max_storage_needed = 0.0

    for mois in config.temporal.mois_ordre_hiver:
        daily_surplus_gwh = 0.0
        daily_deficit_gwh = 0.0

        plages = ['8h-13h', '13h-18h', '18h-20h', '20h-23h', '23h-8h']

        for plage in plages:
            key = (mois, plage)

            if plage == '23h-8h':
                night_data = df[(df['Mois'] == mois) & (df['Plage'] == plage)]
                if len(night_data) > 0:
                    row = night_data.iloc[0]
                    balance_gw = (row['Production_kW'] - row['Consommation_kW']) / 1e6
                    duration = row['Duree_h']
                else:
                    continue
            elif key in solar_cf:
                data = solar_cf[key]
                new_solar = data['cf'] * new_capacity_kw
                new_prod = data['base_prod'] + new_solar
                balance_gw = (new_prod - data['conso']) / 1e6
                duration = data['duree']
            else:
                continue

            if balance_gw > 0:
                daily_surplus_gwh += balance_gw * duration
            else:
                daily_deficit_gwh += abs(balance_gw) * duration

        # Storage needed is min(surplus, deficit) for each day
        storage_needed = min(daily_surplus_gwh, daily_deficit_gwh)
        max_storage_needed = max(max_storage_needed, storage_needed)

    return max_storage_needed


def calculate_storage_by_month(
    extra_solar_gwc: float,
    solar_cf: Dict[Tuple[str, str], Dict],
    df: pd.DataFrame,
    config: Optional[EnergyModelConfig] = None
) -> Dict[str, float]:
    """
    Calculate storage needs for each month.

    Args:
        extra_solar_gwc: Additional solar capacity
        solar_cf: Capacity factor data
        df: Original DataFrame
        config: Model configuration

    Returns:
        Dict mapping month names to storage requirement in GWh
    """
    if config is None:
        config = DEFAULT_CONFIG

    baseline = config.production.solar_capacity_gwc
    new_capacity = max(0, baseline + extra_solar_gwc)
    new_capacity_kw = new_capacity * 1e6

    storage_by_month = {}

    for mois in config.temporal.mois_ordre:
        daily_surplus_gwh = 0.0
        daily_deficit_gwh = 0.0

        plages = ['8h-13h', '13h-18h', '18h-20h', '20h-23h', '23h-8h']

        for plage in plages:
            key = (mois, plage)

            if plage == '23h-8h':
                night_data = df[(df['Mois'] == mois) & (df['Plage'] == plage)]
                if len(night_data) > 0:
                    row = night_data.iloc[0]
                    balance_gw = (row['Production_kW'] - row['Consommation_kW']) / 1e6
                    duration = row['Duree_h']
                else:
                    continue
            elif key in solar_cf:
                data = solar_cf[key]
                new_solar = data['cf'] * new_capacity_kw
                new_prod = data['base_prod'] + new_solar
                balance_gw = (new_prod - data['conso']) / 1e6
                duration = data['duree']
            else:
                continue

            if balance_gw > 0:
                daily_surplus_gwh += balance_gw * duration
            else:
                daily_deficit_gwh += abs(balance_gw) * duration

        storage_by_month[mois] = min(daily_surplus_gwh, daily_deficit_gwh)

    return storage_by_month


def storage_equivalents(storage_gwh: float) -> Dict[str, float]:
    """
    Convert storage capacity to real-world equivalents.

    Args:
        storage_gwh: Storage capacity in GWh

    Returns:
        Dict with equivalent counts for various storage types
    """
    storage_kwh = storage_gwh * 1e6

    return {
        'tesla_powerwalls_millions': storage_kwh / 13.5 / 1e6,
        'ev_batteries_millions': storage_kwh / 60 / 1e6,  # 60 kWh average EV
        'moss_landing_equivalents': storage_gwh / 3.0,
        'grandmaison_step_equivalents': storage_gwh / 5.0,
        'france_step_fraction': storage_gwh / 100.0,
    }
