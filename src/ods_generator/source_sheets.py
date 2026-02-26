"""ODS source sheet generators.

Each function adds a data sheet with consistent 60-row layout
(12 months x 5 time slots) that the synthesis sheet references.

Row 1 = title, Row 2 = header, rows 3+ = data.
"""

from .balance_sheet import add_balance_sheet
from .writer import ODSWriter
from .knob_registry import (
    REGISTRY, KnobEntry, CategoryEntry,
    build_parametres_rows_from_configs,
)


MOIS_ORDRE = (
    'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
    'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
)
PLAGES = ('8h-13h', '13h-18h', '18h-20h', '20h-23h', '23h-8h')


def add_parametres_sheet(writer: ODSWriter, db,
                         config=None, heating_config=None,
                         transport_config=None, industrie_config=None,
                         tertiaire_config=None, agriculture_config=None,
                         electrification_params=None):
    """Add parameters sheet with all 226 knobs organized by category.

    Uses knob_registry as single source of truth. Category rows get
    a special style. If config objects are provided, values come from
    live configs; otherwise from registry defaults.
    """
    rows = build_parametres_rows_from_configs(
        config=config,
        heating_config=heating_config,
        transport_config=transport_config,
        industrie_config=industrie_config,
        tertiaire_config=tertiaire_config,
        agriculture_config=agriculture_config,
        electrification_params=electrification_params,
    )

    # Use add_formula_sheet so we can mix category-styled and normal rows
    table = writer.add_formula_sheet(
        'parametres',
        ['Paramètre', 'Valeur', 'Unité', 'Source', 'Description'],
        title='Paramètres du modèle',
    )

    for i, entry in enumerate(REGISTRY):
        row = rows[i]
        if isinstance(entry, CategoryEntry):
            # Category header row — styled differently
            cells = [
                {'value': row[0], 'style': 'category'},
                {'value': '', 'style': 'category'},
                {'value': '', 'style': 'category'},
                {'value': '', 'style': 'category'},
                {'value': '', 'style': 'category'},
            ]
        else:
            cells = [
                {'value': row[0]},           # name
                {'value': row[1]},            # value (editable knob)
                {'value': row[2]},            # unit
                {'value': row[3]},            # source
                {'value': row[4]},            # description
            ]
        writer.add_formula_row(table, cells)


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
    """Add heating consumption sheet (60 rows) — static pre-computed values."""
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
    """Add sector consumption sheet (60 rows) — static pre-computed values."""
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


def add_all_source_sheets(writer: ODSWriter, db,
                          config=None, heating_config=None,
                          transport_config=None, industrie_config=None,
                          tertiaire_config=None, agriculture_config=None,
                          electrification_params=None):
    """Add all source data sheets in order."""
    add_parametres_sheet(
        writer, db,
        config=config,
        heating_config=heating_config,
        transport_config=transport_config,
        industrie_config=industrie_config,
        tertiaire_config=tertiaire_config,
        agriculture_config=agriculture_config,
        electrification_params=electrification_params,
    )
    add_prod_nucleaire_hydraulique_sheet(writer, db)
    add_facteurs_solaires_sheet(writer, db)
    # Static consumption sheets (kept for reference / auditability)
    add_consommation_chauffage_sheet(writer, db)
    add_consommation_sectors_sheet(writer, db)
    # Electrification balance sheet (sector-by-sector TWh breakdown)
    add_balance_sheet(writer, db)

    # Formula-based calc sheets
    from .calc_sheets import (
        add_calc_industrie_sheet,
        add_calc_tertiaire_sheet,
        add_calc_transport_sheet,
        add_calc_agriculture_sheet,
        add_calc_chauffage_sheet,
    )
    add_calc_industrie_sheet(writer, db, industrie_config)
    add_calc_tertiaire_sheet(writer, db, tertiaire_config)
    add_calc_transport_sheet(writer, db, transport_config)
    add_calc_agriculture_sheet(writer, db, agriculture_config)
    add_calc_chauffage_sheet(writer, db, heating_config)
