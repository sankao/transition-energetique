"""
Financial analysis module for the Energy Transition Model.

Cost calculations and scenario comparisons.
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

from .config import EnergyModelConfig, DEFAULT_CONFIG
from .sensitivity import calculate_gas_need_no_storage, calculate_gas_need_with_storage
from .storage import calculate_storage_need


def calculate_scenario_costs(
    extra_solar_gwc: float,
    solar_cf: Dict[Tuple[str, str], Dict],
    df: pd.DataFrame,
    config: Optional[EnergyModelConfig] = None
) -> Dict[str, float]:
    """
    Calculate costs for a given solar capacity scenario.

    Args:
        extra_solar_gwc: Additional solar beyond baseline
        solar_cf: Capacity factor data
        df: Original DataFrame
        config: Model configuration

    Returns:
        Dict with cost breakdown:
        - total_solar_gwc: Total installed capacity
        - gas_need_twh: Annual gas backup need
        - storage_need_gwh: Required storage capacity
        - gas_cost_annual_eur_b: Annual gas cost (€B)
        - solar_capex_eur_b: Solar CAPEX (€B)
        - storage_capex_eur_b: Storage CAPEX (€B)
        - total_capex_eur_b: Total CAPEX (€B)
        - total_30y_eur_b: Total cost over 30 years (€B)
    """
    if config is None:
        config = DEFAULT_CONFIG

    baseline = config.production.solar_capacity_gwc
    total_solar = max(0, baseline + extra_solar_gwc)

    # Gas need with storage
    gas_need = calculate_gas_need_with_storage(extra_solar_gwc, solar_cf, df, config)
    gas_cost_annual = gas_need * config.financial.gas_cost_eur_per_mwh / 1000  # €B

    # Storage requirement
    storage_need = calculate_storage_need(extra_solar_gwc, solar_cf, df, config)

    # CAPEX (from zero base - the model assumes these are new investments)
    solar_capex = total_solar * config.financial.solar_capex_eur_per_kw / 1000  # €B
    storage_capex = storage_need * config.financial.storage_capex_eur_per_kwh / 1000  # €B
    total_capex = solar_capex + storage_capex

    # Total cost over analysis horizon
    horizon = config.financial.analysis_horizon_years
    total_30y = total_capex + gas_cost_annual * horizon

    return {
        'extra_solar_gwc': extra_solar_gwc,
        'total_solar_gwc': total_solar,
        'gas_need_twh': gas_need,
        'storage_need_gwh': storage_need,
        'gas_cost_annual_eur_b': gas_cost_annual,
        'solar_capex_eur_b': solar_capex,
        'storage_capex_eur_b': storage_capex,
        'total_capex_eur_b': total_capex,
        'total_30y_eur_b': total_30y,
    }


def run_financial_analysis(
    df: pd.DataFrame,
    solar_cf: Dict[Tuple[str, str], Dict],
    extra_range: Optional[List[float]] = None,
    config: Optional[EnergyModelConfig] = None
) -> pd.DataFrame:
    """
    Run financial analysis across a range of solar capacities.

    Args:
        df: Original DataFrame
        solar_cf: Capacity factor data
        extra_range: List of extra solar values to analyze
        config: Model configuration

    Returns:
        DataFrame with cost analysis for each scenario
    """
    if config is None:
        config = DEFAULT_CONFIG

    if extra_range is None:
        extra_range = list(range(-400, 501, 50))

    results = []
    for extra in extra_range:
        costs = calculate_scenario_costs(extra, solar_cf, df, config)
        results.append(costs)

    return pd.DataFrame(results)


def find_optimal_capacity(
    df: pd.DataFrame,
    solar_cf: Dict[Tuple[str, str], Dict],
    config: Optional[EnergyModelConfig] = None
) -> Dict[str, float]:
    """
    Find the solar capacity that minimizes total 30-year cost.

    Args:
        df: Original DataFrame
        solar_cf: Capacity factor data
        config: Model configuration

    Returns:
        Dict with optimal scenario parameters
    """
    if config is None:
        config = DEFAULT_CONFIG

    # Search range
    extra_range = np.arange(-400, 501, 10)
    min_cost = float('inf')
    optimal = None

    for extra in extra_range:
        costs = calculate_scenario_costs(extra, solar_cf, df, config)
        if costs['total_30y_eur_b'] < min_cost:
            min_cost = costs['total_30y_eur_b']
            optimal = costs

    return optimal


def compare_scenarios(
    df: pd.DataFrame,
    solar_cf: Dict[Tuple[str, str], Dict],
    scenarios: Optional[Dict[str, float]] = None,
    config: Optional[EnergyModelConfig] = None
) -> pd.DataFrame:
    """
    Compare specific named scenarios.

    Args:
        df: Original DataFrame
        solar_cf: Capacity factor data
        scenarios: Dict mapping scenario names to extra solar GWc
        config: Model configuration

    Returns:
        DataFrame comparing scenarios
    """
    if config is None:
        config = DEFAULT_CONFIG

    if scenarios is None:
        # Default scenarios based on the model
        scenarios = {
            'France ×5 (100 GWc)': -400,
            'Intermédiaire (300 GWc)': -200,
            'Modèle initial (500 GWc)': 0,
            'Optimum (~700 GWc)': 200,
            'Zéro gaz (~950 GWc)': 450,
        }

    results = []
    for name, extra in scenarios.items():
        costs = calculate_scenario_costs(extra, solar_cf, df, config)
        costs['scenario'] = name
        results.append(costs)

    result_df = pd.DataFrame(results)

    # Add comparison to optimal
    optimal = find_optimal_capacity(df, solar_cf, config)
    optimal_cost = optimal['total_30y_eur_b']
    result_df['vs_optimal_eur_b'] = result_df['total_30y_eur_b'] - optimal_cost

    return result_df


def calculate_payback(
    solar_capex_eur_b: float,
    storage_capex_eur_b: float,
    annual_savings_eur_b: float
) -> float:
    """
    Calculate simple payback period.

    Args:
        solar_capex_eur_b: Solar CAPEX in €B
        storage_capex_eur_b: Storage CAPEX in €B
        annual_savings_eur_b: Annual gas savings in €B

    Returns:
        Payback period in years (inf if no savings)
    """
    total_capex = solar_capex_eur_b + storage_capex_eur_b
    if annual_savings_eur_b <= 0:
        return float('inf')
    return total_capex / annual_savings_eur_b
