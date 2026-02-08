"""
Energy Transition Model - France

Modular simulation of French energy transition with solar PV deployment.

See SOURCES.md for data source documentation.
"""

from .config import EnergyModelConfig, DEFAULT_CONFIG
from .emissions import EmissionsConfig, bilan_carbone
from .heating import HeatingConfig, bilan_chauffage_annuel
from .sources import ALL_SOURCES, get_source, get_sources_for_parameter
from .tarification import TarificationConfig, tarif_equilibre_eur_mwh
from .trajectory import TrajectoryConfig, calculer_trajectoire

__version__ = "0.6.0"
__all__ = [
    "EnergyModelConfig",
    "DEFAULT_CONFIG",
    "EmissionsConfig",
    "bilan_carbone",
    "HeatingConfig",
    "bilan_chauffage_annuel",
    "TarificationConfig",
    "tarif_equilibre_eur_mwh",
    "TrajectoryConfig",
    "calculer_trajectoire",
    "ALL_SOURCES",
    "get_source",
    "get_sources_for_parameter",
]
