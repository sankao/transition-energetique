"""Tests for ElectrificationParams knobs in ODS knob registry."""

from dataclasses import fields

from src.consumption import ElectrificationParams
from src.ods_generator.knob_registry import (
    CategoryEntry,
    KnobEntry,
    PARAM_ROWS,
    REGISTRY,
    build_parametres_rows_from_configs,
    get_param_ref,
)


def test_84_electrification_knobs_registered():
    """All 84 ElectrificationParams fields have a KnobEntry."""
    knobs = [
        e for e in REGISTRY
        if isinstance(e, KnobEntry) and e.config_class == 'ElectrificationParams'
    ]
    assert len(knobs) == 84, f"Expected 84 knobs, got {len(knobs)}"


def test_no_duplicate_names_in_registry():
    """Every KnobEntry name must be unique across the entire REGISTRY."""
    names = [e.name for e in REGISTRY if isinstance(e, KnobEntry)]
    duplicates = [n for n in names if names.count(n) > 1]
    assert len(duplicates) == 0, f"Duplicate knob names: {set(duplicates)}"


def test_get_param_ref_for_electrification_knob():
    """get_param_ref('res_chauffage_cop') returns a valid ODS reference."""
    ref = get_param_ref('res_chauffage_cop')
    assert ref.startswith('[parametres.B')
    assert ref.endswith(']')
    # Row number must be >= 3 (data starts at row 3)
    row = int(ref.replace('[parametres.B', '').replace(']', ''))
    assert row >= 3


def test_build_parametres_rows_with_electrification_params():
    """build_parametres_rows_from_configs with ElectrificationParams returns correct values."""
    params = ElectrificationParams()
    rows = build_parametres_rows_from_configs(electrification_params=params)
    # Should have rows for the full registry
    assert len(rows) == len(REGISTRY)

    # Build a lookup: name -> value
    row_dict = {r[0]: r[1] for r in rows if r[1] != ''}

    # Spot-check a few known defaults
    assert row_dict['res_chauffage_cop'] == 3.5
    assert row_dict['res_ecs_cop'] == 3.0
    assert row_dict['tpt_vp_ev_factor'] == 0.33
    assert row_dict['electrolyse_efficiency'] == 0.65
    assert row_dict['ccgt_efficiency'] == 0.55
    assert row_dict['ne_engrais_h2_twh'] == 16.0
    assert row_dict['agr_serres_cop'] == 3.0

    # Check that modified params flow through
    custom = ElectrificationParams(res_chauffage_cop=4.0, ccgt_efficiency=0.60)
    rows2 = build_parametres_rows_from_configs(electrification_params=custom)
    row_dict2 = {r[0]: r[1] for r in rows2 if r[1] != ''}
    assert row_dict2['res_chauffage_cop'] == 4.0
    assert row_dict2['ccgt_efficiency'] == 0.60


def test_param_rows_has_all_84_electrification_names():
    """PARAM_ROWS mapping contains entries for all 84 ElectrificationParams fields."""
    ep_fields = {f.name for f in fields(ElectrificationParams)}
    missing = ep_fields - set(PARAM_ROWS.keys())
    assert len(missing) == 0, f"Missing from PARAM_ROWS: {missing}"


def test_knob_field_names_match_dataclass_fields():
    """Every ElectrificationParams KnobEntry.field_name matches an actual dataclass field."""
    ep_fields = {f.name for f in fields(ElectrificationParams)}
    knobs = [
        e for e in REGISTRY
        if isinstance(e, KnobEntry) and e.config_class == 'ElectrificationParams'
    ]
    for knob in knobs:
        assert knob.field_name in ep_fields, (
            f"KnobEntry field_name={knob.field_name!r} not found in ElectrificationParams"
        )


def test_knob_defaults_match_dataclass_defaults():
    """Every ElectrificationParams KnobEntry.default_value matches the dataclass default."""
    ep_defaults = {f.name: f.default for f in fields(ElectrificationParams)}
    knobs = [
        e for e in REGISTRY
        if isinstance(e, KnobEntry) and e.config_class == 'ElectrificationParams'
    ]
    for knob in knobs:
        expected = ep_defaults[knob.field_name]
        assert knob.default_value == expected, (
            f"{knob.name}: default_value={knob.default_value}, "
            f"expected {expected} from ElectrificationParams"
        )


def test_seven_electrification_categories_exist():
    """There should be 7 CategoryEntry items for Electrification sectors."""
    cats = [
        e for e in REGISTRY
        if isinstance(e, CategoryEntry)
        and e.label.startswith('Electrification')
    ]
    assert len(cats) == 7, f"Expected 7 categories, got {len(cats)}: {[c.label for c in cats]}"


def test_store_and_load_balance_roundtrip():
    """Store SystemBalance in DB, load back, verify 7 rows."""
    from src.consumption import calculate_system_balance
    from src.database.store import EnergyModelDB
    balance = calculate_system_balance()
    with EnergyModelDB(":memory:") as db:
        db.store_balance(balance)
        data = db.load_balance()
    assert len(data) == 7  # 6 sectors + TOTAL
    total_row = [d for d in data if d['sector'] == 'TOTAL'][0]
    assert abs(total_row['elec_twh'] - balance.direct_electricity_twh) < 0.1
    assert abs(total_row['h2_production_elec_twh'] - balance.h2_production_elec_twh) < 0.1


def test_balance_total_elec_approximately_595():
    """TOTAL row elec_twh should be ~595 TWh."""
    from src.consumption import calculate_system_balance
    from src.database.store import EnergyModelDB
    balance = calculate_system_balance()
    with EnergyModelDB(":memory:") as db:
        db.store_balance(balance)
        data = db.load_balance()
    total_row = [d for d in data if d['sector'] == 'TOTAL'][0]
    assert abs(total_row['elec_twh'] - 595) < 10


def test_balance_h2_production_approximately_134():
    """TOTAL row h2_production_elec_twh should be ~134 TWh."""
    from src.consumption import calculate_system_balance
    from src.database.store import EnergyModelDB
    balance = calculate_system_balance()
    with EnergyModelDB(":memory:") as db:
        db.store_balance(balance)
        data = db.load_balance()
    total_row = [d for d in data if d['sector'] == 'TOTAL'][0]
    assert abs(total_row['h2_production_elec_twh'] - 134) < 10


def test_store_parameters_includes_electrification_knobs():
    """store_parameters with electrification_params stores all 226 knobs."""
    from src.config import EnergyModelConfig
    from src.consumption import ElectrificationParams
    from src.database.store import EnergyModelDB
    config = EnergyModelConfig()
    ep = ElectrificationParams()
    with EnergyModelDB(":memory:") as db:
        db.store_parameters(config, electrification_params=ep)
        cursor = db.conn.execute("SELECT COUNT(*) FROM parametres")
        count = cursor.fetchone()[0]
    # Should have 226 knob rows (142 old + 84 new)
    assert count == 226


def test_compute_consumption_stores_balance():
    """compute_consumption() with electrification_params stores balance in DB."""
    from src.config import EnergyModelConfig
    from src.consumption import ElectrificationParams
    from src.database.store import EnergyModelDB
    from src.heating import HeatingConfig
    from src.transport import TransportConfig
    from src.secteurs import IndustrieConfig, TertiaireConfig
    from src.agriculture import AgricultureConfig
    from main import compute_consumption

    config = EnergyModelConfig()
    ep = ElectrificationParams()
    with EnergyModelDB(":memory:") as db:
        compute_consumption(
            db, config,
            heating_config=HeatingConfig(),
            transport_config=TransportConfig(),
            industrie_config=IndustrieConfig(),
            tertiaire_config=TertiaireConfig(),
            agriculture_config=AgricultureConfig(),
            electrification_params=ep,
        )
        data = db.load_balance()
    assert len(data) == 7  # 6 sectors + TOTAL
    total_row = [d for d in data if d['sector'] == 'TOTAL'][0]
    assert abs(total_row['elec_twh'] - 595) < 10


# --- H2 electrolyse column tests (Task 6) ---


def test_synthesis_schema_has_h2_column():
    """synthese_moulinette table DDL contains h2_electrolyse_kw column."""
    from src.database.schema import TABLES
    assert 'h2_electrolyse_kw' in TABLES['synthese_moulinette']


def test_synthesis_store_accepts_19_columns():
    """store_synthesis() accepts 19-element tuples with h2_electrolyse_kw."""
    from src.database.store import EnergyModelDB
    with EnergyModelDB(":memory:") as db:
        row = (
            'Janvier', '8h-13h',
            1.0, 2.0, 3.0,       # pv_maisons, pv_collectif, pv_centrales
            4.0, 0.0, 5.0, 15.0, # hydraulique, eolien, nucleaire, total_prod
            6.0, 7.0, 8.0, 9.0, 10.0,  # chauffage..agriculture
            40.0, 25.0, 5.0, 0.5,  # total_conso, deficit, duree, energie_gaz
            99.0,                 # h2_electrolyse_kw (19th column)
        )
        db.store_synthesis([row])
        data = db.load_synthesis()
    assert len(data) == 1
    assert data[0]['h2_electrolyse_kw'] == 99.0


def test_synthesis_h2_electrolyse_kw_value():
    """H2 electrolyse kW from balance should be ~15.3 million kW (134 TWh / 8760h)."""
    from src.consumption import calculate_system_balance
    balance = calculate_system_balance()
    expected_kw = balance.h2_production_elec_twh * 1e9 / 8760
    # Should be about 15.3 million kW (134 TWh flat)
    assert abs(expected_kw - 15.3e6) < 1e6


def test_synthesis_headers_include_h2_columns():
    """HEADERS list includes H2 and Total elec+H2 columns at positions R and S."""
    from src.ods_generator.synthesis_sheet import HEADERS
    assert 'H2 électrolyse (kW)' in HEADERS
    assert 'Total élec+H2 (kW)' in HEADERS
    # R is index 17, S is index 18 (0-based)
    assert HEADERS[17] == 'H2 électrolyse (kW)'
    assert HEADERS[18] == 'Total élec+H2 (kW)'


def test_synthesis_deficit_includes_h2():
    """Deficit calculation in compute_synthesis includes H2 electrolyse demand."""
    from src.config import EnergyModelConfig
    from src.consumption import ElectrificationParams
    from src.database.store import EnergyModelDB
    from src.heating import HeatingConfig
    from src.transport import TransportConfig
    from src.secteurs import IndustrieConfig, TertiaireConfig
    from src.agriculture import AgricultureConfig
    from main import compute_consumption, compute_synthesis

    config = EnergyModelConfig()
    ep = ElectrificationParams()
    with EnergyModelDB(":memory:") as db:
        compute_consumption(
            db, config,
            heating_config=HeatingConfig(),
            transport_config=TransportConfig(),
            industrie_config=IndustrieConfig(),
            tertiaire_config=TertiaireConfig(),
            agriculture_config=AgricultureConfig(),
            electrification_params=ep,
        )
        # We need production data too — use dummy data for all 60 slots
        mois_ordre = (
            'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
            'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
        )
        plages = ('8h-13h', '13h-18h', '18h-20h', '20h-23h', '23h-8h')
        rte_rows = []
        pvgis_rows = []
        for mois in mois_ordre:
            for plage in plages:
                rte_rows.append((mois, plage, 40000.0, 8000.0))  # 40 GW nuc, 8 GW hydro
                pvgis_rows.append((mois, plage, 0.15))  # 15% capacity factor
        db.store_rte_production(rte_rows)
        db.store_pvgis_factors(pvgis_rows)

        compute_synthesis(db, config)
        data = db.load_synthesis()

    assert len(data) == 60
    # Every row should have h2_electrolyse_kw > 0
    for row in data:
        assert row['h2_electrolyse_kw'] > 0
    # All rows should have the same h2_electrolyse_kw (flat distribution)
    h2_values = [row['h2_electrolyse_kw'] for row in data]
    assert max(h2_values) == min(h2_values), "H2 electrolyse should be flat across all slots"
    # Value should be ~15.3M kW
    assert abs(h2_values[0] - 15.3e6) < 1e6
