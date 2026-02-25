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
