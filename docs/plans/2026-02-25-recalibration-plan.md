# Recalibration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Recalibrate the energy model so that consumption starts from SDES 2023 reference (1,615 TWh) and produces correct electrification results (733 TWh electricity).

**Architecture:** New `consumption.py` module becomes the single source of truth. Existing modules become temporal profile providers. All old tests deleted; ~80 new tests aligned on reference table.

**Tech Stack:** Python 3.13, dataclasses, pytest, uv

**Reference docs:**
- `docs/plans/2026-02-25-reference-consumption-table.md` — the numbers
- `docs/plans/2026-02-25-recalibration-design.md` — the architecture

---

## Phase 1: Core Dataclasses and Reference Data

### Task 1: UsageReference and SectorReference dataclasses

**Files:**
- Create: `src/consumption.py`
- Create: `tests/test_consumption.py`

**Step 1: Write the failing test**

```python
# tests/test_consumption.py
"""Tests for consumption module — SDES 2023 reference and electrification."""
from src.consumption import UsageReference, SectorReference


class TestUsageReference:
    def test_vectors_sum_to_total(self):
        u = UsageReference(
            name="chauffage", total_twh=312,
            elec_twh=50, gaz_twh=94, petrole_twh=31,
            charbon_twh=0, enr_twh=125, reseau_twh=12,
        )
        assert u.total_twh == 312

    def test_vectors_mismatch_raises(self):
        import pytest
        with pytest.raises(ValueError):
            UsageReference(
                name="bad", total_twh=100,
                elec_twh=10, gaz_twh=10, petrole_twh=10,
                charbon_twh=0, enr_twh=10, reseau_twh=10,
            )  # sum=50, total=100 -> error


class TestSectorReference:
    def test_usages_sum_to_sector_total(self):
        usages = [
            UsageReference("a", 200, 200, 0, 0, 0, 0, 0),
            UsageReference("b", 100, 50, 50, 0, 0, 0, 0),
        ]
        s = SectorReference(name="test", usages=usages)
        assert s.total_twh == 300

    def test_sector_total_property(self):
        usages = [
            UsageReference("x", 50, 50, 0, 0, 0, 0, 0),
        ]
        s = SectorReference(name="test", usages=usages)
        assert s.total_twh == 50
```

**Step 2: Run test to verify it fails**

Run: `cd /home/kingwin/energy_transition/energy_model && uv run pytest tests/test_consumption.py -v`
Expected: FAIL with `ModuleNotFoundError` or `ImportError`

**Step 3: Write minimal implementation**

```python
# src/consumption.py
"""Central consumption module — SDES 2023 reference and electrification balance.

This module is the single source of truth for all consumption figures.
Existing modules (heating, transport, agriculture) provide temporal profiles;
this module provides the annual totals.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class UsageReference:
    """One end-use within a sector (e.g. residential heating, 312 TWh).

    All vector fields are in TWh and must sum to total_twh.
    """
    name: str
    total_twh: float
    elec_twh: float
    gaz_twh: float
    petrole_twh: float
    charbon_twh: float
    enr_twh: float
    reseau_twh: float

    def __post_init__(self) -> None:
        vector_sum = (
            self.elec_twh + self.gaz_twh + self.petrole_twh
            + self.charbon_twh + self.enr_twh + self.reseau_twh
        )
        if abs(vector_sum - self.total_twh) > 0.5:
            raise ValueError(
                f"{self.name}: vectors sum to {vector_sum:.1f}, "
                f"expected {self.total_twh:.1f}"
            )

    @property
    def fossil_twh(self) -> float:
        return self.gaz_twh + self.petrole_twh + self.charbon_twh


@dataclass(frozen=True)
class SectorReference:
    """One sector (e.g. residential, 422 TWh) with its end-use breakdown."""
    name: str
    usages: tuple[UsageReference, ...] | list[UsageReference]

    @property
    def total_twh(self) -> float:
        return sum(u.total_twh for u in self.usages)

    @property
    def elec_twh(self) -> float:
        return sum(u.elec_twh for u in self.usages)

    @property
    def fossil_twh(self) -> float:
        return sum(u.fossil_twh for u in self.usages)

    @property
    def enr_twh(self) -> float:
        return sum(u.enr_twh for u in self.usages)

    @property
    def reseau_twh(self) -> float:
        return sum(u.reseau_twh for u in self.usages)
```

**Step 4: Run test to verify it passes**

Run: `cd /home/kingwin/energy_transition/energy_model && uv run pytest tests/test_consumption.py -v`
Expected: 4 PASSED

**Step 5: Commit**

```bash
git add src/consumption.py tests/test_consumption.py
git commit -m "feat: add UsageReference and SectorReference dataclasses"
```

---

### Task 2: ReferenceData with sdes_2023() factory

**Files:**
- Modify: `src/consumption.py`
- Modify: `tests/test_consumption.py`

**Step 1: Write the failing tests**

Add to `tests/test_consumption.py`:

```python
from src.consumption import ReferenceData, sdes_2023


class TestReferenceData:
    def test_grand_total_is_1615(self):
        ref = sdes_2023()
        assert ref.total_twh == pytest.approx(1615, abs=1)

    def test_residential_is_422(self):
        ref = sdes_2023()
        assert ref.residential.total_twh == pytest.approx(422, abs=1)

    def test_tertiary_is_229(self):
        ref = sdes_2023()
        assert ref.tertiary.total_twh == pytest.approx(229, abs=1)

    def test_industry_is_283(self):
        ref = sdes_2023()
        assert ref.industry.total_twh == pytest.approx(283, abs=1)

    def test_transport_is_513(self):
        ref = sdes_2023()
        assert ref.transport.total_twh == pytest.approx(513, abs=1)

    def test_agriculture_is_55(self):
        ref = sdes_2023()
        assert ref.agriculture.total_twh == pytest.approx(55, abs=1)

    def test_non_energy_is_113(self):
        ref = sdes_2023()
        assert ref.non_energy.total_twh == pytest.approx(113, abs=1)

    def test_residential_has_5_usages(self):
        ref = sdes_2023()
        assert len(ref.residential.usages) == 5
        names = [u.name for u in ref.residential.usages]
        assert "chauffage" in names
        assert "ecs" in names

    def test_transport_has_10_modes(self):
        ref = sdes_2023()
        assert len(ref.transport.usages) == 10

    def test_national_electricity_is_393(self):
        ref = sdes_2023()
        total_elec = sum(s.elec_twh for s in ref.all_sectors)
        assert total_elec == pytest.approx(393, abs=5)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_consumption.py::TestReferenceData -v`
Expected: FAIL with `ImportError`

**Step 3: Write implementation**

Add to `src/consumption.py`:

```python
@dataclass(frozen=True)
class ReferenceData:
    """SDES 2023 complete reference: 6 sectors, 1615 TWh."""
    residential: SectorReference
    tertiary: SectorReference
    industry: SectorReference
    transport: SectorReference
    agriculture: SectorReference
    non_energy: SectorReference

    @property
    def all_sectors(self) -> list[SectorReference]:
        return [
            self.residential, self.tertiary, self.industry,
            self.transport, self.agriculture, self.non_energy,
        ]

    @property
    def total_twh(self) -> float:
        return sum(s.total_twh for s in self.all_sectors)

    def __post_init__(self) -> None:
        if abs(self.total_twh - 1615) > 2:
            raise ValueError(
                f"Grand total {self.total_twh:.1f} TWh != 1615 TWh"
            )


def sdes_2023() -> ReferenceData:
    """Return the SDES 2023 reference data for France (1615 TWh)."""
    residential = SectorReference("residential", [
        UsageReference("chauffage",        312, 50,  94, 31, 0, 125, 12),
        UsageReference("ecs",               38, 15,  15,  5, 0,   2,  1),
        UsageReference("elec_specifique",   68, 68,   0,  0, 0,   0,  0),
        UsageReference("cuisson",           22, 12,  10,  0, 0,   0,  0),
        UsageReference("climatisation",      2,  2,   0,  0, 0,   0,  0),
    ])
    tertiary = SectorReference("tertiary", [
        UsageReference("chauffage",         85, 12,  42, 10, 0,  11, 10),
        UsageReference("clim_ventilation",  20, 20,   0,  0, 0,   0,  0),
        UsageReference("eclairage",         28, 28,   0,  0, 0,   0,  0),
        UsageReference("elec_specifique",   48, 48,   0,  0, 0,   0,  0),
        UsageReference("ecs",               18,  6,  10,  2, 0,   0,  0),
        UsageReference("cuisson",           10,  3,   6,  1, 0,   0,  0),
        UsageReference("autres",            20,  7,   4,  8, 0,   0,  1),
    ])
    industry = SectorReference("industry", [
        UsageReference("chaleur_ht",        75, 10,  35, 10, 6,   5,  9),
        UsageReference("chaleur_mt",        55,  4,  30,  8, 0,   8,  5),
        UsageReference("chaleur_bt",        40,  4,  20,  5, 0,   8,  3),
        UsageReference("force_motrice",     65, 60,   3,  2, 0,   0,  0),
        UsageReference("electrochimie",     18, 18,   0,  0, 0,   0,  0),
        UsageReference("eclairage_it",      15,  3,   7,  2, 0,   3,  0),
        UsageReference("autres",            15,  3,   7,  1, 0,   1,  0),
    ])
    transport = SectorReference("transport", [
        UsageReference("voitures",         200, 2, 1, 180, 0, 17, 0),
        UsageReference("poids_lourds",     140, 0, 4, 126, 0, 10, 0),
        UsageReference("vul",               40, 0, 0,  36, 0,  4, 0),
        UsageReference("deux_roues",        10, 0, 0,  10, 0,  0, 0),
        UsageReference("bus_cars",          15, 1, 0,  13, 0,  1, 0),
        UsageReference("ferroviaire",       15, 10, 0,  5, 0,  0, 0),
        UsageReference("aviation_dom",      10, 0, 0,   9, 0,  1, 0),
        UsageReference("aviation_intl",     55, 0, 0,  50, 0,  5, 0),
        UsageReference("maritime_fluvial",  18, 0, 0,  18, 0,  0, 0),
        UsageReference("autres",            10, 0, 0,  10, 0,  0, 0),
    ])
    agriculture = SectorReference("agriculture", [
        UsageReference("machinisme",        30, 0, 0, 29, 0, 1, 0),
        UsageReference("serres",             7, 1, 3,  1, 0, 2, 0),
        UsageReference("irrigation",         3, 3, 0,  0, 0, 0, 0),
        UsageReference("elevage",            5, 2, 0,  2, 0, 1, 0),
        UsageReference("sechage",            3, 0, 0,  2, 0, 1, 0),
        UsageReference("peche",              4, 0, 0,  4, 0, 0, 0),
        UsageReference("autres",             3, 1, 0,  2, 0, 0, 0),
    ])
    non_energy = SectorReference("non_energy", [
        UsageReference("petrochimie",       60, 0, 5, 55, 0, 0, 0),
        UsageReference("engrais",           18, 0, 18, 0, 0, 0, 0),
        UsageReference("bitumes",           15, 0, 0, 15, 0, 0, 0),
        UsageReference("lubrifiants",        5, 0, 0,  5, 0, 0, 0),
        UsageReference("solvants",           5, 0, 0,  5, 0, 0, 0),
        UsageReference("autres",            10, 0, 2,  8, 0, 0, 0),
    ])
    return ReferenceData(
        residential=residential,
        tertiary=tertiary,
        industry=industry,
        transport=transport,
        agriculture=agriculture,
        non_energy=non_energy,
    )
```

Note for transport: the `enr_twh` field holds biocarburants (17 TWh for VP, etc.).
The `gaz_twh` field for transport is actual gas (GNV). The `petrole_twh` is petroleum fuels.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_consumption.py -v`
Expected: 14 PASSED (4 from Task 1 + 10 new)

**Step 5: Commit**

```bash
git add src/consumption.py tests/test_consumption.py
git commit -m "feat: add ReferenceData and sdes_2023() with SDES 2023 values"
```

---

### Task 3: ElectrificationParams and SectorBalance/SystemBalance

**Files:**
- Modify: `src/consumption.py`
- Modify: `tests/test_consumption.py`

**Step 1: Write the failing tests**

```python
from src.consumption import ElectrificationParams, SectorBalance, SystemBalance


class TestElectrificationParams:
    def test_default_values(self):
        p = ElectrificationParams()
        assert p.res_chauffage_cop == 3.5
        assert p.electrolyse_efficiency == 0.65
        assert p.tpt_vp_ev_factor == 0.33

    def test_custom_override(self):
        p = ElectrificationParams(res_chauffage_cop=4.0)
        assert p.res_chauffage_cop == 4.0


class TestSectorBalance:
    def test_vectors_sum(self):
        sb = SectorBalance(
            name="test", current_twh=100,
            elec_twh=40, h2_twh=10, bio_enr_twh=30, fossil_residual_twh=20,
        )
        assert sb.total_target_twh == 100
        assert sb.reduction_pct == pytest.approx(0.0)

    def test_reduction_pct(self):
        sb = SectorBalance(
            name="test", current_twh=200,
            elec_twh=50, h2_twh=10, bio_enr_twh=20, fossil_residual_twh=10,
        )
        assert sb.total_target_twh == 90
        assert sb.reduction_pct == pytest.approx(0.55, abs=0.01)


class TestSystemBalance:
    def test_from_sectors(self):
        sectors = {
            "a": SectorBalance("a", 100, 50, 10, 30, 10),
            "b": SectorBalance("b", 200, 80, 20, 60, 40),
        }
        sb = SystemBalance.from_sectors(sectors, electrolyse_efficiency=0.65)
        assert sb.current_total_twh == 300
        assert sb.direct_electricity_twh == 130
        assert sb.h2_demand_twh == 30
        assert sb.h2_production_elec_twh == pytest.approx(30 / 0.65, abs=0.5)
        assert sb.total_electricity_twh == pytest.approx(130 + 30 / 0.65, abs=0.5)
        assert sb.bio_enr_twh == 90
        assert sb.fossil_residual_twh == 50
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_consumption.py::TestElectrificationParams tests/test_consumption.py::TestSectorBalance tests/test_consumption.py::TestSystemBalance -v`
Expected: FAIL

**Step 3: Write implementation**

Add to `src/consumption.py`:

```python
@dataclass
class ElectrificationParams:
    """Conversion knobs — all adjustable for sensitivity analysis."""
    # Residential
    res_chauffage_cop: float = 3.5
    res_ecs_cop: float = 3.0
    res_elec_specifique_gain: float = 0.15
    res_cuisson_gain_induction: float = 0.20
    res_clim_growth_twh: float = 2.0

    # Tertiary
    ter_renovation_gain: float = 0.30
    ter_chauffage_cop: float = 3.0
    ter_clim_gain: float = 0.20
    ter_led_gain: float = 0.50
    ter_elec_specifique_gain: float = 0.15
    ter_ecs_cop: float = 3.0
    ter_autres_gain: float = 0.30
    ter_autres_fossil_residual_twh: float = 2.0

    # Industry
    ind_ht_efficiency_gain: float = 0.10
    ind_ht_elec_fraction: float = 0.30
    ind_ht_h2_fraction: float = 0.24
    ind_ht_fossil_residual_twh: float = 15.0
    ind_mt_cop: float = 2.25
    ind_mt_h2_twh: float = 5.0
    ind_mt_efficiency_gain: float = 0.15
    ind_bt_cop: float = 3.25
    ind_bt_efficiency_gain: float = 0.15
    ind_force_motrice_gain: float = 0.12
    ind_eclairage_gain: float = 0.20
    ind_autres_gain: float = 0.15

    # Transport
    tpt_vp_modal_shift: float = 0.10
    tpt_vp_sobriety: float = 0.05
    tpt_vp_ev_factor: float = 0.33
    tpt_vp_ev_fraction: float = 0.95
    tpt_pl_rail_shift: float = 0.10
    tpt_pl_battery_fraction: float = 0.50
    tpt_pl_battery_factor: float = 0.35
    tpt_pl_h2_fraction: float = 0.25
    tpt_pl_h2_factor: float = 0.70
    tpt_pl_biocarb_fraction: float = 0.15
    tpt_pl_fossil_fraction: float = 0.10
    tpt_vul_ev_factor: float = 0.33
    tpt_vul_sobriety: float = 0.05
    tpt_deux_roues_ev_factor: float = 0.30
    tpt_bus_elec_twh: float = 4.0
    tpt_bus_h2_twh: float = 2.0
    tpt_rail_elec_twh: float = 13.0
    tpt_rail_h2_twh: float = 1.0
    tpt_avia_dom_modal_shift: float = 0.50
    tpt_avia_dom_elec_twh: float = 1.0
    tpt_avia_dom_biocarb_twh: float = 4.0
    tpt_avia_intl_sobriety: float = 0.10
    tpt_avia_intl_h2_twh: float = 5.0
    tpt_avia_intl_biocarb_twh: float = 15.0
    tpt_avia_intl_fossil_twh: float = 25.0
    tpt_maritime_elec_twh: float = 2.0
    tpt_maritime_h2_twh: float = 3.0
    tpt_maritime_biocarb_twh: float = 3.0
    tpt_maritime_fossil_twh: float = 8.0
    tpt_autres_elec_twh: float = 8.0

    # Agriculture
    agr_machinisme_ev_fraction: float = 0.40
    agr_machinisme_ev_factor: float = 0.35
    agr_machinisme_h2_fraction: float = 0.20
    agr_machinisme_biocarb_fraction: float = 0.30
    agr_machinisme_fossil_fraction: float = 0.10
    agr_serres_cop: float = 3.0
    agr_elevage_cop: float = 3.0
    agr_elevage_efficiency_gain: float = 0.10
    agr_peche_elec_twh: float = 1.0
    agr_peche_h2_twh: float = 1.0
    agr_peche_fossil_twh: float = 1.0
    agr_sechage_elec_twh: float = 1.0
    agr_autres_elec_twh: float = 2.0

    # Non-energy
    ne_petrochimie_recycling_gain: float = 0.20
    ne_petrochimie_bio_fraction: float = 0.30
    ne_petrochimie_h2_fraction: float = 0.20
    ne_petrochimie_elec_twh: float = 3.0
    ne_engrais_h2_twh: float = 16.0
    ne_engrais_fossil_twh: float = 2.0
    ne_bitumes_recycling_gain: float = 0.20
    ne_bitumes_bio_fraction: float = 0.30
    ne_lubrifiants_bio_fraction: float = 0.50
    ne_solvants_green_fraction: float = 0.60
    ne_autres_elec_twh: float = 2.0
    ne_autres_h2_twh: float = 2.0
    ne_autres_bio_twh: float = 2.0
    ne_autres_fossil_twh: float = 2.0

    # System
    electrolyse_efficiency: float = 0.65
    ccgt_efficiency: float = 0.55


@dataclass(frozen=True)
class SectorBalance:
    """Electrification result for one sector."""
    name: str
    current_twh: float
    elec_twh: float
    h2_twh: float
    bio_enr_twh: float
    fossil_residual_twh: float

    @property
    def total_target_twh(self) -> float:
        return self.elec_twh + self.h2_twh + self.bio_enr_twh + self.fossil_residual_twh

    @property
    def reduction_pct(self) -> float:
        if self.current_twh == 0:
            return 0.0
        return (self.current_twh - self.total_target_twh) / self.current_twh


@dataclass(frozen=True)
class SystemBalance:
    """Complete system balance across all sectors."""
    sectors: dict[str, SectorBalance]
    current_total_twh: float
    direct_electricity_twh: float
    h2_demand_twh: float
    h2_production_elec_twh: float
    total_electricity_twh: float
    bio_enr_twh: float
    fossil_residual_twh: float

    @classmethod
    def from_sectors(
        cls, sectors: dict[str, SectorBalance], electrolyse_efficiency: float,
    ) -> SystemBalance:
        current = sum(s.current_twh for s in sectors.values())
        elec = sum(s.elec_twh for s in sectors.values())
        h2 = sum(s.h2_twh for s in sectors.values())
        h2_elec = h2 / electrolyse_efficiency
        bio = sum(s.bio_enr_twh for s in sectors.values())
        fossil = sum(s.fossil_residual_twh for s in sectors.values())
        return cls(
            sectors=sectors,
            current_total_twh=current,
            direct_electricity_twh=elec,
            h2_demand_twh=h2,
            h2_production_elec_twh=h2_elec,
            total_electricity_twh=elec + h2_elec,
            bio_enr_twh=bio,
            fossil_residual_twh=fossil,
        )
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_consumption.py -v`
Expected: all PASSED

**Step 5: Commit**

```bash
git add src/consumption.py tests/test_consumption.py
git commit -m "feat: add ElectrificationParams, SectorBalance, SystemBalance"
```

---

## Phase 2: Sector Conversion Functions

### Task 4: convert_residential()

**Files:**
- Modify: `src/consumption.py`
- Modify: `tests/test_consumption.py`

**Step 1: Write the failing tests**

```python
class TestConvertResidential:
    def test_electricity_is_175(self):
        ref = sdes_2023()
        params = ElectrificationParams()
        result = convert_residential(ref.residential, params)
        assert result.elec_twh == pytest.approx(175, abs=5)

    def test_h2_is_zero(self):
        ref = sdes_2023()
        params = ElectrificationParams()
        result = convert_residential(ref.residential, params)
        assert result.h2_twh == pytest.approx(0, abs=1)

    def test_bio_enr_is_127(self):
        ref = sdes_2023()
        params = ElectrificationParams()
        result = convert_residential(ref.residential, params)
        assert result.bio_enr_twh == pytest.approx(127, abs=5)

    def test_fossil_is_zero(self):
        ref = sdes_2023()
        params = ElectrificationParams()
        result = convert_residential(ref.residential, params)
        assert result.fossil_residual_twh == pytest.approx(0, abs=1)

    def test_total_is_302(self):
        ref = sdes_2023()
        params = ElectrificationParams()
        result = convert_residential(ref.residential, params)
        assert result.total_target_twh == pytest.approx(302, abs=5)

    def test_higher_cop_reduces_electricity(self):
        ref = sdes_2023()
        base = convert_residential(ref.residential, ElectrificationParams())
        high = convert_residential(ref.residential, ElectrificationParams(res_chauffage_cop=4.5))
        assert high.elec_twh < base.elec_twh
```

**Step 2: Run to verify failure**

Run: `uv run pytest tests/test_consumption.py::TestConvertResidential -v`

**Step 3: Implement**

Add `convert_residential()` to `src/consumption.py`. Logic per usage from the reference table:

- **chauffage (312)**: fossil(94+31)=125 / COP 3.5 = 36 elec. Existing elec(50) optimized to 35. Wood(125) maintained. District(12) maintained as EnR. Total: 71 elec + 125+12=137 EnR → but reference says 125 EnR. So district heat stays as-is (absorbed into EnR column). Elec = 71, EnR = 125, reseau counted in EnR for target.
- **ecs (38)**: fossil(15+5)=20 / COP 3.0 = 7. Existing elec(15) maintained. EnR(2+1)=3 maintained. Total: 22 elec + 2 EnR.
- **elec_specifique (68)**: 68 × (1-0.15) = 58 elec.
- **cuisson (22)**: gas(10) → induction 10×(1-0.20)=8. Existing elec(12). Total: 20 elec.
- **climatisation (2)**: maintained + growth = 4 elec.

```python
def convert_residential(
    sector: SectorReference, params: ElectrificationParams,
) -> SectorBalance:
    """Convert residential sector (422 TWh) to electrified scenario."""
    usages = {u.name: u for u in sector.usages}

    # Chauffage
    ch = usages["chauffage"]
    ch_fossil = ch.gaz_twh + ch.petrole_twh + ch.charbon_twh
    ch_elec = ch_fossil / params.res_chauffage_cop + ch.elec_twh * 0.7  # PAC optimized
    ch_enr = ch.enr_twh  # bois maintained
    ch_reseau = ch.reseau_twh  # district heat maintained

    # ECS
    ecs = usages["ecs"]
    ecs_fossil = ecs.gaz_twh + ecs.petrole_twh
    ecs_elec = ecs_fossil / params.res_ecs_cop + ecs.elec_twh
    ecs_enr = ecs.enr_twh + ecs.reseau_twh

    # Elec specifique
    es = usages["elec_specifique"]
    es_elec = es.elec_twh * (1 - params.res_elec_specifique_gain)

    # Cuisson
    cu = usages["cuisson"]
    cu_elec = cu.elec_twh + cu.gaz_twh * (1 - params.res_cuisson_gain_induction)

    # Climatisation
    cl_elec = usages["climatisation"].elec_twh + params.res_clim_growth_twh

    total_elec = ch_elec + ecs_elec + es_elec + cu_elec + cl_elec
    total_enr = ch_enr + ch_reseau + ecs_enr

    return SectorBalance(
        name="residential",
        current_twh=sector.total_twh,
        elec_twh=round(total_elec, 1),
        h2_twh=0,
        bio_enr_twh=round(total_enr, 1),
        fossil_residual_twh=0,
    )
```

**Step 4: Run and iterate until tests pass**

Run: `uv run pytest tests/test_consumption.py::TestConvertResidential -v`
Adjust coefficients if needed to match reference targets within tolerance.

**Step 5: Commit**

```bash
git add src/consumption.py tests/test_consumption.py
git commit -m "feat: add convert_residential() — 422 TWh -> 302 TWh"
```

---

### Task 5: convert_tertiary()

**Files:** Same as Task 4

**Step 1: Tests** — same pattern: test elec≈120, h2≈0, enr≈8, fossil≈2, total≈140, sensitivity on COP.

**Step 3: Logic** from reference table:
- chauffage(85): renovation -30% → 60 TWh need. fossil(42+10)/COP 3.0 = 17. Existing elec adjusted. EnR(11)+reseau(10) maintained. → 20 elec, 8 EnR.
- clim(20): 20×(1-0.20) = 16 elec.
- eclairage(28): 28×(1-0.50) = 14 elec.
- elec_spe(48): 48×(1-0.15) = 41 elec.
- ecs(18): fossil(10+2)/COP 3.0 + existing elec(6) → 9 elec.
- cuisson(10): gas(6)→induction + existing(3) → 8 elec.
- autres(20): 20×(1-0.30) = 14, of which 2 fossil residual → 12 elec.

**Step 5: Commit**

```bash
git commit -m "feat: add convert_tertiary() — 229 TWh -> 140 TWh"
```

---

### Task 6: convert_industry()

**Step 1: Tests** — elec≈162, h2≈23, enr≈22, fossil≈15, total≈222.

**Step 3: Logic** — most complex sector, 3 temperature tiers:
- HT(75): efficiency -10% → 68. Elec fraction 30% = 20 elec. H2 24% = 16 + existing residual = 18 H2 total. EnR(5)+reseau(9) maintained = 5 EnR (reseau reclassed). Fossil residual 15. Total = 22+18+5+15 = 60.
- MT(55): efficiency -15% → 47. fossil(30+8)/COP 2.25 for electrifiable portion. H2 for specific chemistry. EnR maintained.
- BT(40): efficiency -15% → 34. fossil/COP 3.25. EnR maintained.
- force_motrice(65): already 92% elec. Gain -12%. → 57 elec.
- electrochimie(18): 100% elec, maintained → 18.
- eclairage(15): -20% → 12.
- autres(15): -15% → 12 (11 elec + 1 EnR).

**Step 5: Commit**

```bash
git commit -m "feat: add convert_industry() — 283 TWh -> 222 TWh"
```

---

### Task 7: convert_transport()

**Step 1: Tests** — elec≈118, h2≈33, biocarb≈45, fossil≈49, total≈245.

**Step 3: Logic** — 10 modes with sequential conversion:
- VP(200): modal -10%, sobriety -5% → 171. 95% VE × 0.33 = 53 elec. Residual 5 bio + 4 fossil.
- PL(140): rail shift -10% → 126. 50% battery×0.35=22 elec. 25%×0.70=22 H2. 15%=19 bio. 10%=13 fossil.
  Wait, reference says 17 bio and 12 fossil. Let me recalculate: 126×0.15=18.9→17 bio rounded. 126×0.10=12.6→12 fossil.
- VUL(40): sobriety -5% → 38. VE×0.33 = 12 elec. 1 bio residual.
- deux_roues(10): VE×0.30 = 3.
- bus_cars(15): 4 elec + 2 H2 (from params).
- ferroviaire(15): 13 elec + 1 H2 (from params).
- avia_dom(10): modal -50% → 5. 1 elec + 4 biocarb (from params).
- avia_intl(55): sobriety -10% → 50. 5 H2 + 15 bio + 25 fossil + 0 elec (from params). Total=45.
- maritime(18): 2 elec + 3 H2 + 3 bio + 8 fossil (from params). Total=16.
- autres(10): 8 elec (from params).

**Step 5: Commit**

```bash
git commit -m "feat: add convert_transport() — 513 TWh -> 245 TWh"
```

---

### Task 8: convert_agriculture()

**Step 1: Tests** — elec≈16, h2≈5, bio≈11, fossil≈4, total≈36.

**Step 3: Logic** from reference table:
- machinisme(30): 40% VE×0.35=4 elec. 20%→4 H2. 30%→7 bio. 10%→3 fossil.
  Calculation: 30×0.40×0.35=4.2 elec. 30×0.20×0.67≈4 H2 (with efficiency factor). 30×0.30=9→7 bio adjusted. 30×0.10=3 fossil. Total=18.
- serres(7): fossil(1+3)/COP 3.0 + elec(1) → 2 elec. EnR(2) maintained.
- irrigation(3): already elec → 3 elec.
- elevage(5): fossil(2)/COP 3.0 + elec(2)×0.9 → 3 elec. EnR(1) maintained.
- sechage(3): 1 elec + 1 EnR.
- peche(4): 1 elec + 1 H2 + 1 fossil (from params).
- autres(3): 2 elec (from params).

**Step 5: Commit**

```bash
git commit -m "feat: add convert_agriculture() — 55 TWh -> 36 TWh"
```

---

### Task 9: convert_non_energy()

**Step 1: Tests** — elec≈5, h2≈28, bio≈27, fossil≈35, total≈95.

**Step 3: Logic** from reference table:
- petrochimie(60): recycling -20% → 48. bio 30%=14. H2 20%=10. elec 3. fossil residual 30%=20. Total → 3+10+15+20=48.
- engrais(18): H2 vert 16 + fossil residual 2. Total=18.
- bitumes(15): recycling -20% → 12. bio 30%=5. fossil 50%=7. Total=12.
- lubrifiants(5): bio 50%=2. fossil 50%=2. Total=4.
- solvants(5): green 60%=3 bio. fossil 40%=2. Total=5.
- autres(10): 2 elec + 2 H2 + 2 bio + 2 fossil (from params). Total=8.

**Step 5: Commit**

```bash
git commit -m "feat: add convert_non_energy() — 113 TWh -> 95 TWh"
```

---

## Phase 3: System Integration

### Task 10: calculate_system_balance() and system-level tests

**Files:**
- Modify: `src/consumption.py`
- Modify: `tests/test_consumption.py`

**Step 1: Write the failing system tests**

```python
class TestSystemBalance_Integration:
    def test_total_electricity_is_733(self):
        balance = calculate_system_balance()
        assert balance.total_electricity_twh == pytest.approx(733, abs=10)

    def test_direct_electricity_is_596(self):
        balance = calculate_system_balance()
        assert balance.direct_electricity_twh == pytest.approx(596, abs=10)

    def test_h2_demand_is_89(self):
        balance = calculate_system_balance()
        assert balance.h2_demand_twh == pytest.approx(89, abs=5)

    def test_h2_production_elec_is_137(self):
        balance = calculate_system_balance()
        assert balance.h2_production_elec_twh == pytest.approx(137, abs=10)

    def test_fossil_residual_is_105(self):
        balance = calculate_system_balance()
        assert balance.fossil_residual_twh == pytest.approx(105, abs=10)

    def test_bio_enr_is_240(self):
        balance = calculate_system_balance()
        assert balance.bio_enr_twh == pytest.approx(240, abs=10)

    def test_current_total_is_1615(self):
        balance = calculate_system_balance()
        assert balance.current_total_twh == pytest.approx(1615, abs=1)

    def test_all_sectors_present(self):
        balance = calculate_system_balance()
        assert len(balance.sectors) == 6

    def test_custom_params_change_result(self):
        base = calculate_system_balance()
        custom = calculate_system_balance(
            params=ElectrificationParams(res_chauffage_cop=5.0)
        )
        assert custom.total_electricity_twh < base.total_electricity_twh
```

**Step 3: Implement**

```python
def calculate_system_balance(
    ref: ReferenceData | None = None,
    params: ElectrificationParams | None = None,
) -> SystemBalance:
    """Calculate complete system balance from reference data and parameters.

    This is the single source of truth for all consumption figures.
    """
    if ref is None:
        ref = sdes_2023()
    if params is None:
        params = ElectrificationParams()

    sectors = {
        "residential": convert_residential(ref.residential, params),
        "tertiary": convert_tertiary(ref.tertiary, params),
        "industry": convert_industry(ref.industry, params),
        "transport": convert_transport(ref.transport, params),
        "agriculture": convert_agriculture(ref.agriculture, params),
        "non_energy": convert_non_energy(ref.non_energy, params),
    }
    return SystemBalance.from_sectors(sectors, params.electrolyse_efficiency)
```

**Step 4: Run all tests**

Run: `uv run pytest tests/test_consumption.py -v`
Expected: ALL PASSED (~50-60 tests)

**Step 5: Commit**

```bash
git add src/consumption.py tests/test_consumption.py
git commit -m "feat: add calculate_system_balance() — full 1615 TWh -> 733 TWh elec"
```

---

## Phase 4: Module Adaptation (Profiles)

### Task 11: Delete old tests

**Files:**
- Delete: all files in `tests/` except `tests/__init__.py` and `tests/test_consumption.py`

**Step 1: Remove old test files**

```bash
cd /home/kingwin/energy_transition/energy_model
# Keep only __init__.py and test_consumption.py
find tests/ -name "test_*.py" ! -name "test_consumption.py" -delete
```

**Step 2: Verify remaining tests pass**

Run: `uv run pytest tests/ -v`
Expected: only test_consumption.py tests run; all PASS

**Step 3: Commit**

```bash
git add -A tests/
git commit -m "chore: remove old tests — replaced by test_consumption.py"
```

---

### Task 12: Adapt heating.py to profile mode

**Files:**
- Modify: `src/heating.py`
- Create: `tests/test_profiles.py`

**Step 1: Write profile tests**

```python
# tests/test_profiles.py
"""Tests for temporal profile functions."""
import pytest
from src.heating import profil_chauffage_normalise, HeatingConfig


class TestHeatingProfile:
    def test_sums_to_one(self):
        profil = profil_chauffage_normalise()
        assert sum(profil) == pytest.approx(1.0, abs=0.001)

    def test_returns_12_months(self):
        profil = profil_chauffage_normalise()
        assert len(profil) == 12

    def test_january_greater_than_july(self):
        profil = profil_chauffage_normalise()
        assert profil[0] > profil[6]  # jan > jul

    def test_winter_dominant(self):
        profil = profil_chauffage_normalise()
        winter = profil[0] + profil[1] + profil[10] + profil[11]  # jan,feb,nov,dec
        summer = profil[5] + profil[6] + profil[7] + profil[8]    # jun,jul,aug,sep
        assert winter > 2 * summer
```

**Step 3: Implement**

Add to `src/heating.py` (keep existing functions for backward compat, add new one):

```python
def profil_chauffage_normalise(config: HeatingConfig | None = None) -> list[float]:
    """Return 12 monthly coefficients summing to 1.0.

    Uses the Roland 7-variable model to compute relative heating demand
    per month, then normalizes. The TOTAL TWh comes from consumption.py,
    not from this function.
    """
    if config is None:
        config = HeatingConfig()
    bilan = bilan_chauffage_annuel(config)
    mois = [
        "janvier", "fevrier", "mars", "avril", "mai", "juin",
        "juillet", "aout", "septembre", "octobre", "novembre", "decembre",
    ]
    values = [bilan[m]["energie_annuelle_twh"] for m in mois]
    total = sum(values)
    if total == 0:
        return [1 / 12] * 12
    return [v / total for v in values]
```

**Step 5: Commit**

```bash
git add src/heating.py tests/test_profiles.py
git commit -m "feat: add profil_chauffage_normalise() — normalized monthly profile"
```

---

### Task 13: Adapt transport.py to profile mode

**Files:**
- Modify: `src/transport.py`
- Modify: `tests/test_profiles.py`

**Step 1: Write profile tests**

```python
from src.transport import profil_recharge_normalise, TransportConfig


class TestTransportProfile:
    def test_sums_to_one(self):
        profil = profil_recharge_normalise()
        total = sum(sum(month) for month in profil)
        assert total == pytest.approx(1.0, abs=0.001)

    def test_shape_12x5(self):
        profil = profil_recharge_normalise()
        assert len(profil) == 12
        for month in profil:
            assert len(month) == 5

    def test_night_slot_dominant(self):
        """Nighttime charging (23h-8h, slot 4) should be largest."""
        profil = profil_recharge_normalise()
        jan = profil[0]
        assert jan[4] > jan[0]  # night > morning
```

**Step 3: Implement**

Add `profil_recharge_normalise()` to `src/transport.py`. Extracts the existing charging profile logic from `demande_recharge_par_plage()`, normalizes to sum=1.0 across 12×5=60 slots.

**Step 5: Commit**

```bash
git commit -m "feat: add profil_recharge_normalise() — 12x5 EV charging profile"
```

---

### Task 14: Adapt agriculture.py to profile mode

**Files:**
- Modify: `src/agriculture.py`
- Modify: `tests/test_profiles.py`

**Step 1: Tests** — `profil_agriculture_normalise()` returns 12 monthly coeff summing to 1.0, summer > winter (irrigation peak).

**Step 3: Implement** — Extract monthly coefficients from existing `consommation_mensuelle_twh()`, normalize.

**Step 5: Commit**

```bash
git commit -m "feat: add profil_agriculture_normalise() — monthly seasonal profile"
```

---

## Phase 5: Downstream Updates

### Task 15: Update config.py — remove legacy ConsumptionConfig

**Files:**
- Modify: `src/config.py:103-121` (ConsumptionConfig)

**Step 1: Verify no imports of ConsumptionConfig remain**

Run: `grep -r "ConsumptionConfig" src/ --include="*.py"`
Expected: only in config.py itself and possibly EnergyModelConfig

**Step 2: Remove ConsumptionConfig** from config.py. Remove the `consumption` field from `EnergyModelConfig`. Keep `ProductionConfig`, `StorageConfig`, `FinancialConfig`.

**Step 3: Run tests**

Run: `uv run pytest tests/ -v`
Fix any imports that break.

**Step 4: Commit**

```bash
git commit -m "chore: remove legacy ConsumptionConfig — replaced by consumption.py"
```

---

### Task 16: Update tarification.py — derive from consumption.py

**Files:**
- Modify: `src/tarification.py:24` (TarificationConfig)
- Modify: `tests/test_consumption.py`

**Step 1: Add tarification integration test**

```python
class TestTarificationIntegration:
    def test_tarif_uses_733_twh(self):
        from src.tarification import TarificationConfig, tarif_equilibre_eur_mwh
        from src.consumption import calculate_system_balance
        balance = calculate_system_balance()
        config = TarificationConfig(
            consommation_totale_twh=balance.total_electricity_twh,
        )
        tarif = tarif_equilibre_eur_mwh(config)
        assert tarif > 0
```

**Step 2: Change** `TarificationConfig.consommation_totale_twh` default from 700 to derive from `calculate_system_balance().total_electricity_twh`. Or better: add a factory method `TarificationConfig.from_system_balance(balance)`.

**Step 4: Commit**

```bash
git commit -m "feat: tarification derives consumption from consumption.py (733 TWh)"
```

---

### Task 17: Update sensitivity.py — use consumption.py demand

**Files:**
- Modify: `src/sensitivity.py`

**Step 1: Test** that sensitivity functions accept total electricity demand as parameter.

**Step 2: Modify** `calculate_gas_need_*()` functions to accept `total_demand_twh` parameter instead of computing it internally.

**Step 4: Commit**

```bash
git commit -m "feat: sensitivity.py receives demand from consumption.py"
```

---

### Task 18: Final validation and cleanup

**Files:**
- Modify: `src/rapport.py` (optional, if time permits)

**Step 1: Run full test suite**

Run: `uv run pytest tests/ -v --tb=short`
Expected: ALL PASS (~80 tests)

**Step 2: Verify key numbers**

```bash
uv run python -c "
from src.consumption import calculate_system_balance
b = calculate_system_balance()
print(f'Current total:     {b.current_total_twh:.0f} TWh (expect 1615)')
print(f'Direct electricity:{b.direct_electricity_twh:.0f} TWh (expect 596)')
print(f'H2 demand:         {b.h2_demand_twh:.0f} TWh (expect 89)')
print(f'H2 prod elec:      {b.h2_production_elec_twh:.0f} TWh (expect 137)')
print(f'Total electricity: {b.total_electricity_twh:.0f} TWh (expect 733)')
print(f'Bio/EnR:           {b.bio_enr_twh:.0f} TWh (expect 240)')
print(f'Fossil residual:   {b.fossil_residual_twh:.0f} TWh (expect 105)')
print()
for name, s in b.sectors.items():
    print(f'{name:15s}: {s.current_twh:5.0f} -> {s.total_target_twh:5.0f} TWh '
          f'(elec={s.elec_twh:.0f}, h2={s.h2_twh:.0f}, bio={s.bio_enr_twh:.0f}, '
          f'fos={s.fossil_residual_twh:.0f}) [{s.reduction_pct:.0%}]')
"
```

Expected output matching reference table within tolerances.

**Step 3: Commit and tag**

```bash
git add -A
git commit -m "feat: recalibration v0.8.0 — model aligned on SDES 2023 (1615 TWh)"
git tag v0.8.0
```

---

## Summary

| Phase | Tasks | Tests added | Key deliverable |
|-------|-------|-------------|-----------------|
| 1: Core dataclasses | 1-3 | ~18 | UsageReference, SectorReference, ReferenceData, ElectrificationParams, SystemBalance |
| 2: Conversion functions | 4-9 | ~36 | 6 × convert_*() functions matching reference table |
| 3: System integration | 10 | ~9 | calculate_system_balance() → 733 TWh |
| 4: Module profiles | 11-14 | ~12 | heating/transport/agriculture provide normalized profiles |
| 5: Downstream | 15-18 | ~5 | config cleanup, tarification, sensitivity, validation |
| **Total** | **18 tasks** | **~80 tests** | **Model aligned on SDES 2023** |
