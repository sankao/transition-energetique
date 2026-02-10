"""PVGIS solar capacity factor downloader.

Fetches hourly solar production from EU JRC PVGIS API for representative
French locations, computes population-weighted capacity factors by
(month, time_slot) for the 60-row model grid.
"""

import json
import time
from pathlib import Path
from typing import Optional

import requests


MOIS_ORDRE = (
    'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
    'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
)
PLAGES = ('8h-13h', '13h-18h', '18h-20h', '20h-23h', '23h-8h')
MONTH_NUM_TO_FR = {i+1: m for i, m in enumerate(MOIS_ORDRE)}

PVGIS_API_URL = "https://re.jrc.ec.europa.eu/api/v5_2/seriescalc"

# 7 representative French locations with population weights
LOCATIONS = [
    {'name': 'Paris_IdF', 'lat': 48.86, 'lon': 2.35, 'weight': 0.20},
    {'name': 'Lyon', 'lat': 45.76, 'lon': 4.83, 'weight': 0.15},
    {'name': 'Marseille', 'lat': 43.30, 'lon': 5.37, 'weight': 0.15},
    {'name': 'Toulouse', 'lat': 43.60, 'lon': 1.44, 'weight': 0.12},
    {'name': 'Nantes', 'lat': 47.22, 'lon': -1.55, 'weight': 0.13},
    {'name': 'Strasbourg', 'lat': 48.57, 'lon': 7.75, 'weight': 0.10},
    {'name': 'Lille', 'lat': 50.63, 'lon': 3.06, 'weight': 0.15},
]


def assign_time_slot(hour: int) -> str:
    """Map hour 0-23 to model time slot."""
    if 8 <= hour < 13:
        return '8h-13h'
    elif 13 <= hour < 18:
        return '13h-18h'
    elif 18 <= hour < 20:
        return '18h-20h'
    elif 20 <= hour < 23:
        return '20h-23h'
    else:
        return '23h-8h'


def fetch_pvgis_hourly(lat: float, lon: float, name: str = "", cache_dir: Optional[str] = None) -> list:
    """Fetch hourly PV output for 1 kWp at given location from PVGIS TMY data.

    Args:
        lat: Latitude
        lon: Longitude
        name: Location name for cache file
        cache_dir: Cache directory

    Returns:
        List of dicts with month, hour, power_kw (output of 1 kWp system)
    """
    if cache_dir is None:
        cache_dir = "data/cache"
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)

    safe_name = name.replace('/', '_').replace(' ', '_') if name else f"{lat}_{lon}"
    cache_file = cache_path / f"pvgis_{safe_name}.json"

    if cache_file.exists():
        with open(cache_file, 'r') as f:
            return json.load(f)

    params = {
        'lat': lat,
        'lon': lon,
        'pvcalculation': 1,
        'peakpower': 1,  # 1 kWp normalized
        'loss': 14,
        'outputformat': 'json',
    }

    response = requests.get(PVGIS_API_URL, params=params, timeout=60)
    response.raise_for_status()
    data = response.json()

    hourly = data.get('outputs', {}).get('hourly', [])

    records = []
    for entry in hourly:
        # PVGIS time format: "20050101:0010" (YYYYMMDD:HHMM)
        time_str = entry.get('time', '')
        month = int(time_str[4:6])
        hour = int(time_str[9:11])
        power = entry.get('P', 0.0) / 1000.0  # W to kW for 1 kWp

        records.append({
            'month': month,
            'hour': hour,
            'power_kw': power,
        })

    with open(cache_file, 'w') as f:
        json.dump(records, f)

    return records


def compute_capacity_factors(hourly_records: list) -> dict:
    """Aggregate hourly data to capacity factors by (month, time_slot).

    Capacity factor = mean_power / peak_power. Since peakpower=1 kWp,
    CF = mean(power_kw).

    Args:
        hourly_records: From fetch_pvgis_hourly

    Returns:
        Dict mapping (month_num, plage) -> capacity_factor
    """
    from collections import defaultdict

    sums = defaultdict(lambda: {'power_sum': 0.0, 'count': 0})

    for rec in hourly_records:
        plage = assign_time_slot(rec['hour'])
        key = (rec['month'], plage)
        sums[key]['power_sum'] += rec['power_kw']
        sums[key]['count'] += 1

    factors = {}
    for key, s in sums.items():
        if s['count'] > 0:
            factors[key] = s['power_sum'] / s['count']
        else:
            factors[key] = 0.0

    return factors


def download_pvgis_capacity_factors(cache_dir: Optional[str] = None) -> list:
    """High-level: download and compute weighted-average capacity factors.

    Fetches hourly data for 7 representative French locations,
    computes per-location capacity factors, then population-weighted average.

    Returns 60 rows (12 months x 5 time slots).

    Args:
        cache_dir: Cache directory

    Returns:
        List of 60 tuples (mois, plage, capacity_factor)
    """
    # Collect per-location capacity factors
    location_factors = []

    for loc in LOCATIONS:
        hourly = fetch_pvgis_hourly(
            lat=loc['lat'], lon=loc['lon'],
            name=loc['name'], cache_dir=cache_dir
        )
        factors = compute_capacity_factors(hourly)
        location_factors.append((factors, loc['weight']))
        time.sleep(1)  # Be nice to the API

    # Weighted average
    result = []
    for month_num, mois in enumerate(MOIS_ORDRE, 1):
        for plage in PLAGES:
            weighted_cf = 0.0
            for factors, weight in location_factors:
                cf = factors.get((month_num, plage), 0.0)
                weighted_cf += cf * weight
            result.append((mois, plage, weighted_cf))

    return result
