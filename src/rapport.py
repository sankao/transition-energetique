"""
Module de generation de rapport de synthese pour decideurs politiques.

Produit un rapport textuel structure a partir des resultats du modele
de transition energetique. Le rapport est concu pour etre accessible,
factuel et transparent sur les hypotheses utilisees.

Issue: energy_transition-4yf
"""

from typing import Optional

from src.config import EnergyModelConfig, DEFAULT_CONFIG
from src.emissions import bilan_carbone, resume_emissions
from src.heating import bilan_chauffage_annuel, resume_chauffage, HeatingConfig
from src.transport import resume_transport
from src.trajectory import (
    calculer_trajectoire,
    resume_trajectoire,
    TrajectoryConfig,
)


# ---------------------------------------------------------------------------
# Section generators
# ---------------------------------------------------------------------------

def generer_resume_executif(gaz_twh: float = 114.0) -> str:
    """
    Generate a concise executive summary (< 500 characters).

    Args:
        gaz_twh: Annual gas backup in TWh.

    Returns:
        Short executive summary string in French.
    """
    bilan = bilan_carbone(gaz_twh)
    chauffage = bilan_chauffage_annuel()
    total_chauffage_twh = chauffage["_total"]["energie_annuelle_twh"]

    lines = [
        f"Le scenario 500 GWc solaire necessite {gaz_twh:.0f} TWh/an de gaz de backup.",
        f"Le chauffage electrifie represente {total_chauffage_twh:.0f} TWh/an.",
        f"Les emissions nationales passent de {bilan['france_actuelle_mt']:.0f} a {bilan['scenario_total_mt']:.0f} MtCO2/an "
        f"(reduction de {bilan['reduction_pct']:.0f} %).",
        f"L'investissement solaire cumule sur 2024-2050 est estime a {_investissement_cumule():.0f} Mds EUR.",
        "L'eolien et le stockage intersaisonnier ne sont pas inclus (hypothese conservative).",
    ]
    return "\n".join(lines)


def generer_tableau_hypotheses(
    config: Optional[EnergyModelConfig] = None,
) -> str:
    """
    Generate a formatted table of key model assumptions.

    Args:
        config: Model configuration (uses defaults if None).

    Returns:
        Formatted assumptions table string.
    """
    if config is None:
        config = DEFAULT_CONFIG

    sep = "+" + "-" * 42 + "+" + "-" * 22 + "+" + "-" * 30 + "+"
    header = f"| {'Parametre':<40} | {'Valeur':>20} | {'Source':<28} |"

    rows = [
        ("Capacite solaire PV", f"{config.production.solar_capacity_gwc:.0f} GWc", "Hypothese scenario"),
        ("Capacite solaire actuelle", f"{config.production.solar_capacity_current_gwc:.0f} GWc", "RTE 2024"),
        ("Nucleaire (plage)", f"{config.production.nuclear_min_gw:.0f}-{config.production.nuclear_max_gw:.0f} GW", "RTE 2020"),
        ("Hydraulique", f"{config.production.hydro_avg_gw:.1f} GW", "RTE 2020"),
        ("COP pompe a chaleur", f"{config.consumption.heat_pump_cop:.1f}", "ADEME (conservateur)"),
        ("Part chauffage residentiel", f"{config.consumption.residential_heating_fraction * 100:.0f} %", "ADEME"),
        ("Facteur transport fret", f"{config.consumption.transport_freight_factor}", "Hypothese modele"),
        ("Facteur transport passagers", f"{config.consumption.transport_passenger_factor}", "Hypothese modele"),
        ("Rendement stockage batterie", f"{config.storage.battery_efficiency * 100:.0f} %", "Industrie Li-ion"),
        ("Cout gaz (CCGT)", f"{config.financial.gas_cost_eur_per_mwh:.0f} EUR/MWh", "CCGT Europe 2024"),
        ("CAPEX solaire", f"{config.financial.solar_capex_eur_per_kw:.0f} EUR/kW", "IRENA 2024"),
        ("CAPEX stockage", f"{config.financial.storage_capex_eur_per_kwh:.0f} EUR/kWh", "BNEF 2024"),
        ("Duree de vie solaire", f"{config.financial.solar_lifetime_years} ans", "Industrie"),
        ("Duree de vie stockage", f"{config.financial.storage_lifetime_years} ans", "Industrie"),
        ("Horizon d'analyse", f"{config.financial.analysis_horizon_years} ans", "Hypothese modele"),
    ]

    lines = [sep, header, sep]
    for param, valeur, source in rows:
        lines.append(f"| {param:<40} | {valeur:>20} | {source:<28} |")
    lines.append(sep)

    return "\n".join(lines)


def generer_section_resultats(gaz_twh: float = 114.0) -> str:
    """
    Generate the key results section.

    Args:
        gaz_twh: Annual gas backup in TWh.

    Returns:
        Formatted results section string.
    """
    bilan = bilan_carbone(gaz_twh)
    chauffage = bilan_chauffage_annuel()
    total_chauffage_twh = chauffage["_total"]["energie_annuelle_twh"]

    lines = [
        "Resultats cles",
        "-" * 40,
        "",
        "Bilan energetique:",
        f"  Gaz de backup necessaire :     {gaz_twh:.0f} TWh/an",
        f"  Chauffage electrifie :         {total_chauffage_twh:.1f} TWh/an",
        "",
        "Bilan carbone:",
        f"  Emissions actuelles France :   {bilan['france_actuelle_mt']:.0f} MtCO2/an",
        f"  Emissions apres transition :   {bilan['scenario_total_mt']:.0f} MtCO2/an",
        f"  Reduction :                    {bilan['reduction_mt']:.0f} MtCO2 ({bilan['reduction_pct']:.0f} %)",
        f"  Emissions evitees transport :  {bilan['evitees_transport_mt']:.0f} MtCO2",
        f"  Emissions evitees batiments :  {bilan['evitees_batiments_mt']:.0f} MtCO2",
        "",
        "Comparaison aux objectifs SNBC:",
        f"  Objectif 2030 (270 Mt) :       {bilan['vs_objectif_2030_mt']:+.0f} MtCO2",
        f"  Objectif 2050 (80 Mt) :        {bilan['vs_objectif_2050_mt']:+.0f} MtCO2",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _investissement_cumule() -> float:
    """Return cumulative solar investment in EUR billions from trajectory."""
    traj = calculer_trajectoire()
    if traj:
        return traj[-1]["cumul_invest_eur_b"]
    return 0.0


def _section_titre(titre: str) -> str:
    """Return a formatted section title."""
    return f"\n{'=' * 60}\n  {titre}\n{'=' * 60}\n"


# ---------------------------------------------------------------------------
# Main report generator
# ---------------------------------------------------------------------------

def generer_rapport(
    gaz_twh: float = 114.0,
    config: Optional[EnergyModelConfig] = None,
) -> str:
    """
    Generate complete decision-maker report as formatted text.

    The report is structured, factual and in French. It presents
    the model results without advocacy, letting decision-makers
    draw their own conclusions.

    Args:
        gaz_twh: Annual gas backup in TWh.
        config: Model configuration (uses defaults if None).

    Returns:
        Complete formatted report as a single string.
    """
    if config is None:
        config = DEFAULT_CONFIG

    sections: list[str] = []

    # ---- Title ----
    sections.append(
        "=" * 60
        + "\n  RAPPORT DE SYNTHESE"
        + "\n  Modele de transition energetique - France"
        + "\n  Scenario : 500 GWc solaire + electrification"
        + "\n" + "=" * 60
    )

    # ---- 1. Resume executif ----
    sections.append(_section_titre("1. Resume executif"))
    sections.append(generer_resume_executif(gaz_twh))

    # ---- 2. Contexte et objectifs ----
    sections.append(_section_titre("2. Contexte et objectifs"))
    sections.append(
        "La France s'est engagee a atteindre la neutralite carbone d'ici 2050\n"
        "(Strategie Nationale Bas Carbone). Cela implique une electrification\n"
        "massive du chauffage et du transport, aujourd'hui largement dependants\n"
        "des energies fossiles.\n"
        "\n"
        "Ce modele evalue la faisabilite physique et economique d'un scenario\n"
        "base sur un deploiement massif de solaire photovoltaique (500 GWc),\n"
        "le maintien du parc nucleaire et hydraulique existant, et le recours\n"
        "au gaz naturel comme source de backup pour les periodes sans soleil.\n"
        "\n"
        "L'objectif est de fournir des ordres de grandeur fiables pour eclairer\n"
        "les choix publics, en rendant toutes les hypotheses explicites et\n"
        "verifiables."
    )

    # ---- 3. Hypotheses principales ----
    sections.append(_section_titre("3. Hypotheses principales"))
    sections.append(generer_tableau_hypotheses(config))
    sections.append(
        "\nNotes :\n"
        "- L'eolien n'est pas inclus (hypothese conservative).\n"
        "- Le stockage intersaisonnier (hydrogene, STEP) n'est pas modelise.\n"
        "- Les interconnexions europeennes ne sont pas prises en compte.\n"
        "- La flexibilite de la demande (effacement, V2G) est ignoree."
    )

    # ---- 4. Resultats cles ----
    sections.append(_section_titre("4. Resultats cles"))
    sections.append(generer_section_resultats(gaz_twh))

    # ---- 5. Chauffage ----
    sections.append(_section_titre("5. Chauffage"))
    sections.append(resume_chauffage())

    # ---- 5b. Transport ----
    sections.append(_section_titre("5b. Transport"))
    sections.append(resume_transport())

    # ---- 6. Bilan carbone ----
    sections.append(_section_titre("6. Bilan carbone"))
    sections.append(resume_emissions(gaz_twh))

    # ---- 7. Trajectoire ----
    sections.append(_section_titre("7. Trajectoire 2024-2050"))
    sections.append(resume_trajectoire())

    # ---- 8. Limites et incertitudes ----
    sections.append(_section_titre("8. Limites et incertitudes"))
    sections.append(
        "Ce modele presente plusieurs limites importantes :\n"
        "\n"
        "- Pas de stockage intersaisonnier : les batteries, le pompage-turbinage\n"
        "  (STEP) et l'hydrogene ne sont pas modelises. Leur inclusion reduirait\n"
        "  significativement le besoin en gaz de backup.\n"
        "\n"
        "- Pas d'eolien : le vent, complementaire du solaire (production hivernale\n"
        "  accrue), n'est pas pris en compte. Son ajout ameliorerait le bilan.\n"
        "\n"
        "- Pas d'interconnexions europeennes : les echanges transfrontaliers\n"
        "  permettraient un lissage supplementaire.\n"
        "\n"
        "- Pas de flexibilite de la demande : l'effacement, la recharge\n"
        "  intelligente des vehicules (V2G) et la gestion thermique des\n"
        "  batiments ne sont pas integres.\n"
        "\n"
        "- Granularite temporelle limitee : le modele utilise 12 mois x 5\n"
        "  creneaux horaires (60 periodes), sans variabilite intra-journaliere\n"
        "  fine ni evenements meteorologiques extremes.\n"
        "\n"
        "- COP des pompes a chaleur : le COP moyen utilise est conservateur.\n"
        "  Les pompes geothermiques offrent des performances superieures.\n"
        "\n"
        "Ces limites rendent les resultats conservateurs : le besoin reel\n"
        "en gaz de backup serait probablement inferieur aux estimations."
    )

    # ---- 9. Recommandations ----
    sections.append(_section_titre("9. Recommandations"))
    sections.append(
        "Sur la base des resultats du modele, les elements suivants meritent\n"
        "l'attention des decideurs :\n"
        "\n"
        "1. Faisabilite physique : le scenario 500 GWc solaire avec maintien\n"
        "   du nucleaire et de l'hydraulique couvre l'essentiel de la demande.\n"
        "   Le complement gaz (environ {gaz:.0f} TWh/an) reste significatif\n"
        "   mais represente une fraction limitee du mix.\n"
        "\n"
        "2. Reduction des emissions : la transition permet une reduction\n"
        "   estimee a environ {red:.0f} % des emissions nationales, principalement\n"
        "   grace a l'electrification du transport et du chauffage.\n"
        "\n"
        "3. Investissement : le deploiement solaire represente un investissement\n"
        "   cumule de l'ordre de {inv:.0f} Mds EUR sur la periode 2024-2050.\n"
        "   Les courbes d'apprentissage suggerent une baisse continue des couts.\n"
        "\n"
        "4. Axes d'amelioration : l'ajout d'eolien, de stockage intersaisonnier\n"
        "   et de flexibilite de la demande permettrait de reduire davantage\n"
        "   le recours au gaz de backup.\n"
        "\n"
        "5. Robustesse : les hypotheses sont deliberement conservatives.\n"
        "   Les resultats constituent donc une borne superieure du besoin\n"
        "   en gaz de backup.".format(
            gaz=gaz_twh,
            red=bilan_carbone(gaz_twh)["reduction_pct"],
            inv=_investissement_cumule(),
        )
    )

    # ---- Footer ----
    sections.append(
        "\n" + "=" * 60
        + "\n  Fin du rapport"
        + "\n  Modele v0.5 - Donnees sources documentees dans SOURCES.md"
        + "\n" + "=" * 60
    )

    return "\n".join(sections)
