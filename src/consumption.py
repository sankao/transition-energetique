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
