"""
Sensitivity analysis module for the Energy Transition Model.

Functions to analyze how gas backup needs vary with solar capacity.
Demand figures come from the DataFrame (time-slot level consumption)
which should be calibrated against consumption.py system balance (~729 TWh).
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

from .config import EnergyModelConfig, DEFAULT_CONFIG
from .energy import calculer_energie_twh


def calculate_gas_need_no_storage(
    extra_solar_gwc: float,
    solar_cf: Dict[Tuple[str, str], Dict],
    df: pd.DataFrame,
    config: Optional[EnergyModelConfig] = None
) -> float:
    """
    Calculate gas backup need with additional solar capacity, WITHOUT storage.

    Args:
        extra_solar_gwc: Additional solar capacity beyond baseline (can be negative)
        solar_cf: Capacity factor data from production.calculate_solar_capacity_factors
        df: Original DataFrame with nighttime data
        config: Model configuration

    Returns:
        Total annual gas need in TWh
    """
    if config is None:
        config = DEFAULT_CONFIG

    baseline = config.production.solar_capacity_gwc
    new_capacity = max(0, baseline + extra_solar_gwc)
    new_capacity_kw = new_capacity * 1e6

    total_gas_twh = 0.0

    # Daytime slots: scale solar production
    for (mois, plage), data in solar_cf.items():
        new_solar = data['cf'] * new_capacity_kw
        new_total_prod = data['base_prod'] + new_solar
        deficit = max(0, data['conso'] - new_total_prod)
        gas_twh = calculer_energie_twh(deficit, data['duree'], config)
        total_gas_twh += gas_twh

    # Nighttime slots: unchanged (no solar)
    for mois in df['Mois'].unique():
        night_data = df[(df['Mois'] == mois) & (df['Plage'] == '23h-8h')]
        if len(night_data) > 0:
            row = night_data.iloc[0]
            deficit = max(0, row['Deficit_kW'])
            gas_twh = calculer_energie_twh(deficit, row['Duree_h'], config)
            total_gas_twh += gas_twh

    return total_gas_twh


def calculate_gas_need_with_storage(
    extra_solar_gwc: float,
    solar_cf: Dict[Tuple[str, str], Dict],
    df: pd.DataFrame,
    config: Optional[EnergyModelConfig] = None
) -> float:
    """
    Calculate gas backup need with additional solar AND daily storage.

    Storage allows surplus energy from daytime to offset nighttime deficit.
    Uses configurable round-trip efficiency.

    Args:
        extra_solar_gwc: Additional solar capacity beyond baseline
        solar_cf: Capacity factor data
        df: Original DataFrame
        config: Model configuration

    Returns:
        Total annual gas need in TWh (reduced by storage)
    """
    if config is None:
        config = DEFAULT_CONFIG

    baseline = config.production.solar_capacity_gwc
    new_capacity = max(0, baseline + extra_solar_gwc)
    new_capacity_kw = new_capacity * 1e6
    efficiency = config.storage.battery_efficiency

    total_gas_twh = 0.0

    for mois in df['Mois'].unique():
        # Calculate daily surplus and deficit for this month
        daily_surplus_kwh = 0.0
        daily_deficit_kwh = 0.0

        plages = ['8h-13h', '13h-18h', '18h-20h', '20h-23h', '23h-8h']

        for plage in plages:
            key = (mois, plage)

            if plage == '23h-8h':
                # Nighttime: no solar, use original data
                night_data = df[(df['Mois'] == mois) & (df['Plage'] == plage)]
                if len(night_data) > 0:
                    row = night_data.iloc[0]
                    balance = row['Production_kW'] - row['Consommation_kW']
                    duration = row['Duree_h']
            elif key in solar_cf:
                # Daytime: scale solar
                data = solar_cf[key]
                new_solar = data['cf'] * new_capacity_kw
                new_total_prod = data['base_prod'] + new_solar
                balance = new_total_prod - data['conso']
                duration = data['duree']
            else:
                continue

            if balance > 0:
                daily_surplus_kwh += balance * duration
            else:
                daily_deficit_kwh += abs(balance) * duration

        # Storage transfers surplus to offset deficit
        usable_surplus = daily_surplus_kwh * efficiency
        net_deficit_kwh = max(0, daily_deficit_kwh - usable_surplus)

        # Convert to monthly TWh
        jours = config.temporal.jours_par_mois
        gas_twh = net_deficit_kwh * jours / 1e9
        total_gas_twh += gas_twh

    return total_gas_twh


def run_sensitivity_analysis(
    df: pd.DataFrame,
    solar_cf: Dict[Tuple[str, str], Dict],
    extra_range: Optional[np.ndarray] = None,
    config: Optional[EnergyModelConfig] = None
) -> pd.DataFrame:
    """
    Run sensitivity analysis across a range of solar capacities.

    Args:
        df: Original DataFrame
        solar_cf: Capacity factor data
        extra_range: Array of extra solar values (default: -400 to +500 GWc)
        config: Model configuration

    Returns:
        DataFrame with columns:
        - extra_solar_gwc: Additional capacity
        - total_solar_gwc: Total installed capacity
        - gas_no_storage_twh: Gas need without storage
        - gas_with_storage_twh: Gas need with storage
        - storage_benefit_twh: Reduction from storage
    """
    if config is None:
        config = DEFAULT_CONFIG

    if extra_range is None:
        extra_range = np.arange(-400, 501, 25)

    results = []
    baseline = config.production.solar_capacity_gwc

    for extra in extra_range:
        gas_no_storage = calculate_gas_need_no_storage(
            extra, solar_cf, df, config
        )
        gas_with_storage = calculate_gas_need_with_storage(
            extra, solar_cf, df, config
        )

        results.append({
            'extra_solar_gwc': extra,
            'total_solar_gwc': baseline + extra,
            'gas_no_storage_twh': gas_no_storage,
            'gas_with_storage_twh': gas_with_storage,
            'storage_benefit_twh': gas_no_storage - gas_with_storage,
        })

    return pd.DataFrame(results)


def find_zero_gas_capacity(
    df: pd.DataFrame,
    solar_cf: Dict[Tuple[str, str], Dict],
    config: Optional[EnergyModelConfig] = None,
    with_storage: bool = True,
    tolerance_twh: float = 0.5
) -> float:
    """
    Find the solar capacity needed to eliminate gas backup.

    Uses binary search to find the capacity where gas need drops to zero.

    Args:
        df: Original DataFrame
        solar_cf: Capacity factor data
        config: Model configuration
        with_storage: Whether to include daily storage
        tolerance_twh: Acceptable residual gas (default 0.5 TWh)

    Returns:
        Total solar capacity in GWc needed for zero gas
    """
    if config is None:
        config = DEFAULT_CONFIG

    baseline = config.production.solar_capacity_gwc

    # Binary search
    low, high = -400, 1000
    calc_func = (
        calculate_gas_need_with_storage if with_storage
        else calculate_gas_need_no_storage
    )

    while high - low > 1:
        mid = (low + high) // 2
        gas = calc_func(mid, solar_cf, df, config)
        if gas > tolerance_twh:
            low = mid
        else:
            high = mid

    return baseline + high
