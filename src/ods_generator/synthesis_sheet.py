"""Synthesis sheet generator — the core deliverable.

Every numeric cell is an ODF formula referencing source data sheets.
Pre-computed values from the DB are set alongside formulas so numbers
display immediately without recalculation.

60 data rows (12 months x 5 time slots) plus monthly totals and annual total.
"""

from .writer import ODSWriter


MOIS_ORDRE = (
    'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
    'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
)
PLAGES = ('8h-13h', '13h-18h', '18h-20h', '20h-23h', '23h-8h')
DUREES = {'8h-13h': 5.0, '13h-18h': 5.0, '18h-20h': 2.0, '20h-23h': 3.0, '23h-8h': 9.0}

HEADERS = [
    'Période',             # A
    'PV maisons (kW)',     # B
    'PV collectif (kW)',   # C
    'PV centrales (kW)',   # D
    'Hydraulique (kW)',    # E
    'Éolien (kW)',         # F
    'Nucléaire (kW)',      # G
    'Total prod (kW)',     # H
    'Chauffage (kW)',      # I
    'Transport (kW)',      # J
    'Industrie (kW)',      # K
    'Tertiaire (kW)',      # L
    'Agriculture (kW)',    # M
    'Total conso (kW)',    # N
    'Déficit gaz (kW)',    # O
    'Durée (h)',           # P
    'Énergie gaz (TWh)',   # Q
]


def _col_letter(idx):
    """Convert 0-based column index to ODS column letter (A-Z)."""
    return chr(65 + idx)


def add_synthesis_sheet(writer: ODSWriter, db):
    """Generate the synthesis sheet with cross-sheet formulas.

    Every numeric cell has:
    - An ODF formula (of:=...) referencing source sheets
    - A pre-computed office:value so it displays immediately
    """
    synthesis_data = db.load_synthesis()
    if not synthesis_data:
        raise ValueError("No synthesis data in DB. Run pipeline first.")

    table = writer.add_formula_sheet(
        'moulinette_simplifiee',
        HEADERS,
        title='Moulinette simplifiée avec PAC — formules traçables',
    )

    # Build lookup for pre-computed values
    lookup = {}
    for row in synthesis_data:
        lookup[(row['mois'], row['plage'])] = row

    # Load parameters for formula references
    # Row positions in parametres sheet (1-based, row 1 is header):
    # We need to find the row index for each parameter
    param_rows = {}
    cursor = db.conn.execute("SELECT rowid, name FROM parametres ORDER BY rowid")
    for r in cursor.fetchall():
        # In ODS: row 1 = title, row 2 = header, data starts at row 3
        param_rows[r['name']] = r['rowid'] + 2  # +2 for title+header

    # Data rows: title=row1, header=row2, data starts row3
    row_num = 3
    for mois in MOIS_ORDRE:
        for plage in PLAGES:
            key = (mois, plage)
            vals = lookup.get(key, {})
            duree = DUREES[plage]

            # Source sheet row: title=row1, header=row2, data starts row3
            # Data rows in source sheets are in same order, so same row_num
            r = row_num

            # Build formula cells
            # Col indices: B=kwc_par_maison, C=facteurs_solaires
            cells = [
                # A: Period label (static)
                {'value': f"{mois} {plage}"},

                # B: PV maisons (kW)
                # = kwc_par_maison * nombre_maisons * 1000 * capacity_factor
                {
                    'value': vals.get('pv_maisons_kw', 0.0),
                    'formula': (
                        f"of:=[parametres.B{param_rows.get('kwc_par_maison', 8)}]"
                        f"*[parametres.B{param_rows.get('nombre_maisons', 6)}]"
                        f"*1000"
                        f"*[facteurs_solaires.C{r}]"
                    ),
                },

                # C: PV collectif (kW)
                {
                    'value': vals.get('pv_collectif_kw', 0.0),
                    'formula': (
                        f"of:=[parametres.B{param_rows.get('kwc_par_collectif', 9)}]"
                        f"*[parametres.B{param_rows.get('nombre_collectifs', 7)}]"
                        f"*1000"
                        f"*[facteurs_solaires.C{r}]"
                    ),
                },

                # D: PV centrales (kW)
                {
                    'value': vals.get('pv_centrales_kw', 0.0),
                    'formula': (
                        f"of:=[parametres.B{param_rows.get('solar_gwc_centrales', 5)}]"
                        f"*1000000"
                        f"*[facteurs_solaires.C{r}]"
                    ),
                },

                # E: Hydraulique (kW) = MW * 1000
                {
                    'value': vals.get('hydraulique_kw', 0.0),
                    'formula': f"of:=[prod_nucleaire_hydraulique.D{r}]*1000",
                },

                # F: Éolien (kW) = 0
                {
                    'value': 0.0,
                    'formula': "of:=0",
                },

                # G: Nucléaire (kW) = MW * 1000
                {
                    'value': vals.get('nucleaire_kw', 0.0),
                    'formula': f"of:=[prod_nucleaire_hydraulique.C{r}]*1000",
                },

                # H: Total production = B+C+D+E+F+G
                {
                    'value': vals.get('total_production_kw', 0.0),
                    'formula': f"of:=[.B{r}]+[.C{r}]+[.D{r}]+[.E{r}]+[.F{r}]+[.G{r}]",
                },

                # I: Chauffage (kW)
                {
                    'value': vals.get('chauffage_kw', 0.0),
                    'formula': f"of:=[consommation_chauffage.E{r}]",
                },

                # J: Transport (kW)
                {
                    'value': vals.get('transport_kw', 0.0),
                    'formula': f"of:=[consommation_sectors.C{r}]",
                },

                # K: Industrie (kW)
                {
                    'value': vals.get('industrie_kw', 0.0),
                    'formula': f"of:=[consommation_sectors.D{r}]",
                },

                # L: Tertiaire (kW)
                {
                    'value': vals.get('tertiaire_kw', 0.0),
                    'formula': f"of:=[consommation_sectors.E{r}]",
                },

                # M: Agriculture (kW)
                {
                    'value': vals.get('agriculture_kw', 0.0),
                    'formula': f"of:=[consommation_sectors.F{r}]",
                },

                # N: Total conso = I+J+K+L+M
                {
                    'value': vals.get('total_conso_kw', 0.0),
                    'formula': f"of:=[.I{r}]+[.J{r}]+[.K{r}]+[.L{r}]+[.M{r}]",
                },

                # O: Déficit gaz = MAX(0, conso - prod)
                {
                    'value': vals.get('deficit_gaz_kw', 0.0),
                    'formula': f"of:=MAX(0;[.N{r}]-[.H{r}])",
                },

                # P: Durée (h) - static
                {'value': duree},

                # Q: Énergie gaz (TWh) = deficit * durée * jours_par_mois / 1e9
                {
                    'value': vals.get('energie_gaz_twh', 0.0),
                    'formula': (
                        f"of:=[.O{r}]*[.P{r}]"
                        f"*[parametres.B{param_rows.get('jours_par_mois', 11)}]"
                        f"/1000000000"
                    ),
                },
            ]

            writer.add_formula_row(table, cells)
            row_num += 1

    # Monthly totals
    row_num_after_data = row_num
    # Add blank separator
    writer.add_formula_row(table, [{'value': ''} for _ in HEADERS])
    row_num += 1

    # Monthly summary rows
    writer.add_formula_row(table, [
        {'value': 'TOTAUX MENSUELS', 'style': 'total'},
    ] + [{'value': ''} for _ in range(len(HEADERS) - 1)])
    row_num += 1

    for i, mois in enumerate(MOIS_ORDRE):
        first_row = 3 + i * 5  # First slot row for this month
        last_row = first_row + 4  # Last slot row for this month

        # Compute pre-computed monthly gas total
        monthly_gas = sum(
            lookup.get((mois, p), {}).get('energie_gaz_twh', 0.0)
            for p in PLAGES
        )

        cells = [
            {'value': mois, 'style': 'total'},
        ]
        # For columns B through P, leave empty
        for _ in range(15):
            cells.append({'value': ''})

        # Q: Monthly gas total = SUM of 5 rows
        cells.append({
            'value': monthly_gas,
            'formula': f"of:=SUM([.Q{first_row}:.Q{last_row}])",
            'style': 'total',
        })

        writer.add_formula_row(table, cells)
        row_num += 1

    # Annual grand total
    monthly_start = row_num_after_data + 2  # After blank + header
    monthly_end = monthly_start + 11

    total_gas = sum(
        v.get('energie_gaz_twh', 0.0) for v in lookup.values()
    )

    cells = [
        {'value': 'TOTAL ANNUEL', 'style': 'total'},
    ]
    for _ in range(15):
        cells.append({'value': ''})
    cells.append({
        'value': total_gas,
        'formula': f"of:=SUM([.Q{monthly_start}:.Q{monthly_end}])",
        'style': 'total',
    })
    writer.add_formula_row(table, cells)
