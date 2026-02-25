"""Balance sheet generator --- electrification system balance.

Shows sector-by-sector conversion from current consumption to electrified target.
Values are Python-computed via consumption.py, stored in DB.
"""

from .writer import ODSWriter


def add_balance_sheet(writer: ODSWriter, db):
    """Generate the bilan_electrification sheet with pre-computed values."""
    data = db.load_balance()
    if not data:
        raise ValueError("No balance data in DB. Run pipeline first.")

    rows = [(d['sector'], d['current_twh'], d['elec_twh'], d['h2_twh'],
             d['bio_enr_twh'], d['fossil_residual_twh'],
             d['total_target_twh'], d['h2_production_elec_twh'])
            for d in data]

    writer.add_data_sheet(
        'bilan_electrification',
        ['Secteur', 'Actuel (TWh)', 'Elec direct (TWh)', 'H2 (TWh)',
         'Bio/EnR (TWh)', 'Fossile residuel (TWh)', 'Total cible (TWh)',
         'H2 prod elec (TWh)'],
        rows,
        title='Bilan electrification --- scenario recalibre v0.8',
    )
