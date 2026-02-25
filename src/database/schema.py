"""SQLite schema for the energy model database."""

TABLES = {
    'metadata': """
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """,
    'parametres': """
        CREATE TABLE IF NOT EXISTS parametres (
            name TEXT PRIMARY KEY,
            value REAL,
            unit TEXT,
            source TEXT,
            description TEXT
        )
    """,
    'prod_nucleaire_hydraulique': """
        CREATE TABLE IF NOT EXISTS prod_nucleaire_hydraulique (
            mois TEXT,
            plage TEXT,
            nucleaire_mw REAL,
            hydraulique_mw REAL,
            PRIMARY KEY (mois, plage)
        )
    """,
    'facteurs_solaires_pvgis': """
        CREATE TABLE IF NOT EXISTS facteurs_solaires_pvgis (
            mois TEXT,
            plage TEXT,
            capacity_factor REAL,
            PRIMARY KEY (mois, plage)
        )
    """,
    'consommation_chauffage': """
        CREATE TABLE IF NOT EXISTS consommation_chauffage (
            mois TEXT,
            plage TEXT,
            temperature_ext REAL,
            cop REAL,
            besoin_electrique_kw REAL,
            PRIMARY KEY (mois, plage)
        )
    """,
    'consommation_sectors': """
        CREATE TABLE IF NOT EXISTS consommation_sectors (
            mois TEXT,
            plage TEXT,
            transport_kw REAL,
            industrie_kw REAL,
            tertiaire_kw REAL,
            agriculture_kw REAL,
            PRIMARY KEY (mois, plage)
        )
    """,
    'synthese_moulinette': """
        CREATE TABLE IF NOT EXISTS synthese_moulinette (
            mois TEXT,
            plage TEXT,
            pv_maisons_kw REAL,
            pv_collectif_kw REAL,
            pv_centrales_kw REAL,
            hydraulique_kw REAL,
            eolien_kw REAL,
            nucleaire_kw REAL,
            total_production_kw REAL,
            chauffage_kw REAL,
            transport_kw REAL,
            industrie_kw REAL,
            tertiaire_kw REAL,
            agriculture_kw REAL,
            total_conso_kw REAL,
            deficit_gaz_kw REAL,
            duree_h REAL,
            energie_gaz_twh REAL,
            PRIMARY KEY (mois, plage)
        )
    """,
    'bilan_electrification': """
        CREATE TABLE IF NOT EXISTS bilan_electrification (
            sector TEXT PRIMARY KEY,
            current_twh REAL,
            elec_twh REAL,
            h2_twh REAL,
            bio_enr_twh REAL,
            fossil_residual_twh REAL,
            total_target_twh REAL,
            h2_production_elec_twh REAL
        )
    """
}
