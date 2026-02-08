"""
Tertiary and industry sectors module for the Energy Transition Model.

Details the sectors currently modeled as "maintained at current level":
- Industry: electrification of processes, high-temperature heat
- Tertiary: energy efficiency, heating electrification

Sources:
- SDES Bilan énergétique de la France 2022
- ADEME: sectoral energy studies
- RTE Futurs Énergétiques 2050
"""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class IndustrieConfig:
    """Industrial sector energy parameters."""

    # --- Current consumption by usage (TWh/year) ---
    # Source: SDES Bilan énergétique 2022

    # High-temperature heat (>400°C): steel, cement, glass, chemicals
    # Difficult to electrify — requires hydrogen or maintained fossil
    chaleur_haute_temp_twh: float = 60.0

    # Medium-temperature heat (100-400°C): chemicals, food processing
    # Partially electrifiable via industrial heat pumps
    chaleur_moyenne_temp_twh: float = 40.0

    # Low-temperature heat (<100°C): drying, pasteurization
    # Fully electrifiable via heat pumps
    chaleur_basse_temp_twh: float = 25.0

    # Mechanical drive (motors, compressors) — already largely electric
    force_motrice_twh: float = 55.0

    # Electrochemistry, electrolysis (already electric)
    electrochimie_twh: float = 15.0

    # Other (lighting, IT, etc.)
    autres_twh: float = 10.0

    # --- Electrification parameters ---
    # High-temp: fraction replaceable by electric arc / hydrogen
    haute_temp_electrifiable: float = 0.30
    haute_temp_efficacite: float = 0.85  # Electric arc is quite efficient

    # Medium-temp: industrial heat pumps
    moyenne_temp_electrifiable: float = 0.70
    moyenne_temp_cop: float = 2.5

    # Low-temp: heat pumps
    basse_temp_electrifiable: float = 0.90
    basse_temp_cop: float = 3.5

    # Energy efficiency gains from process optimization
    # Source: ADEME estimates 15-20% potential
    gain_efficacite_fraction: float = 0.15


@dataclass
class TertiaireConfig:
    """Tertiary sector energy parameters."""

    # --- Current consumption by usage (TWh/year) ---
    # Source: SDES / CEREN 2022

    # Heating (offices, shops, schools, hospitals)
    chauffage_twh: float = 85.0

    # Cooling/air conditioning
    climatisation_twh: float = 15.0

    # Lighting
    eclairage_twh: float = 30.0

    # Specific electricity (IT, appliances, elevators)
    electricite_specifique_twh: float = 45.0

    # Hot water
    eau_chaude_twh: float = 15.0

    # Other
    autres_twh: float = 10.0

    # --- Electrification and efficiency parameters ---
    # Heating: fraction currently fossil (gas, oil)
    chauffage_fossile_fraction: float = 0.60
    chauffage_pac_cop: float = 3.0

    # Lighting: LED replacement savings
    eclairage_gain_led: float = 0.50  # 50% reduction

    # Building renovation: insulation gains on heating
    renovation_gain_chauffage: float = 0.30  # 30% reduction

    # Cooling: efficiency improvement
    climatisation_gain: float = 0.20


def bilan_industrie(config: Optional[IndustrieConfig] = None) -> Dict[str, float]:
    """
    Calculate industrial sector energy balance after electrification.

    Args:
        config: Industry configuration

    Returns:
        Dict with current vs electrified consumption
    """
    if config is None:
        config = IndustrieConfig()

    # Current total
    actuel_total = (config.chaleur_haute_temp_twh + config.chaleur_moyenne_temp_twh +
                    config.chaleur_basse_temp_twh + config.force_motrice_twh +
                    config.electrochimie_twh + config.autres_twh)

    # High-temp electrification
    ht_elec = (config.chaleur_haute_temp_twh * config.haute_temp_electrifiable
               * config.haute_temp_efficacite)
    ht_fossile = config.chaleur_haute_temp_twh * (1 - config.haute_temp_electrifiable)

    # Medium-temp electrification (heat pumps)
    mt_elec = (config.chaleur_moyenne_temp_twh * config.moyenne_temp_electrifiable
               / config.moyenne_temp_cop)
    mt_fossile = config.chaleur_moyenne_temp_twh * (1 - config.moyenne_temp_electrifiable)

    # Low-temp electrification (heat pumps)
    bt_elec = (config.chaleur_basse_temp_twh * config.basse_temp_electrifiable
               / config.basse_temp_cop)
    bt_fossile = config.chaleur_basse_temp_twh * (1 - config.basse_temp_electrifiable)

    # Already electric
    force_motrice = config.force_motrice_twh
    electrochimie = config.electrochimie_twh
    autres = config.autres_twh

    # Apply efficiency gains
    total_elec_brut = ht_elec + mt_elec + bt_elec + force_motrice + electrochimie + autres
    total_elec = total_elec_brut * (1 - config.gain_efficacite_fraction)

    fossile_residuel = ht_fossile + mt_fossile + bt_fossile

    return {
        'actuel_total_twh': actuel_total,
        'chaleur_ht_elec_twh': ht_elec,
        'chaleur_ht_fossile_twh': ht_fossile,
        'chaleur_mt_elec_twh': mt_elec,
        'chaleur_mt_fossile_twh': mt_fossile,
        'chaleur_bt_elec_twh': bt_elec,
        'chaleur_bt_fossile_twh': bt_fossile,
        'force_motrice_twh': force_motrice,
        'electrochimie_twh': electrochimie,
        'autres_twh': autres,
        'total_elec_twh': total_elec,
        'fossile_residuel_twh': fossile_residuel,
        'gain_efficacite_twh': total_elec_brut - total_elec,
    }


def bilan_tertiaire(config: Optional[TertiaireConfig] = None) -> Dict[str, float]:
    """
    Calculate tertiary sector energy balance after electrification.

    Args:
        config: Tertiary configuration

    Returns:
        Dict with current vs electrified consumption
    """
    if config is None:
        config = TertiaireConfig()

    actuel_total = (config.chauffage_twh + config.climatisation_twh +
                    config.eclairage_twh + config.electricite_specifique_twh +
                    config.eau_chaude_twh + config.autres_twh)

    # Heating: electrify fossil portion with PAC, reduce via renovation
    chauffage_apres_renovation = config.chauffage_twh * (1 - config.renovation_gain_chauffage)
    chauffage_fossile_pac = (chauffage_apres_renovation * config.chauffage_fossile_fraction
                             / config.chauffage_pac_cop)
    chauffage_elec_existant = chauffage_apres_renovation * (1 - config.chauffage_fossile_fraction)
    chauffage_total = chauffage_fossile_pac + chauffage_elec_existant

    # Cooling: efficiency gains
    climatisation = config.climatisation_twh * (1 - config.climatisation_gain)

    # Lighting: LED gains
    eclairage = config.eclairage_twh * (1 - config.eclairage_gain_led)

    # Unchanged
    elec_specifique = config.electricite_specifique_twh
    eau_chaude = config.eau_chaude_twh  # Already largely electric or PAC
    autres = config.autres_twh

    total_elec = chauffage_total + climatisation + eclairage + elec_specifique + eau_chaude + autres

    return {
        'actuel_total_twh': actuel_total,
        'chauffage_elec_twh': chauffage_total,
        'climatisation_twh': climatisation,
        'eclairage_twh': eclairage,
        'electricite_specifique_twh': elec_specifique,
        'eau_chaude_twh': eau_chaude,
        'autres_twh': autres,
        'total_elec_twh': total_elec,
        'gain_renovation_twh': config.chauffage_twh - chauffage_apres_renovation,
        'gain_eclairage_twh': config.eclairage_twh - eclairage,
        'gain_climatisation_twh': config.climatisation_twh - climatisation,
    }


def bilan_tous_secteurs(
    industrie_config: Optional[IndustrieConfig] = None,
    tertiaire_config: Optional[TertiaireConfig] = None,
) -> Dict[str, float]:
    """
    Combined balance for industry + tertiary.

    Args:
        industrie_config: Industry configuration
        tertiaire_config: Tertiary configuration

    Returns:
        Combined sector balance
    """
    ind = bilan_industrie(industrie_config)
    ter = bilan_tertiaire(tertiaire_config)

    return {
        'industrie_actuel_twh': ind['actuel_total_twh'],
        'industrie_elec_twh': ind['total_elec_twh'],
        'industrie_fossile_twh': ind['fossile_residuel_twh'],
        'tertiaire_actuel_twh': ter['actuel_total_twh'],
        'tertiaire_elec_twh': ter['total_elec_twh'],
        'total_actuel_twh': ind['actuel_total_twh'] + ter['actuel_total_twh'],
        'total_elec_twh': ind['total_elec_twh'] + ter['total_elec_twh'],
        'total_fossile_residuel_twh': ind['fossile_residuel_twh'],
    }


def resume_secteurs(
    industrie_config: Optional[IndustrieConfig] = None,
    tertiaire_config: Optional[TertiaireConfig] = None,
) -> str:
    """
    Generate human-readable summary for industry and tertiary sectors.

    Args:
        industrie_config: Industry configuration
        tertiaire_config: Tertiary configuration

    Returns:
        Formatted summary string
    """
    ind = bilan_industrie(industrie_config)
    ter = bilan_tertiaire(tertiaire_config)
    total = bilan_tous_secteurs(industrie_config, tertiaire_config)

    lines = [
        "Secteurs Industrie et Tertiaire",
        "=" * 45,
        "",
        "INDUSTRIE",
        f"  Actuel total:          {ind['actuel_total_twh']:>6.1f} TWh",
        f"  Chaleur haute T (élec):{ind['chaleur_ht_elec_twh']:>6.1f} TWh",
        f"  Chaleur haute T (foss):{ind['chaleur_ht_fossile_twh']:>6.1f} TWh (non-électrifiable)",
        f"  Chaleur moy. T (PAC):  {ind['chaleur_mt_elec_twh']:>6.1f} TWh",
        f"  Chaleur basse T (PAC): {ind['chaleur_bt_elec_twh']:>6.1f} TWh",
        f"  Force motrice:         {ind['force_motrice_twh']:>6.1f} TWh",
        f"  Électrochimie:         {ind['electrochimie_twh']:>6.1f} TWh",
        f"  Gain efficacité:       {ind['gain_efficacite_twh']:>6.1f} TWh (-{IndustrieConfig().gain_efficacite_fraction*100:.0f}%)",
        f"  TOTAL élec:            {ind['total_elec_twh']:>6.1f} TWh",
        "",
        "TERTIAIRE",
        f"  Actuel total:          {ter['actuel_total_twh']:>6.1f} TWh",
        f"  Chauffage (rénové+PAC):{ter['chauffage_elec_twh']:>6.1f} TWh",
        f"  Climatisation:         {ter['climatisation_twh']:>6.1f} TWh",
        f"  Éclairage (LED):       {ter['eclairage_twh']:>6.1f} TWh",
        f"  Élec. spécifique:      {ter['electricite_specifique_twh']:>6.1f} TWh",
        f"  Eau chaude:            {ter['eau_chaude_twh']:>6.1f} TWh",
        f"  TOTAL élec:            {ter['total_elec_twh']:>6.1f} TWh",
        "",
        "SYNTHÈSE",
        f"  Actuel (ind+tert):     {total['total_actuel_twh']:>6.1f} TWh",
        f"  Électrifié:            {total['total_elec_twh']:>6.1f} TWh",
        f"  Fossile résiduel:      {total['total_fossile_residuel_twh']:>6.1f} TWh",
        f"  Réduction:             {total['total_actuel_twh'] - total['total_elec_twh'] - total['total_fossile_residuel_twh']:>6.1f} TWh",
    ]

    return '\n'.join(lines)
