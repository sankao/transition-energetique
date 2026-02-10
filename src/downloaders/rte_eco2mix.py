"""RTE eco2mix downloader — nuclear and hydraulic production data.

API: OpenDataSoft eco2mix national consolidated data.
Returns 60-row DataFrame (12 months × 5 time slots) with mean production in MW.
"""

import csv
import json
import time
from pathlib import Path
from typing import Optional

import requests


# French month names matching config.TemporalConfig.mois_ordre
MOIS_ORDRE = (
    'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
    'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
)
PLAGES = ('8h-13h', '13h-18h', '18h-20h', '20h-23h', '23h-8h')

# Map month number (1-12) to French name
MONTH_NUM_TO_FR = {i+1: m for i, m in enumerate(MOIS_ORDRE)}

API_URL = "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-national-cons-def/records"


def assign_time_slot(hour: int) -> str:
    """Map hour 0-23 to one of 5 time slots.

    Slots: 8h-13h, 13h-18h, 18h-20h, 20h-23h, 23h-8h.
    The 23h-8h slot wraps midnight.
    """
    if 8 <= hour < 13:
        return '8h-13h'
    elif 13 <= hour < 18:
        return '13h-18h'
    elif 18 <= hour < 20:
        return '18h-20h'
    elif 20 <= hour < 23:
        return '20h-23h'
    else:  # 23, 0, 1, 2, 3, 4, 5, 6, 7
        return '23h-8h'


def fetch_eco2mix_raw(year: int = 2023, cache_dir: Optional[str] = None) -> list:
    """Fetch half-hourly eco2mix data for a year from OpenDataSoft API.

    Paginates through all records (100 per page, ~17,520 records/year).
    Caches raw JSON response to avoid repeated API calls.

    Args:
        year: Reference year (default 2023)
        cache_dir: Directory for caching (default: data/cache)

    Returns:
        List of dicts with date_heure, nucleaire, hydraulique fields
    """
    if cache_dir is None:
        cache_dir = "data/cache"
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)

    cache_file = cache_path / f"eco2mix_{year}.json"
    if cache_file.exists():
        with open(cache_file, 'r') as f:
            return json.load(f)

    all_records = []
    limit = 100

    # Paginate by month to stay under API offset limit (10000)
    for month in range(1, 13):
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1
        where_clause = (
            f"date_heure >= '{year}-{month:02d}-01' "
            f"AND date_heure < '{next_year}-{next_month:02d}-01'"
        )

        offset = 0
        while True:
            params = {
                'select': 'date_heure,nucleaire,hydraulique',
                'where': where_clause,
                'limit': limit,
                'offset': offset,
                'order_by': 'date_heure',
            }

            response = requests.get(API_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            results = data.get('results', [])
            if not results:
                break

            for r in results:
                if r.get('nucleaire') is not None and r.get('hydraulique') is not None:
                    all_records.append({
                        'date_heure': r['date_heure'],
                        'nucleaire': r['nucleaire'],
                        'hydraulique': r['hydraulique'],
                    })

            offset += limit
            total = data.get('total_count', 0)
            if offset >= total:
                break

            time.sleep(0.1)

        print(f"      Month {month:2d}: {offset + len(results) if results else offset} records")

    # Cache
    with open(cache_file, 'w') as f:
        json.dump(all_records, f)

    return all_records


def aggregate_to_monthly_slots(raw_records: list) -> list:
    """Aggregate half-hourly records to monthly time slot averages.

    Groups by (month, time_slot) and computes mean nuclear and hydraulic MW.

    Args:
        raw_records: List of dicts from fetch_eco2mix_raw()

    Returns:
        List of 60 tuples (mois, plage, nucleaire_mw, hydraulique_mw)
    """
    from collections import defaultdict

    # Accumulate sums and counts
    sums = defaultdict(lambda: {'nuc_sum': 0.0, 'hyd_sum': 0.0, 'count': 0})

    for rec in raw_records:
        dt_str = rec['date_heure']
        # Parse ISO format: "2023-01-15T08:30:00+01:00" or "2023-01-15T08:30:00+00:00"
        # We just need month and hour
        month = int(dt_str[5:7])
        hour = int(dt_str[11:13])

        mois = MONTH_NUM_TO_FR[month]
        plage = assign_time_slot(hour)

        key = (mois, plage)
        sums[key]['nuc_sum'] += rec['nucleaire']
        sums[key]['hyd_sum'] += rec['hydraulique']
        sums[key]['count'] += 1

    # Build 60 rows in canonical order
    result = []
    for mois in MOIS_ORDRE:
        for plage in PLAGES:
            key = (mois, plage)
            if key in sums and sums[key]['count'] > 0:
                s = sums[key]
                nuc_avg = s['nuc_sum'] / s['count']
                hyd_avg = s['hyd_sum'] / s['count']
            else:
                nuc_avg = 0.0
                hyd_avg = 0.0
            result.append((mois, plage, nuc_avg, hyd_avg))

    return result


def download_rte_production(year: int = 2023, cache_dir: Optional[str] = None) -> list:
    """High-level orchestrator: download and aggregate RTE production data.

    Returns 60 rows (12 months × 5 time slots) of mean nuclear and hydraulic
    production in MW.

    Args:
        year: Reference year
        cache_dir: Cache directory path

    Returns:
        List of 60 tuples (mois, plage, nucleaire_mw, hydraulique_mw)
    """
    raw = fetch_eco2mix_raw(year, cache_dir)
    return aggregate_to_monthly_slots(raw)
