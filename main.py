"""Energy model data pipeline — download, compute, generate ODS.

Usage:
    uv run python main.py                  # Full pipeline
    uv run python main.py --skip-download  # Use existing DB
    uv run python main.py --download-only  # Just fetch data
    uv run python main.py --year 2022      # Different reference year
    uv run python main.py --output foo.ods # Custom output path
"""

import argparse
import sys
from datetime import datetime

from src.config import EnergyModelConfig
from src.database.store import EnergyModelDB
from src.downloaders.rte_eco2mix import download_rte_production
from src.downloaders.pvgis_solar import download_pvgis_capacity_factors
from src.heating import HeatingConfig, besoin_national_chauffage_kw
from src.transport import TransportConfig, demande_recharge_par_plage
from src.secteurs import bilan_industrie, bilan_tertiaire, IndustrieConfig, TertiaireConfig
from src.agriculture import consommation_mensuelle_twh, AgricultureConfig
from src.ods_generator.writer import ODSWriter
from src.ods_generator.source_sheets import add_all_source_sheets
from src.ods_generator.synthesis_sheet import add_synthesis_sheet


MOIS_ORDRE = (
    'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
    'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
)
PLAGES = ('8h-13h', '13h-18h', '18h-20h', '20h-23h', '23h-8h')
DUREES = {'8h-13h': 5.0, '13h-18h': 5.0, '18h-20h': 2.0, '20h-23h': 3.0, '23h-8h': 9.0}


def download_data(year, cache_dir, db):
    """Step 1: Download RTE and PVGIS data."""
    print(f"[1/5] Downloading RTE eco2mix data (year={year})...")
    rte_rows = download_rte_production(year=year, cache_dir=cache_dir)
    db.store_rte_production(rte_rows)
    print(f"      Stored {len(rte_rows)} rows of nuclear/hydraulic data")

    print("[1/5] Downloading PVGIS solar capacity factors...")
    pvgis_rows = download_pvgis_capacity_factors(cache_dir=cache_dir)
    db.store_pvgis_factors(pvgis_rows)
    print(f"      Stored {len(pvgis_rows)} rows of solar capacity factors")


def compute_consumption(db, config, heating_config, transport_config,
                        industrie_config, tertiaire_config, agriculture_config):
    """Step 2: Compute heating, transport, sector, agriculture consumption."""
    print("[2/5] Computing consumption models...")

    # Parameters (all 142 knobs via knob registry)
    db.store_parameters(
        config,
        heating_config=heating_config,
        transport_config=transport_config,
        industrie_config=industrie_config,
        tertiaire_config=tertiaire_config,
        agriculture_config=agriculture_config,
    )

    # Heating (60 rows via Roland model with COP(T))
    db.store_heating_data(heating_config)
    print("      Heating: 60 rows (COP variable)")

    # Sector consumption (transport, industry, tertiary, agriculture)
    db.store_sector_data(
        transport_config=transport_config,
        industrie_config=industrie_config,
        tertiaire_config=tertiaire_config,
        agriculture_config=agriculture_config,
    )
    print("      Sectors: 60 rows (transport, industry, tertiary, agriculture)")


def compute_synthesis(db, config):
    """Step 3: Compute the 60-row synthesis (production - consumption = deficit)."""
    print("[3/5] Computing synthesis...")

    rte_data = db.load_rte_production()
    pvgis_data = db.load_pvgis_factors()
    heating_data = db.load_heating_data()
    sector_data = db.load_sector_data()

    # Build lookups
    rte_lookup = {(r['mois'], r['plage']): r for r in rte_data}
    pvgis_lookup = {(r['mois'], r['plage']): r for r in pvgis_data}
    heating_lookup = {(r['mois'], r['plage']): r for r in heating_data}
    sector_lookup = {(r['mois'], r['plage']): r for r in sector_data}

    jours = config.temporal.jours_par_mois

    # PV parameters from config
    p = config.production
    kwc_maison = p.kwc_par_maison
    nombre_maisons = p.nombre_maisons
    kwc_collectif = p.kwc_par_collectif
    nombre_collectifs = p.nombre_collectifs
    gwc_centrales = p.solar_gwc_centrales

    synthesis_rows = []
    total_gas_twh = 0.0

    for mois in MOIS_ORDRE:
        for plage in PLAGES:
            key = (mois, plage)

            cf = pvgis_lookup.get(key, {}).get('capacity_factor', 0.0)
            nuc_mw = rte_lookup.get(key, {}).get('nucleaire_mw', 0.0)
            hyd_mw = rte_lookup.get(key, {}).get('hydraulique_mw', 0.0)

            # Production (kW)
            pv_maisons = kwc_maison * nombre_maisons * 1000 * cf
            pv_collectif = kwc_collectif * nombre_collectifs * 1000 * cf
            pv_centrales = gwc_centrales * 1_000_000 * cf
            hydraulique = hyd_mw * 1000
            eolien = 0.0
            nucleaire = nuc_mw * 1000
            total_prod = pv_maisons + pv_collectif + pv_centrales + hydraulique + eolien + nucleaire

            # Consumption (kW)
            chauffage = heating_lookup.get(key, {}).get('besoin_electrique_kw', 0.0)
            transport = sector_lookup.get(key, {}).get('transport_kw', 0.0)
            industrie = sector_lookup.get(key, {}).get('industrie_kw', 0.0)
            tertiaire = sector_lookup.get(key, {}).get('tertiaire_kw', 0.0)
            agriculture = sector_lookup.get(key, {}).get('agriculture_kw', 0.0)
            total_conso = chauffage + transport + industrie + tertiaire + agriculture

            # Deficit
            deficit = max(0.0, total_conso - total_prod)
            duree = DUREES[plage]
            energie_gaz = deficit * duree * jours / 1e9

            total_gas_twh += energie_gaz

            synthesis_rows.append((
                mois, plage,
                pv_maisons, pv_collectif, pv_centrales,
                hydraulique, eolien, nucleaire, total_prod,
                chauffage, transport, industrie, tertiaire, agriculture,
                total_conso, deficit, duree, energie_gaz,
            ))

    db.store_synthesis(synthesis_rows)
    print(f"      Synthesis: {len(synthesis_rows)} rows, gas backup: {total_gas_twh:.1f} TWh/year")
    return total_gas_twh


def generate_ods(db, output_path, config=None, heating_config=None,
                 transport_config=None, industrie_config=None,
                 tertiaire_config=None, agriculture_config=None):
    """Step 4: Generate ODS file with source sheets and synthesis formulas."""
    print(f"[4/5] Generating ODS: {output_path}")

    writer = ODSWriter()
    add_all_source_sheets(
        writer, db,
        config=config,
        heating_config=heating_config,
        transport_config=transport_config,
        industrie_config=industrie_config,
        tertiaire_config=tertiaire_config,
        agriculture_config=agriculture_config,
    )
    add_synthesis_sheet(writer, db)
    writer.save(output_path)

    import os
    size = os.path.getsize(output_path)
    print(f"      Saved {output_path} ({size:,} bytes, {len(writer.sheets)} sheets)")


def main():
    parser = argparse.ArgumentParser(description="Energy model data pipeline")
    parser.add_argument('--year', type=int, default=2023,
                        help='Reference year for RTE data (default: 2023)')
    parser.add_argument('--output', type=str, default='output/modele_transition.ods',
                        help='Output ODS path')
    parser.add_argument('--db', type=str, default='data/energy_model.db',
                        help='SQLite database path')
    parser.add_argument('--cache-dir', type=str, default='data/cache',
                        help='Download cache directory')
    parser.add_argument('--skip-download', action='store_true',
                        help='Skip downloading, use existing DB')
    parser.add_argument('--download-only', action='store_true',
                        help='Only download data, do not generate ODS')
    args = parser.parse_args()

    config = EnergyModelConfig()
    heating_config = HeatingConfig()
    transport_config = TransportConfig()
    industrie_config = IndustrieConfig()
    tertiaire_config = TertiaireConfig()
    agriculture_config = AgricultureConfig()

    print("=" * 60)
    print("Energy Transition Model — Data Pipeline")
    print(f"  Year: {args.year}")
    print(f"  DB:   {args.db}")
    print(f"  ODS:  {args.output}")
    print("=" * 60)

    with EnergyModelDB(args.db) as db:
        db.store_metadata('pipeline_start', datetime.now().isoformat())
        db.store_metadata('year', str(args.year))

        if not args.skip_download:
            download_data(args.year, args.cache_dir, db)

        compute_consumption(db, config, heating_config, transport_config,
                            industrie_config, tertiaire_config, agriculture_config)
        gas_total = compute_synthesis(db, config)

        if args.download_only:
            print("[4/5] Skipped ODS generation (--download-only)")
        else:
            generate_ods(db, args.output,
                         config=config,
                         heating_config=heating_config,
                         transport_config=transport_config,
                         industrie_config=industrie_config,
                         tertiaire_config=tertiaire_config,
                         agriculture_config=agriculture_config)

        db.store_metadata('pipeline_end', datetime.now().isoformat())
        db.store_metadata('gas_total_twh', f"{gas_total:.2f}")

    print()
    print(f"[5/5] Pipeline complete!")
    print(f"      Gas backup: {gas_total:.1f} TWh/year @ 500 GWc solar")
    print(f"      Open {args.output} in LibreOffice to explore formulas")


if __name__ == "__main__":
    main()
