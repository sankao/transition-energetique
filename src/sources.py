"""
Data sources registry for the Energy Transition Model.

All external data sources are documented here with:
- URL
- Access date
- Description
- Parameters derived from this source

This module enables programmatic access to source metadata for
auditability and reproducibility.
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import date


@dataclass
class DataSource:
    """A documented external data source."""

    id: str
    name: str
    url: str
    access_date: date
    description: str
    parameters: List[str]
    notes: Optional[str] = None

    def citation(self) -> str:
        """Generate a citation string."""
        return f"{self.name}. {self.url} (accessed {self.access_date.isoformat()})"


# =============================================================================
# PRODUCTION SOURCES
# =============================================================================

RTE_BILAN_2020 = DataSource(
    id="rte-bilan-2020",
    name="RTE Bilan Électrique 2020",
    url="https://www.rte-france.com/analyses-tendances-et-prospectives/bilan-electrique",
    access_date=date(2026, 1, 4),
    description="Historical French electricity production data by source",
    parameters=[
        "nuclear_min_gw",
        "nuclear_max_gw",
        "hydro_avg_gw",
    ],
    notes="Used 2020 as reference year (pre-COVID recovery, representative)"
)

RTE_PANORAMA_ENR = DataSource(
    id="rte-panorama-enr",
    name="RTE Panorama des Énergies Renouvelables",
    url="https://www.rte-france.com/analyses-tendances-et-prospectives/panorama-de-lelectricite-renouvelable",
    access_date=date(2026, 1, 4),
    description="Current renewable energy capacity in France",
    parameters=[
        "solar_capacity_current_gwc",
    ],
)

PVGIS_EU_JRC = DataSource(
    id="pvgis-eu-jrc",
    name="PVGIS - Photovoltaic Geographical Information System",
    url="https://re.jrc.ec.europa.eu/pvg_tools/en/",
    access_date=date(2026, 1, 4),
    description="EU Joint Research Centre PV production simulator",
    parameters=[
        "solar_capacity_factors",  # Derived from PVGIS simulations
    ],
    notes="Capacity factors range 7-22% depending on month and location"
)

# =============================================================================
# CONSUMPTION SOURCES
# =============================================================================

ADEME_CHIFFRES_CLES = DataSource(
    id="ademe-chiffres-cles",
    name="ADEME Chiffres clés du bâtiment",
    url="https://www.ademe.fr/",
    access_date=date(2026, 1, 4),
    description="Building energy consumption statistics",
    parameters=[
        "residential_heating_fraction",
    ],
)

ADEME_PAC = DataSource(
    id="ademe-pac",
    name="ADEME Guide Pompes à Chaleur",
    url="https://www.ademe.fr/expertises/batiment/passer-a-laction/elements-dequipement/pompes-a-chaleur",
    access_date=date(2026, 1, 4),
    description="Heat pump performance data",
    parameters=[
        "heat_pump_cop",
    ],
    notes="COP varies 2.0-5.0 depending on type and temperature. Model uses conservative 2.0"
)

INSEE_LOGEMENTS = DataSource(
    id="insee-logements",
    name="INSEE Recensement de la Population - Logements",
    url="https://www.insee.fr/fr/statistiques",
    access_date=date(2026, 1, 4),
    description="French housing stock statistics",
    parameters=[
        "number_individual_houses",  # ~20 million
        "number_collective_housing",  # ~10 million
    ],
)

# =============================================================================
# TEMPORAL SOURCES
# =============================================================================

WORLDDATA_SUNSET = DataSource(
    id="worlddata-sunset",
    name="WorldData.info Sunset Times France",
    url="https://www.worlddata.info/europe/france/sunset.php",
    access_date=date(2026, 1, 4),
    description="Sunrise and sunset times for Paris (latitude ~49°N)",
    parameters=[
        "sunset_times",
    ],
)

# =============================================================================
# FINANCIAL SOURCES
# =============================================================================

IRENA_COSTS_2024 = DataSource(
    id="irena-costs-2024",
    name="IRENA Renewable Power Generation Costs 2024",
    url="https://www.irena.org/publications/2024/Sep/Renewable-Power-Generation-Costs-in-2023",
    access_date=date(2026, 1, 4),
    description="Global renewable energy cost benchmarks",
    parameters=[
        "solar_capex_eur_per_kw",
        "solar_lifetime_years",
    ],
)

BNEF_STORAGE_2024 = DataSource(
    id="bnef-storage-2024",
    name="BloombergNEF Energy Storage Outlook 2024",
    url="https://about.bnef.com/energy-storage-outlook/",
    access_date=date(2026, 1, 4),
    description="Battery storage cost projections",
    parameters=[
        "storage_capex_eur_per_kwh",
        "storage_lifetime_years",
        "battery_efficiency",
    ],
)

EEX_GAS_PRICES = DataSource(
    id="eex-gas-prices",
    name="European Energy Exchange - Gas/Power Markets",
    url="https://www.eex.com/",
    access_date=date(2026, 1, 4),
    description="European gas and electricity market prices",
    parameters=[
        "gas_cost_eur_per_mwh",
    ],
    notes="SRMC (Short Run Marginal Cost) for CCGT plants"
)

# =============================================================================
# STORAGE REFERENCE SOURCES
# =============================================================================

EDF_HYDRAULIQUE = DataSource(
    id="edf-hydraulique",
    name="EDF Hydraulique - Grand'Maison",
    url="https://www.edf.fr/groupe-edf/nos-energies/energies-renouvelables/hydraulique",
    access_date=date(2026, 1, 4),
    description="STEP (pumped hydro) capacity data",
    parameters=[
        "step_grandmaison_gwh",
        "france_step_total_gwh",
    ],
)

VISTRA_MOSS_LANDING = DataSource(
    id="vistra-moss-landing",
    name="Vistra Moss Landing Energy Storage",
    url="https://vistracorp.com/energy-storage/",
    access_date=date(2026, 1, 4),
    description="World's largest battery storage facility reference",
    parameters=[
        "moss_landing_gwh",
    ],
)


# =============================================================================
# SOURCE REGISTRY
# =============================================================================

ALL_SOURCES = [
    RTE_BILAN_2020,
    RTE_PANORAMA_ENR,
    PVGIS_EU_JRC,
    ADEME_CHIFFRES_CLES,
    ADEME_PAC,
    INSEE_LOGEMENTS,
    WORLDDATA_SUNSET,
    IRENA_COSTS_2024,
    BNEF_STORAGE_2024,
    EEX_GAS_PRICES,
    EDF_HYDRAULIQUE,
    VISTRA_MOSS_LANDING,
]


def get_source(source_id: str) -> Optional[DataSource]:
    """Get a source by its ID."""
    for source in ALL_SOURCES:
        if source.id == source_id:
            return source
    return None


def get_sources_for_parameter(parameter: str) -> List[DataSource]:
    """Get all sources that contribute to a parameter."""
    return [s for s in ALL_SOURCES if parameter in s.parameters]


def generate_bibliography() -> str:
    """Generate a bibliography of all sources."""
    lines = ["# Bibliography", ""]
    for source in sorted(ALL_SOURCES, key=lambda s: s.name):
        lines.append(f"- {source.citation()}")
    return "\n".join(lines)


def check_source_freshness(max_age_days: int = 365) -> List[DataSource]:
    """Return sources that haven't been updated recently."""
    today = date.today()
    stale = []
    for source in ALL_SOURCES:
        age = (today - source.access_date).days
        if age > max_age_days:
            stale.append(source)
    return stale
