"""
Energy Transition Model - France

Modular simulation of French energy transition with solar PV deployment.

See SOURCES.md for data source documentation.
"""

from .config import EnergyModelConfig, DEFAULT_CONFIG
from .sources import ALL_SOURCES, get_source, get_sources_for_parameter

__version__ = "0.2.0"
__all__ = [
    "EnergyModelConfig",
    "DEFAULT_CONFIG",
    "ALL_SOURCES",
    "get_source",
    "get_sources_for_parameter",
]
