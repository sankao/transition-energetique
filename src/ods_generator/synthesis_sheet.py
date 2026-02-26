"""Synthesis sheet generator — the core deliverable.

Every numeric cell is an ODF formula referencing source data sheets.
Pre-computed values from the DB are set alongside formulas so numbers
display immediately without recalculation.

Production columns reference parametres + facteurs_solaires + prod_nucleaire_hydraulique.
Consumption columns reference calc sheets (formula-based, traceable to parametres).

60 data rows (12 months x 5 time slots) plus monthly totals and annual total.
"""

from .writer import ODSWriter
from .knob_registry import get_param_ref


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
    'H2 électrolyse (kW)', # R
    'Total élec+H2 (kW)',  # S
]


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

    # Parameter references from knob registry
    ref_kwc_maison = get_param_ref('kwc_par_maison')
    ref_n_maisons = get_param_ref('nombre_maisons')
    ref_kwc_collectif = get_param_ref('kwc_par_collectif')
    ref_n_collectifs = get_param_ref('nombre_collectifs')
    ref_gwc_centrales = get_param_ref('solar_gwc_centrales')
    ref_jours = get_param_ref('jours_par_mois')

    # Data rows: title=row1, header=row2, data starts row3
    row_num = 3
    slot_index = 0  # 0-based index into 60 rows (for calc_chauffage reference)
    for mois_idx, mois in enumerate(MOIS_ORDRE):
        for plage_idx, plage in enumerate(PLAGES):
            key = (mois, plage)
            vals = lookup.get(key, {})
            duree = DUREES[plage]

            # Source sheet row: same ordering as synthesis
            r = row_num

            # Calc sheet row references:
            # calc_chauffage: 60 data rows, row 3-62, column H = besoin_electrique_kw
            chauffage_r = r  # Same row ordering
            # calc_transport: 5 slot rows (row 3-7), column B = transport_kw
            transport_slot_r = 3 + plage_idx  # Row per slot type
            # calc_industrie: single value at row 3, column B = flat_kw
            # calc_tertiaire: single value at row 3, column B = flat_kw
            # calc_agriculture: 12 monthly rows (row 3-14), column B = kw
            agriculture_month_r = 3 + mois_idx

            cells = [
                # A: Period label (static)
                {'value': f"{mois} {plage}"},

                # B: PV maisons (kW) = kwc_par_maison * nombre_maisons * capacity_factor
                {
                    'value': vals.get('pv_maisons_kw', 0.0),
                    'formula': (
                        f"of:={ref_kwc_maison}"
                        f"*{ref_n_maisons}"
                        f"*[facteurs_solaires.C{r}]"
                    ),
                },

                # C: PV collectif (kW) = kwc_par_collectif * nombre_collectifs * capacity_factor
                {
                    'value': vals.get('pv_collectif_kw', 0.0),
                    'formula': (
                        f"of:={ref_kwc_collectif}"
                        f"*{ref_n_collectifs}"
                        f"*[facteurs_solaires.C{r}]"
                    ),
                },

                # D: PV centrales (kW) = GWc * 1e6 * capacity_factor
                {
                    'value': vals.get('pv_centrales_kw', 0.0),
                    'formula': (
                        f"of:={ref_gwc_centrales}"
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

                # I: Chauffage (kW) — from calc_chauffage sheet
                {
                    'value': vals.get('chauffage_kw', 0.0),
                    'formula': f"of:=[calc_chauffage.H{chauffage_r}]",
                },

                # J: Transport (kW) — from calc_transport sheet
                {
                    'value': vals.get('transport_kw', 0.0),
                    'formula': f"of:=[calc_transport.B{transport_slot_r}]",
                },

                # K: Industrie (kW) — flat value from calc_industrie
                {
                    'value': vals.get('industrie_kw', 0.0),
                    'formula': f"of:=[calc_industrie.B3]",
                },

                # L: Tertiaire (kW) — flat value from calc_tertiaire
                {
                    'value': vals.get('tertiaire_kw', 0.0),
                    'formula': f"of:=[calc_tertiaire.B3]",
                },

                # M: Agriculture (kW) — monthly value from calc_agriculture
                {
                    'value': vals.get('agriculture_kw', 0.0),
                    'formula': f"of:=[calc_agriculture.B{agriculture_month_r}]",
                },

                # N: Total conso = I+J+K+L+M
                {
                    'value': vals.get('total_conso_kw', 0.0),
                    'formula': f"of:=[.I{r}]+[.J{r}]+[.K{r}]+[.L{r}]+[.M{r}]",
                },

                # O: Déficit gaz = MAX(0, total_elec_h2 - prod)
                {
                    'value': vals.get('deficit_gaz_kw', 0.0),
                    'formula': f"of:=MAX(0;[.N{r}]+[.R{r}]-[.H{r}])",
                },

                # P: Durée (h) - static
                {'value': duree},

                # Q: Énergie gaz (TWh) = deficit * durée * jours_par_mois / 1e9
                {
                    'value': vals.get('energie_gaz_twh', 0.0),
                    'formula': (
                        f"of:=[.O{r}]*[.P{r}]"
                        f"*{ref_jours}"
                        f"/1000000000"
                    ),
                },

                # R: H2 électrolyse (kW) — flat value from balance
                {
                    'value': vals.get('h2_electrolyse_kw', 0.0),
                },

                # S: Total élec+H2 = N + R
                {
                    'value': (vals.get('total_conso_kw', 0.0)
                              + vals.get('h2_electrolyse_kw', 0.0)),
                    'formula': f"of:=[.N{r}]+[.R{r}]",
                },
            ]

            writer.add_formula_row(table, cells)
            row_num += 1
            slot_index += 1

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

        # R, S: empty for monthly totals
        cells.append({'value': ''})
        cells.append({'value': ''})

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

    # R, S: empty for annual total
    cells.append({'value': ''})
    cells.append({'value': ''})

    writer.add_formula_row(table, cells)
