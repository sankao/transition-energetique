"""ODS source sheet generators.

Each function adds a data sheet with consistent 60-row layout
(12 months x 5 time slots) that the synthesis sheet references.

Row 1 = header, rows 2-61 = data (Jan 8h-13h through Dec 23h-8h).
"""

from .writer import ODSWriter


MOIS_ORDRE = (
    'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
    'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
)
PLAGES = ('8h-13h', '13h-18h', '18h-20h', '20h-23h', '23h-8h')


def add_parametres_sheet(writer: ODSWriter, db):
    """Add parameters sheet with model configuration values.

    Key rows referenced by synthesis formulas:
    B2: solar_gwc_maisons, B3: solar_gwc_collectif, B4: solar_gwc_centrales, etc.
    """
    cursor = db.conn.execute(
        "SELECT name, value, unit, source, description FROM parametres ORDER BY rowid"
    )
    rows = [(r['name'], r['value'], r['unit'], r['source'], r['description'])
            for r in cursor.fetchall()]

    writer.add_data_sheet(
        'parametres',
        ['Paramètre', 'Valeur', 'Unité', 'Source', 'Description'],
        rows,
        title='Paramètres du modèle',
    )


def add_prod_nucleaire_hydraulique_sheet(writer: ODSWriter, db):
    """Add nuclear/hydraulic production sheet (60 rows from RTE data)."""
    data = db.load_rte_production()
    rows = [(d['mois'], d['plage'], d['nucleaire_mw'], d['hydraulique_mw'])
            for d in data]

    writer.add_data_sheet(
        'prod_nucleaire_hydraulique',
        ['Mois', 'Plage', 'Nucléaire (MW)', 'Hydraulique (MW)'],
        rows,
        title='Production nucléaire et hydraulique (RTE eco2mix)',
    )


def add_facteurs_solaires_sheet(writer: ODSWriter, db):
    """Add PVGIS solar capacity factors sheet (60 rows)."""
    data = db.load_pvgis_factors()
    rows = [(d['mois'], d['plage'], d['capacity_factor'])
            for d in data]

    writer.add_data_sheet(
        'facteurs_solaires',
        ['Mois', 'Plage', 'Facteur de capacité'],
        rows,
        title='Facteurs solaires PVGIS (moyenne pondérée France)',
    )


def add_consommation_chauffage_sheet(writer: ODSWriter, db):
    """Add heating consumption sheet (60 rows)."""
    data = db.load_heating_data()
    rows = [(d['mois'], d['plage'], d['temperature_ext'], d['cop'],
             d['besoin_electrique_kw'])
            for d in data]

    writer.add_data_sheet(
        'consommation_chauffage',
        ['Mois', 'Plage', 'T_ext (°C)', 'COP', 'Besoin électrique (kW)'],
        rows,
        title='Consommation chauffage (modèle Roland, COP variable)',
    )


def add_consommation_sectors_sheet(writer: ODSWriter, db):
    """Add sector consumption sheet (60 rows)."""
    data = db.load_sector_data()
    rows = [(d['mois'], d['plage'], d['transport_kw'], d['industrie_kw'],
             d['tertiaire_kw'], d['agriculture_kw'])
            for d in data]

    writer.add_data_sheet(
        'consommation_sectors',
        ['Mois', 'Plage', 'Transport (kW)', 'Industrie (kW)',
         'Tertiaire (kW)', 'Agriculture (kW)'],
        rows,
        title='Consommation par secteur',
    )


def add_all_source_sheets(writer: ODSWriter, db):
    """Add all source data sheets in order."""
    add_parametres_sheet(writer, db)
    add_prod_nucleaire_hydraulique_sheet(writer, db)
    add_facteurs_solaires_sheet(writer, db)
    add_consommation_chauffage_sheet(writer, db)
    add_consommation_sectors_sheet(writer, db)
