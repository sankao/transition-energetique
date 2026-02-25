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
        UsageReference("chauffage",        292, 50,  94, 31, 0, 105, 12),
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
        UsageReference("autres",            15,  3,   7,  1, 0,   1,  3),
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
