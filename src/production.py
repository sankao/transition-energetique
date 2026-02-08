"""
Production module for the Energy Transition Model.

Handles solar, nuclear, and hydro production calculations.
"""

from typing import Dict, Optional, Tuple
import pandas as pd

from .config import EnergyModelConfig, DEFAULT_CONFIG
from .temporal import fraction_solaire_attendue


def extract_base_production(
    df: pd.DataFrame,
    config: Optional[EnergyModelConfig] = None
) -> Dict[str, float]:
    """
    Extract base production (nuclear + hydro) from nighttime data.

    Since there's no solar production at night (23h-8h), the nighttime
    production represents the nuclear + hydro baseline.

    Args:
        df: DataFrame with 'Mois', 'Plage', 'Production_kW' columns
        config: Model configuration

    Returns:
        Dict mapping month names to base production in kW
    """
    base_prod_by_month = {}

    for mois in df['Mois'].unique():
        night_data = df[(df['Mois'] == mois) & (df['Plage'] == '23h-8h')]
        if len(night_data) > 0:
            base_prod_by_month[mois] = night_data['Production_kW'].values[0]

    return base_prod_by_month


def calculate_solar_capacity_factors(
    df: pd.DataFrame,
    base_prod_by_month: Dict[str, float],
    config: Optional[EnergyModelConfig] = None
) -> Dict[Tuple[str, str], Dict]:
    """
    Calculate solar capacity factors from production data.

    For each (month, time_slot) combination, compute:
    - The fraction of installed capacity that produces power
    - The base production (nuclear + hydro)
    - The consumption
    - The slot duration

    Args:
        df: DataFrame with production data
        base_prod_by_month: Base production by month (from extract_base_production)
        config: Model configuration

    Returns:
        Dict mapping (month, slot) to capacity factor data
    """
    if config is None:
        config = DEFAULT_CONFIG

    solar_capacity_kw = config.production.solar_capacity_gwc * 1e6
    solar_cf = {}

    for _, row in df.iterrows():
        mois = row['Mois']
        plage = row['Plage']

        # Skip nighttime slots (no solar)
        if plage == '23h-8h':
            continue

        base = base_prod_by_month.get(mois, 50e6)
        total_prod = row['Production_kW']
        solar_prod = max(0, total_prod - base)

        # Capacity factor = solar production / installed capacity
        cf = solar_prod / solar_capacity_kw if solar_capacity_kw > 0 else 0

        solar_cf[(mois, plage)] = {
            'cf': cf,
            'base_prod': base,
            'conso': row['Consommation_kW'],
            'duree': row['Duree_h']
        }

    return solar_cf


def scale_production(
    solar_cf: Dict[Tuple[str, str], Dict],
    new_capacity_gwc: float,
    config: Optional[EnergyModelConfig] = None
) -> Dict[Tuple[str, str], Dict]:
    """
    Scale production to a new solar capacity.

    Uses the capacity factors to calculate what production would be
    with a different installed solar capacity.

    Args:
        solar_cf: Capacity factor data from calculate_solar_capacity_factors
        new_capacity_gwc: New solar capacity in GWc
        config: Model configuration

    Returns:
        Dict with scaled production data for each (month, slot)
    """
    new_capacity_kw = new_capacity_gwc * 1e6
    scaled = {}

    for (mois, plage), data in solar_cf.items():
        new_solar_kw = data['cf'] * new_capacity_kw
        new_total_prod = data['base_prod'] + new_solar_kw

        scaled[(mois, plage)] = {
            'production_kw': new_total_prod,
            'solar_kw': new_solar_kw,
            'base_kw': data['base_prod'],
            'conso_kw': data['conso'],
            'duree': data['duree'],
            'deficit_kw': max(0, data['conso'] - new_total_prod),
            'surplus_kw': max(0, new_total_prod - data['conso']),
        }

    return scaled


def detect_production_anomalies(
    df: pd.DataFrame,
    config: Optional[EnergyModelConfig] = None
) -> pd.DataFrame:
    """
    Detect anomalies in production data.

    Checks if production values are physically plausible given:
    - Time of sunset for each month
    - Maximum possible solar + base production

    Args:
        df: DataFrame with production data
        config: Model configuration

    Returns:
        DataFrame with anomalies (production > expected maximum)
    """
    if config is None:
        config = DEFAULT_CONFIG

    prod_base_max = config.production.prod_base_max_gw * 1e6  # Convert to kW
    prod_solaire_max = config.production.prod_solaire_max_gw * 1e6

    anomalies = []

    for _, row in df.iterrows():
        prod_kw = row['Production_kW']
        plage = row['Plage']
        mois = row['Mois']

        # Calculate expected maximum production
        fraction_soleil = fraction_solaire_attendue(mois, plage, config)
        prod_max_kw = prod_base_max + fraction_soleil * prod_solaire_max

        # Check for anomaly (with 20 GW margin)
        margin_kw = 20e6
        if prod_kw > prod_max_kw + margin_kw:
            anomalies.append({
                'Mois': mois,
                'Plage': plage,
                'Production_GW': prod_kw / 1e6,
                'Attendu_max_GW': prod_max_kw / 1e6,
                'Ecart_GW': (prod_kw - prod_max_kw) / 1e6,
                'Fraction_soleil': fraction_soleil,
                'Sunset': config.temporal.sunset_times.get(mois, 18.0),
            })

    return pd.DataFrame(anomalies)
