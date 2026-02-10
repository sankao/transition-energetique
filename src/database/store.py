"""SQLite store for the energy model — single source of truth."""

import sqlite3
from pathlib import Path
from typing import Optional

from .schema import TABLES


class EnergyModelDB:
    """Energy model database with context manager support."""

    def __init__(self, db_path: str = "data/energy_model.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn: Optional[sqlite3.Connection] = None

    def __enter__(self):
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()
            self.conn = None

    def _create_tables(self):
        for table_sql in TABLES.values():
            self.conn.execute(table_sql)
        self.conn.commit()

    def store_parameters(self, config):
        """Store all EnergyModelConfig params. config is an EnergyModelConfig instance."""
        # Store key parameters that the ODS synthesis will reference
        p = config.production
        params = [
            ('solar_gwc_maisons', p.solar_gwc_maisons, 'GWc', 'Model scenario', 'PV résidentiel individuel'),
            ('solar_gwc_collectif', p.solar_gwc_collectif, 'GWc', 'Model scenario', 'PV résidentiel collectif'),
            ('solar_gwc_centrales', p.solar_gwc_centrales, 'GWc', 'Model scenario', 'PV centrales au sol'),
            ('nombre_maisons', p.nombre_maisons, 'unités', 'INSEE', 'Maisons individuelles'),
            ('nombre_collectifs', p.nombre_collectifs, 'unités', 'INSEE', 'Logements collectifs'),
            ('kwc_par_maison', p.kwc_par_maison, 'kWc', 'Model assumption', 'Puissance PV par maison'),
            ('kwc_par_collectif', p.kwc_par_collectif, 'kWc', 'Model assumption', 'Puissance PV par collectif'),
            ('cop_pac', config.consumption.heat_pump_cop, 'ratio', 'ADEME', 'COP pompe à chaleur'),
            ('jours_par_mois', config.temporal.jours_par_mois, 'jours', 'Simplification', 'Jours par mois'),
            ('solar_capacity_gwc', p.solar_capacity_gwc, 'GWc', 'Model scenario', 'Capacité solaire totale'),
            ('nuclear_min_gw', p.nuclear_min_gw, 'GW', 'RTE', 'Nucléaire minimum'),
            ('nuclear_max_gw', p.nuclear_max_gw, 'GW', 'RTE', 'Nucléaire maximum'),
            ('hydro_avg_gw', p.hydro_avg_gw, 'GW', 'RTE', 'Hydraulique moyen'),
        ]
        self.conn.executemany(
            "INSERT OR REPLACE INTO parametres (name, value, unit, source, description) VALUES (?, ?, ?, ?, ?)",
            params
        )
        self.conn.commit()

    def store_rte_production(self, rows):
        """Store RTE production data. rows is a list of (mois, plage, nucleaire_mw, hydraulique_mw) tuples."""
        self.conn.executemany(
            "INSERT OR REPLACE INTO prod_nucleaire_hydraulique (mois, plage, nucleaire_mw, hydraulique_mw) VALUES (?, ?, ?, ?)",
            rows
        )
        self.conn.commit()

    def load_rte_production(self):
        """Load RTE production as list of dicts."""
        cursor = self.conn.execute(
            "SELECT mois, plage, nucleaire_mw, hydraulique_mw FROM prod_nucleaire_hydraulique ORDER BY rowid"
        )
        return [dict(row) for row in cursor.fetchall()]

    def store_pvgis_factors(self, rows):
        """Store PVGIS capacity factors. rows is list of (mois, plage, capacity_factor) tuples."""
        self.conn.executemany(
            "INSERT OR REPLACE INTO facteurs_solaires_pvgis (mois, plage, capacity_factor) VALUES (?, ?, ?)",
            rows
        )
        self.conn.commit()

    def load_pvgis_factors(self):
        """Load PVGIS factors as list of dicts."""
        cursor = self.conn.execute(
            "SELECT mois, plage, capacity_factor FROM facteurs_solaires_pvgis ORDER BY rowid"
        )
        return [dict(row) for row in cursor.fetchall()]

    def store_heating_data(self, heating_config):
        """Compute and store 60 heating rows using besoin_national_chauffage_kw().

        heating_config is a HeatingConfig instance.
        Import from src.heating: besoin_national_chauffage_kw, interpoler_cop
        """
        from src.heating import besoin_national_chauffage_kw, interpoler_cop

        mois_ordre = ('Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                       'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre')
        plages = ('8h-13h', '13h-18h', '18h-20h', '20h-23h', '23h-8h')

        rows = []
        for mois in mois_ordre:
            t_ext = heating_config.temperatures_exterieures.get(mois, 10.0)
            cop = interpoler_cop(t_ext, heating_config.cop_par_temperature) if heating_config.avec_pompe_a_chaleur else 1.0
            for plage in plages:
                besoin_kw = besoin_national_chauffage_kw(heating_config, mois, plage)
                rows.append((mois, plage, t_ext, cop, besoin_kw))

        self.conn.executemany(
            "INSERT OR REPLACE INTO consommation_chauffage (mois, plage, temperature_ext, cop, besoin_electrique_kw) VALUES (?, ?, ?, ?, ?)",
            rows
        )
        self.conn.commit()

    def load_heating_data(self):
        """Load heating data as list of dicts."""
        cursor = self.conn.execute(
            "SELECT mois, plage, temperature_ext, cop, besoin_electrique_kw FROM consommation_chauffage ORDER BY rowid"
        )
        return [dict(row) for row in cursor.fetchall()]

    def store_sector_data(self, transport_config=None, industrie_config=None, tertiaire_config=None, agriculture_config=None):
        """Compute and store per-slot sector consumption data.

        Uses existing model functions to compute annual TWh, then distributes
        across 60 time slots.

        Transport: uses demande_recharge_par_plage() from src.transport
        Industry/Tertiary: bilan_industrie(), bilan_tertiaire() from src.secteurs - distributed flat across all slots
        Agriculture: consommation_mensuelle_twh() from src.agriculture - distributed by monthly profile
        """
        from src.transport import demande_recharge_par_plage, TransportConfig, consommation_electrifiee_twh as transport_elec
        from src.secteurs import bilan_industrie, bilan_tertiaire, IndustrieConfig, TertiaireConfig
        from src.agriculture import consommation_mensuelle_twh, AgricultureConfig

        if transport_config is None:
            transport_config = TransportConfig()
        if industrie_config is None:
            industrie_config = IndustrieConfig()
        if tertiaire_config is None:
            tertiaire_config = TertiaireConfig()
        if agriculture_config is None:
            agriculture_config = AgricultureConfig()

        mois_ordre = ('Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                       'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre')
        plages = ('8h-13h', '13h-18h', '18h-20h', '20h-23h', '23h-8h')
        durees = {'8h-13h': 5.0, '13h-18h': 5.0, '18h-20h': 2.0, '20h-23h': 3.0, '23h-8h': 9.0}
        jours_par_mois = 30

        # Industry and tertiary: annual TWh distributed flat
        ind = bilan_industrie(industrie_config)
        ter = bilan_tertiaire(tertiaire_config)

        # Convert annual TWh to constant kW: TWh * 1e9 / (8760 hours)
        # Note: flat distribution is a simplification (no seasonality)
        industrie_kw_flat = ind['total_elec_twh'] * 1e9 / 8760
        tertiaire_kw_flat = ter['total_elec_twh'] * 1e9 / 8760

        # Transport: rail + SAF electricity (not in charging profile, distributed flat)
        electrifie = transport_elec(transport_config)
        rail_saf_kw = (electrifie['rail_elec_twh'] + electrifie['aviation_elec_saf_twh']) * 1e9 / 8760

        rows = []
        for mois in mois_ordre:
            # Agriculture: monthly TWh distributed evenly across 5 slots
            agri_monthly_twh = consommation_mensuelle_twh(mois, agriculture_config)

            for plage in plages:
                duree = durees[plage]

                # Transport kW: charging profile + flat rail/SAF
                transport_slot_twh = demande_recharge_par_plage(plage, transport_config)
                # annual TWh for this slot -> kW power during that slot
                # Slot happens every day: kW = TWh * 1e9 / (duree_h * 365)
                transport_kw = transport_slot_twh * 1e9 / (duree * 365) + rail_saf_kw

                # Agriculture: distribute monthly TWh across 5 slots proportional to duration
                agri_slot_twh = agri_monthly_twh * duree / 24.0
                agri_kw = agri_slot_twh * 1e9 / (duree * jours_par_mois)

                rows.append((mois, plage, transport_kw, industrie_kw_flat, tertiaire_kw_flat, agri_kw))

        self.conn.executemany(
            "INSERT OR REPLACE INTO consommation_sectors (mois, plage, transport_kw, industrie_kw, tertiaire_kw, agriculture_kw) VALUES (?, ?, ?, ?, ?, ?)",
            rows
        )
        self.conn.commit()

    def load_sector_data(self):
        """Load sector data as list of dicts."""
        cursor = self.conn.execute(
            "SELECT mois, plage, transport_kw, industrie_kw, tertiaire_kw, agriculture_kw FROM consommation_sectors ORDER BY rowid"
        )
        return [dict(row) for row in cursor.fetchall()]

    def store_synthesis(self, rows):
        """Store 60-row synthesis. rows is list of tuples matching synthese_moulinette columns."""
        self.conn.executemany(
            """INSERT OR REPLACE INTO synthese_moulinette
            (mois, plage, pv_maisons_kw, pv_collectif_kw, pv_centrales_kw,
             hydraulique_kw, eolien_kw, nucleaire_kw, total_production_kw,
             chauffage_kw, transport_kw, industrie_kw, tertiaire_kw, agriculture_kw,
             total_conso_kw, deficit_gaz_kw, duree_h, energie_gaz_twh)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            rows
        )
        self.conn.commit()

    def load_synthesis(self):
        """Load synthesis as list of dicts."""
        cursor = self.conn.execute(
            "SELECT * FROM synthese_moulinette ORDER BY rowid"
        )
        return [dict(row) for row in cursor.fetchall()]

    def store_metadata(self, key, value):
        """Store a metadata key-value pair."""
        self.conn.execute(
            "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
            (key, str(value))
        )
        self.conn.commit()

    def load_metadata(self, key):
        """Load a metadata value by key."""
        cursor = self.conn.execute("SELECT value FROM metadata WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row['value'] if row else None
