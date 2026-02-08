"""
Detailed heating module for the Energy Transition Model.

Implements Roland's 7-variable heating model:
1. Nombre de maisons individuelles (number of houses)
2. Volume moyen (average volume)
3. Degré d'isolation (G coefficient, W/m³/°C)
4. Température souhaitée (desired indoor temperature)
5. Température extérieure par période (outdoor temp by month)
6. Existence ou non d'une pompe à chaleur (heat pump presence)
7. COP en fonction de la température (temperature-dependent COP)

Formula: P_chauffage = G × V × (T_int - T_ext) × N_maisons / COP(T_ext)

Sources documented in SOURCES.md and src/sources.py.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple


# Monthly average exterior temperatures for France (°C)
# Source: Statista / Météo France, average 2021-2022
# Used in the original ODS model ("consommation chauffage et autres selon mois")
TEMPERATURES_EXTERIEURES: Dict[str, float] = {
    'Janvier': 5.2,
    'Février': 6.7,
    'Mars': 9.1,
    'Avril': 11.4,
    'Mai': 15.3,
    'Juin': 19.8,
    'Juillet': 22.1,
    'Août': 21.6,
    'Septembre': 17.9,
    'Octobre': 13.8,
    'Novembre': 8.4,
    'Décembre': 5.8,
}

# Heating distribution coefficients by time slot
# Source: Model assumption based on occupancy and thermostat patterns
# Night has lower setpoint, peak hours have full heating
COEFFICIENTS_PLAGE: Dict[str, float] = {
    '8h-13h': 1.0,     # Full heating during morning
    '13h-18h': 0.8,    # Slightly reduced (solar gains, some absence)
    '18h-20h': 1.0,    # Full heating - return home
    '20h-23h': 1.0,    # Full heating - evening
    '23h-8h': 0.7,     # Reduced setpoint at night (typically -2°C)
}


@dataclass
class HeatingConfig:
    """
    Detailed heating parameters with Roland's 7 variables.

    All parameters are explicit and auditable with documented sources.
    """

    # --- Variable 1: Nombre de maisons individuelles ---
    # Source: INSEE Recensement de la Population
    # ~20 million individual houses in mainland France
    nombre_maisons: int = 20_000_000

    # --- Variable 2: Volume moyen (m³) ---
    # Source: ADEME / INSEE - average house 120 m² × 2.5 m ceiling
    surface_moyenne_m2: float = 120.0
    hauteur_plafond_m: float = 2.5

    # --- Variable 3: Degré d'isolation - coefficient G (W/m³/°C) ---
    # Source: RT 2005 / ADEME
    # G represents global heat loss per unit volume per degree of temperature
    # difference. Lower = better insulation.
    # RT 2005: ~0.65, RT 2012: ~0.45, RE 2020: ~0.35, Passivhaus: ~0.15
    coefficient_g: float = 0.65

    # --- Variable 4: Température souhaitée (°C) ---
    # Source: ADEME recommendation
    temperature_interieure: float = 19.0

    # --- Variable 5: Températures extérieures par mois (°C) ---
    # Source: Statista / Météo France (2021-2022 averages)
    temperatures_exterieures: Dict[str, float] = field(
        default_factory=lambda: dict(TEMPERATURES_EXTERIEURES)
    )

    # --- Variable 6: Existence de pompes à chaleur ---
    # True = all houses have heat pumps (target scenario)
    # False = direct electric heating (resistance)
    avec_pompe_a_chaleur: bool = True

    # --- Variable 7: COP en fonction de la température ---
    # Source: ADEME / manufacturer data for air-source heat pumps
    # COP decreases as outdoor temperature drops
    # Format: {temperature_°C: COP}
    # Interpolated linearly between points
    cop_par_temperature: Dict[float, float] = field(default_factory=lambda: {
        -15.0: 1.5,   # Very cold: COP drops significantly
        -10.0: 1.8,   # Cold snap
        -5.0: 2.1,    # Cold winter
        0.0: 2.5,     # Frost
        5.0: 3.0,     # Mild winter
        10.0: 3.5,    # Autumn/spring
        15.0: 4.0,    # Mild - heating barely needed
    })

    @property
    def volume_moyen_m3(self) -> float:
        """Average house volume in m³."""
        return self.surface_moyenne_m2 * self.hauteur_plafond_m


def interpoler_cop(temperature: float, cop_table: Dict[float, float]) -> float:
    """
    Interpolate COP from temperature lookup table.

    Linear interpolation between defined points.
    Clamps to boundary values outside the table range.

    Args:
        temperature: Outdoor temperature in °C
        cop_table: Dict mapping temperature to COP

    Returns:
        Interpolated COP value
    """
    temps = sorted(cop_table.keys())

    # Clamp to boundaries
    if temperature <= temps[0]:
        return cop_table[temps[0]]
    if temperature >= temps[-1]:
        return cop_table[temps[-1]]

    # Find bracketing temperatures
    for i in range(len(temps) - 1):
        t_low, t_high = temps[i], temps[i + 1]
        if t_low <= temperature <= t_high:
            # Linear interpolation
            fraction = (temperature - t_low) / (t_high - t_low)
            cop_low = cop_table[t_low]
            cop_high = cop_table[t_high]
            return cop_low + fraction * (cop_high - cop_low)

    return 2.0  # Fallback (should not reach here)


def besoin_thermique_maison_w(
    config: HeatingConfig,
    temperature_ext: float,
) -> float:
    """
    Calculate thermal power need for one house (Watts).

    Formula: P = G × V × max(0, T_int - T_ext)

    Args:
        config: Heating configuration
        temperature_ext: Outdoor temperature in °C

    Returns:
        Thermal power in Watts (before heat pump COP)
    """
    delta_t = max(0.0, config.temperature_interieure - temperature_ext)
    return config.coefficient_g * config.volume_moyen_m3 * delta_t


def besoin_electrique_maison_w(
    config: HeatingConfig,
    temperature_ext: float,
) -> float:
    """
    Calculate electrical power need for heating one house (Watts).

    If heat pump: P_elec = P_thermique / COP(T_ext)
    If resistance: P_elec = P_thermique

    Args:
        config: Heating configuration
        temperature_ext: Outdoor temperature in °C

    Returns:
        Electrical power in Watts
    """
    p_thermique = besoin_thermique_maison_w(config, temperature_ext)

    if config.avec_pompe_a_chaleur:
        cop = interpoler_cop(temperature_ext, config.cop_par_temperature)
        return p_thermique / cop
    else:
        return p_thermique


def besoin_national_chauffage_kw(
    config: HeatingConfig,
    mois: str,
    plage: str,
) -> float:
    """
    Calculate national heating electricity demand (kW).

    Scales single-house demand to all houses, adjusted for time slot.

    Args:
        config: Heating configuration
        mois: Month name (e.g., "Janvier")
        plage: Time slot (e.g., "8h-13h")

    Returns:
        National heating power demand in kW
    """
    t_ext = config.temperatures_exterieures.get(mois, 10.0)
    p_maison_w = besoin_electrique_maison_w(config, t_ext)

    # Time slot adjustment coefficient
    coeff = COEFFICIENTS_PLAGE.get(plage, 1.0)

    # Scale to national level: Watts to kW
    return p_maison_w * config.nombre_maisons * coeff / 1000.0


def energie_chauffage_mensuelle_twh(
    config: HeatingConfig,
    mois: str,
    jours_par_mois: int = 30,
) -> float:
    """
    Calculate total monthly heating energy (TWh).

    Sums across all time slots for the month.

    Args:
        config: Heating configuration
        mois: Month name
        jours_par_mois: Days per month (default 30)

    Returns:
        Monthly heating energy in TWh
    """
    total_kwh = 0.0

    durees = {
        '8h-13h': 5.0,
        '13h-18h': 5.0,
        '18h-20h': 2.0,
        '20h-23h': 3.0,
        '23h-8h': 9.0,
    }

    for plage, duree_h in durees.items():
        p_kw = besoin_national_chauffage_kw(config, mois, plage)
        total_kwh += p_kw * duree_h * jours_par_mois

    # kWh to TWh
    return total_kwh / 1e9


def bilan_chauffage_annuel(
    config: Optional[HeatingConfig] = None,
) -> Dict[str, Dict]:
    """
    Calculate annual heating balance with monthly detail.

    Returns a dict with monthly breakdown showing:
    - Temperature, COP, thermal need, electrical need, energy

    Args:
        config: Heating configuration (uses defaults if None)

    Returns:
        Dict mapping month names to their heating data
    """
    if config is None:
        config = HeatingConfig()

    mois_ordre = (
        'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
        'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
    )

    bilan = {}
    total_twh = 0.0

    for mois in mois_ordre:
        t_ext = config.temperatures_exterieures.get(mois, 10.0)
        cop = interpoler_cop(t_ext, config.cop_par_temperature) if config.avec_pompe_a_chaleur else 1.0
        p_thermique_w = besoin_thermique_maison_w(config, t_ext)
        p_electrique_w = besoin_electrique_maison_w(config, t_ext)
        energie_twh = energie_chauffage_mensuelle_twh(config, mois)
        total_twh += energie_twh

        bilan[mois] = {
            'temperature_ext': t_ext,
            'delta_t': max(0.0, config.temperature_interieure - t_ext),
            'cop': cop,
            'besoin_thermique_w_par_maison': p_thermique_w,
            'besoin_electrique_w_par_maison': p_electrique_w,
            'energie_mensuelle_twh': energie_twh,
        }

    bilan['_total'] = {'energie_annuelle_twh': total_twh}

    return bilan


def resume_chauffage(config: Optional[HeatingConfig] = None) -> str:
    """
    Generate a human-readable summary of the heating model.

    Args:
        config: Heating configuration (uses defaults if None)

    Returns:
        Formatted string with heating analysis
    """
    if config is None:
        config = HeatingConfig()

    bilan = bilan_chauffage_annuel(config)
    total = bilan['_total']['energie_annuelle_twh']

    lines = [
        "Module Chauffage Détaillé",
        "=" * 40,
        "",
        "Paramètres (variables Roland):",
        f"  Nombre de maisons:     {config.nombre_maisons:>15,}",
        f"  Surface moyenne:       {config.surface_moyenne_m2:>15.0f} m²",
        f"  Volume moyen:          {config.volume_moyen_m3:>15.0f} m³",
        f"  Coeff. isolation (G):  {config.coefficient_g:>15.2f} W/m³/°C",
        f"  Température intérieure:{config.temperature_interieure:>15.1f} °C",
        f"  Pompe à chaleur:       {'Oui (COP variable)' if config.avec_pompe_a_chaleur else 'Non (résistance)':>15}",
        "",
        "Bilan mensuel:",
        f"  {'Mois':<12} {'T_ext':>6} {'ΔT':>5} {'COP':>5} {'P_therm':>10} {'P_elec':>10} {'TWh':>8}",
        f"  {'':─<12} {'':─>6} {'':─>5} {'':─>5} {'':─>10} {'':─>10} {'':─>8}",
    ]

    for mois in ('Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'):
        d = bilan[mois]
        lines.append(
            f"  {mois:<12} {d['temperature_ext']:>5.1f}° {d['delta_t']:>4.1f}° "
            f"{d['cop']:>5.2f} {d['besoin_thermique_w_par_maison']:>9.0f}W "
            f"{d['besoin_electrique_w_par_maison']:>9.0f}W {d['energie_mensuelle_twh']:>7.2f}"
        )

    lines.extend([
        "",
        f"  TOTAL ANNUEL: {total:.1f} TWh",
        "",
    ])

    # Compare with old model (fixed COP=2)
    config_old = HeatingConfig(
        nombre_maisons=config.nombre_maisons,
        surface_moyenne_m2=config.surface_moyenne_m2,
        hauteur_plafond_m=config.hauteur_plafond_m,
        coefficient_g=config.coefficient_g,
        temperature_interieure=config.temperature_interieure,
        temperatures_exterieures=dict(config.temperatures_exterieures),
        avec_pompe_a_chaleur=True,
        cop_par_temperature={t: 2.0 for t in config.cop_par_temperature},
    )
    bilan_old = bilan_chauffage_annuel(config_old)
    total_old = bilan_old['_total']['energie_annuelle_twh']

    lines.append(f"  Comparaison ancien modèle (COP fixe=2): {total_old:.1f} TWh")
    lines.append(f"  Écart: {total - total_old:+.1f} TWh ({(total/total_old - 1)*100:+.1f}%)")

    return '\n'.join(lines)
