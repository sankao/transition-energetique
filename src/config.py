"""
Configuration module for the Energy Transition Model.

All model parameters are centralized here with documentation of:
- Units
- Valid ranges
- Data sources (see SOURCES.md and src/sources.py for full references)

Source IDs reference entries in src/sources.py for programmatic access.
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class TemporalConfig:
    """Temporal parameters for the model."""

    # Days per month (approximation for simplified calculation)
    # Source: Model simplification
    jours_par_mois: int = 30

    # Sunset times by month (decimal hours, Paris latitude ~49°N)
    # Source: worlddata.info/europe/france/sunset.php
    sunset_times: Dict[str, float] = field(default_factory=lambda: {
        'Janvier': 17.4,    # 17:23
        'Février': 18.2,    # 18:12
        'Mars': 18.9,       # 18:56
        'Avril': 20.7,      # 20:43
        'Mai': 21.5,        # 21:27
        'Juin': 22.0,       # 21:57
        'Juillet': 21.9,    # 21:51
        'Août': 21.1,       # 21:08
        'Septembre': 20.1,  # 20:05
        'Octobre': 19.1,    # 19:03
        'Novembre': 17.2,   # 17:12
        'Décembre': 16.9,   # 16:56
    })

    # Time slots definition (name -> duration in hours)
    time_slots: Dict[str, float] = field(default_factory=lambda: {
        '8h-13h': 5.0,
        '13h-18h': 5.0,
        '18h-20h': 2.0,
        '20h-23h': 3.0,
        '23h-8h': 9.0,
    })

    # Month ordering (calendar and winter-priority)
    mois_ordre: tuple = (
        'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
        'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
    )

    mois_ordre_hiver: tuple = (
        'Janvier', 'Décembre', 'Novembre', 'Février', 'Octobre',
        'Mars', 'Avril', 'Septembre', 'Mai', 'Août', 'Juin', 'Juillet'
    )


@dataclass
class ProductionConfig:
    """Production-side parameters."""

    # Solar PV capacity (GWc)
    # Breakdown: 200 GWc residential + 50 GWc collective + 250 GWc centralized
    # Source: Model scenario assumption
    solar_capacity_gwc: float = 500.0

    # Current French solar capacity for reference (GWc)
    # Source: RTE 2024
    solar_capacity_current_gwc: float = 20.0

    # Nuclear baseline production range (GW)
    # Source: RTE 2020 data
    nuclear_min_gw: float = 30.0  # Summer minimum
    nuclear_max_gw: float = 50.0  # Winter maximum

    # Hydro baseline production (GW)
    # Source: RTE 2020 data
    hydro_avg_gw: float = 7.5

    # Maximum base production without solar (GW)
    # = nuclear_max + hydro + margin
    prod_base_max_gw: float = 65.0

    # Maximum theoretical solar production (GW) at 500 GWc
    # Based on capacity factor ~30% at peak
    prod_solaire_max_gw: float = 150.0


@dataclass
class ConsumptionConfig:
    """Consumption-side parameters."""

    # Heat pump coefficient of performance (legacy, fixed value)
    # For detailed temperature-dependent COP, use HeatingConfig in src/heating.py
    # Source: Conservative estimate for air-source heat pumps
    # Valid range: 2.0 - 4.0 depending on temperature
    heat_pump_cop: float = 2.0

    # Fraction of residential consumption that is heating
    # Source: ADEME statistics
    residential_heating_fraction: float = 0.67

    # Transport electrification efficiency factors
    # Source: Model assumptions based on motor efficiency
    transport_freight_factor: float = 0.4   # Thermal -> electric efficiency gain
    transport_passenger_factor: float = 0.2  # Includes modal shift


@dataclass
class StorageConfig:
    """Energy storage parameters."""

    # Round-trip efficiency for battery storage
    # Source: Industry standard for Li-ion
    battery_efficiency: float = 0.85

    # Reference storage capacities (GWh)
    # Source: Grand'Maison STEP, Moss Landing battery
    step_grandmaison_gwh: float = 5.0
    moss_landing_gwh: float = 3.0
    france_step_total_gwh: float = 100.0


@dataclass
class FinancialConfig:
    """Financial parameters for cost analysis."""

    # Gas cost (€/MWh = €M/TWh)
    # Source: CCGT marginal cost Europe 2024
    gas_cost_eur_per_mwh: float = 90.0

    # Solar PV CAPEX (€/kW = €M/GWc)
    # Source: IRENA Europe 2024
    solar_capex_eur_per_kw: float = 600.0

    # Battery storage CAPEX (€/kWh = €M/GWh)
    # Source: BNEF Europe 2024 (turnkey)
    storage_capex_eur_per_kwh: float = 200.0

    # Asset lifetimes (years)
    solar_lifetime_years: int = 30
    storage_lifetime_years: int = 15

    # Analysis horizon (years)
    analysis_horizon_years: int = 30


@dataclass
class EnergyModelConfig:
    """
    Main configuration container for the Energy Transition Model.

    All parameters are documented with units, valid ranges, and sources.
    Modify this configuration to run different scenarios.

    Example:
        config = EnergyModelConfig()
        config.production.solar_capacity_gwc = 700  # Test higher solar
        config.consumption.heat_pump_cop = 3.0      # Better heat pumps
    """

    temporal: TemporalConfig = field(default_factory=TemporalConfig)
    production: ProductionConfig = field(default_factory=ProductionConfig)
    consumption: ConsumptionConfig = field(default_factory=ConsumptionConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    financial: FinancialConfig = field(default_factory=FinancialConfig)

    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate()

    def _validate(self):
        """Check that parameters are within valid ranges."""
        errors = []

        # Production validations
        if self.production.solar_capacity_gwc < 0:
            errors.append("solar_capacity_gwc must be >= 0")
        if self.production.solar_capacity_gwc > 2000:
            errors.append("solar_capacity_gwc > 2000 GWc is unrealistic")

        # Consumption validations
        if not 1.5 <= self.consumption.heat_pump_cop <= 5.0:
            errors.append("heat_pump_cop should be between 1.5 and 5.0")

        # Storage validations
        if not 0.5 <= self.storage.battery_efficiency <= 1.0:
            errors.append("battery_efficiency should be between 0.5 and 1.0")

        # Financial validations
        if self.financial.gas_cost_eur_per_mwh <= 0:
            errors.append("gas_cost must be positive")
        if self.financial.solar_capex_eur_per_kw <= 0:
            errors.append("solar_capex must be positive")

        if errors:
            raise ValueError(f"Configuration errors: {'; '.join(errors)}")

    def summary(self) -> str:
        """Return a human-readable summary of the configuration."""
        return f"""
Energy Model Configuration
==========================

PRODUCTION
  Solar PV capacity: {self.production.solar_capacity_gwc} GWc
  Nuclear range: {self.production.nuclear_min_gw}-{self.production.nuclear_max_gw} GW
  Hydro average: {self.production.hydro_avg_gw} GW

CONSUMPTION
  Heat pump COP: {self.consumption.heat_pump_cop}
  Heating fraction: {self.consumption.residential_heating_fraction*100:.0f}%
  Transport factors: freight={self.consumption.transport_freight_factor}, passenger={self.consumption.transport_passenger_factor}

STORAGE
  Battery efficiency: {self.storage.battery_efficiency*100:.0f}%

FINANCIAL
  Gas cost: €{self.financial.gas_cost_eur_per_mwh}/MWh
  Solar CAPEX: €{self.financial.solar_capex_eur_per_kw}/kW
  Storage CAPEX: €{self.financial.storage_capex_eur_per_kwh}/kWh
  Analysis horizon: {self.financial.analysis_horizon_years} years
"""


# Default configuration instance
DEFAULT_CONFIG = EnergyModelConfig()
