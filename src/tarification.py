"""
Steady-state pricing model for the Energy Transition Model.

Models the financial equilibrium in the target scenario (cruise regime):
- Electricity tariff needed to cover all costs
- Revenue distribution among actors (producers, grid operator, state)
- Consumer cost comparison with current situation
- Financial flows between actors

This is Roland's step 5: "équilibrer le fonctionnement en vitesse de
croisière avec des prix pour tous les acteurs"

Sources:
- CRE: current electricity tariff structure
- RTE: grid costs
- EDF/ADEME: production cost references
"""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class TarificationConfig:
    """
    Steady-state pricing parameters.

    All costs are annualized in the target scenario (2050, 500 GWc solar).
    """

    # --- Production costs (annualized) ---

    # Solar PV LCOE (Levelized Cost of Energy)
    # CAPEX amortized over lifetime + O&M
    # Source: IRENA 2024 / learning curve projection
    # At 500 GWc, after learning: ~315 €/kW, 30y life, 15% avg CF
    # LCOE = CAPEX / (lifetime × CF × 8760h) + O&M
    solaire_lcoe_eur_mwh: float = 30.0

    # Nuclear LCOE (existing fleet, amortized)
    # Source: Cour des Comptes / EDF
    nucleaire_lcoe_eur_mwh: float = 50.0

    # Hydro LCOE (existing fleet)
    # Source: CRE
    hydro_lcoe_eur_mwh: float = 25.0

    # Gas backup LCOE (CCGT, low utilization factor increases cost)
    # Source: Market data, low CF (~20%) increases per-MWh cost
    gaz_lcoe_eur_mwh: float = 120.0

    # Battery storage cost per MWh cycled
    # Source: BNEF, after learning curve
    stockage_cout_eur_mwh: float = 50.0

    # --- Production volumes (TWh/year, target scenario) ---
    solaire_twh: float = 300.0
    nucleaire_twh: float = 400.0
    hydro_twh: float = 65.0
    gaz_twh: float = 114.0
    stockage_twh: float = 80.0  # Energy cycled through storage

    # --- Grid and system costs ---

    # Grid operation and maintenance (TURPE equivalent)
    # Source: CRE, scaled for higher distributed generation
    reseau_cout_annuel_eur_b: float = 15.0

    # Grid investment (reinforcement for solar integration)
    # Source: RTE Futurs Énergétiques 2050
    reseau_investissement_annuel_eur_b: float = 5.0

    # System services (frequency regulation, reserves)
    services_systeme_eur_b: float = 2.0

    # --- Taxes and policy costs ---

    # Current electricity taxes (TICFE/CSPE equivalent)
    # Source: CRE
    taxes_eur_mwh: float = 32.0

    # Renewable support costs (declining as solar becomes competitive)
    soutien_enr_eur_b: float = 1.0

    # --- Consumer reference ---

    # Current average retail electricity price (€/MWh = c€/kWh × 10)
    # Source: Eurostat France 2024 (household)
    prix_actuel_menage_eur_mwh: float = 230.0

    # Current average retail price (industrial)
    prix_actuel_industrie_eur_mwh: float = 130.0

    # Total electricity consumption (TWh/year, target scenario)
    # Source: consumption.py calculate_system_balance() -> ~729 TWh
    consommation_totale_twh: float = 729.0

    # Split between consumer types
    part_menages: float = 0.40  # 40% residential
    part_industrie: float = 0.35  # 35% industry
    part_tertiaire: float = 0.25  # 25% tertiary


def cout_production_annuel(config: Optional[TarificationConfig] = None) -> Dict[str, float]:
    """
    Calculate annual production costs by source.

    Args:
        config: Pricing configuration

    Returns:
        Dict with production costs in €B
    """
    if config is None:
        config = TarificationConfig()

    solaire = config.solaire_twh * config.solaire_lcoe_eur_mwh / 1000
    nucleaire = config.nucleaire_twh * config.nucleaire_lcoe_eur_mwh / 1000
    hydro = config.hydro_twh * config.hydro_lcoe_eur_mwh / 1000
    gaz = config.gaz_twh * config.gaz_lcoe_eur_mwh / 1000
    stockage = config.stockage_twh * config.stockage_cout_eur_mwh / 1000

    total = solaire + nucleaire + hydro + gaz + stockage

    return {
        'solaire_eur_b': solaire,
        'nucleaire_eur_b': nucleaire,
        'hydro_eur_b': hydro,
        'gaz_eur_b': gaz,
        'stockage_eur_b': stockage,
        'total_production_eur_b': total,
    }


def cout_systeme_annuel(config: Optional[TarificationConfig] = None) -> Dict[str, float]:
    """
    Calculate annual system costs (grid, services).

    Args:
        config: Pricing configuration

    Returns:
        Dict with system costs in €B
    """
    if config is None:
        config = TarificationConfig()

    reseau = config.reseau_cout_annuel_eur_b + config.reseau_investissement_annuel_eur_b
    services = config.services_systeme_eur_b
    soutien = config.soutien_enr_eur_b

    return {
        'reseau_eur_b': reseau,
        'services_systeme_eur_b': services,
        'soutien_enr_eur_b': soutien,
        'total_systeme_eur_b': reseau + services + soutien,
    }


def tarif_equilibre_eur_mwh(config: Optional[TarificationConfig] = None) -> Dict[str, float]:
    """
    Calculate the break-even electricity tariff.

    The tariff that covers all costs: production + system + taxes.

    Args:
        config: Pricing configuration

    Returns:
        Dict with tariff components in €/MWh
    """
    if config is None:
        config = TarificationConfig()

    prod = cout_production_annuel(config)
    sys = cout_systeme_annuel(config)
    conso_twh = config.consommation_totale_twh

    # Production component (€/MWh)
    composante_production = prod['total_production_eur_b'] * 1000 / conso_twh

    # Grid component
    composante_reseau = sys['reseau_eur_b'] * 1000 / conso_twh

    # Services and support
    composante_services = (sys['services_systeme_eur_b'] + sys['soutien_enr_eur_b']) * 1000 / conso_twh

    # Taxes
    composante_taxes = config.taxes_eur_mwh

    total_ht = composante_production + composante_reseau + composante_services
    total_ttc = total_ht + composante_taxes

    return {
        'composante_production_eur_mwh': composante_production,
        'composante_reseau_eur_mwh': composante_reseau,
        'composante_services_eur_mwh': composante_services,
        'total_ht_eur_mwh': total_ht,
        'composante_taxes_eur_mwh': composante_taxes,
        'total_ttc_eur_mwh': total_ttc,
    }


def flux_financiers(config: Optional[TarificationConfig] = None) -> Dict[str, float]:
    """
    Calculate annual financial flows between actors.

    Actors:
    - Consumers (ménages, industrie, tertiaire)
    - Producers (solaire, nucléaire, hydro, gaz)
    - Grid operator (RTE/Enedis)
    - State (taxes, support)

    Args:
        config: Pricing configuration

    Returns:
        Dict with annual flows in €B
    """
    if config is None:
        config = TarificationConfig()

    tarif = tarif_equilibre_eur_mwh(config)
    prod = cout_production_annuel(config)
    sys = cout_systeme_annuel(config)
    conso = config.consommation_totale_twh

    # Consumer payments (total revenue)
    revenus_totaux = conso * tarif['total_ttc_eur_mwh'] / 1000

    # Consumer breakdown
    revenus_menages = revenus_totaux * config.part_menages
    revenus_industrie = revenus_totaux * config.part_industrie
    revenus_tertiaire = revenus_totaux * config.part_tertiaire

    # Flows to actors
    vers_producteurs = prod['total_production_eur_b']
    vers_reseau = sys['reseau_eur_b']
    vers_services = sys['services_systeme_eur_b'] + sys['soutien_enr_eur_b']
    vers_etat = conso * config.taxes_eur_mwh / 1000

    return {
        # Revenue sources
        'revenus_totaux_eur_b': revenus_totaux,
        'revenus_menages_eur_b': revenus_menages,
        'revenus_industrie_eur_b': revenus_industrie,
        'revenus_tertiaire_eur_b': revenus_tertiaire,

        # Expenditure destinations
        'vers_producteurs_eur_b': vers_producteurs,
        'vers_reseau_eur_b': vers_reseau,
        'vers_services_eur_b': vers_services,
        'vers_etat_eur_b': vers_etat,

        # Balance check (should be ~0)
        'balance_eur_b': revenus_totaux - vers_producteurs - vers_reseau - vers_services - vers_etat,
    }


def comparaison_cout_consommateur(config: Optional[TarificationConfig] = None) -> Dict[str, float]:
    """
    Compare consumer costs: current vs transition scenario.

    Args:
        config: Pricing configuration

    Returns:
        Dict with cost comparison
    """
    if config is None:
        config = TarificationConfig()

    tarif = tarif_equilibre_eur_mwh(config)

    # Current annual electricity bill (households)
    # Average French household: ~4.7 MWh/year
    conso_menage_mwh = 4.7
    facture_actuelle = conso_menage_mwh * config.prix_actuel_menage_eur_mwh
    facture_transition = conso_menage_mwh * tarif['total_ttc_eur_mwh']

    # But heating electrification increases consumption
    # Average household with heat pump: ~7 MWh/year (heating adds ~2.3 MWh)
    conso_menage_electrifie_mwh = 7.0
    facture_electrifiee = conso_menage_electrifie_mwh * tarif['total_ttc_eur_mwh']

    # Current heating cost (gas/oil) that is eliminated
    # Source: ADEME, average gas heating cost ~1200 €/year
    cout_chauffage_fossile = 1200.0

    # Net household impact
    # Before: electricity bill + gas heating
    # After: higher electricity bill (includes heat pump heating), no gas
    cout_actuel_total = facture_actuelle + cout_chauffage_fossile
    cout_transition_total = facture_electrifiee

    # Industry comparison
    conso_industrie_mwh = 100.0  # Representative industrial consumer
    facture_industrie_actuelle = conso_industrie_mwh * config.prix_actuel_industrie_eur_mwh
    facture_industrie_transition = conso_industrie_mwh * tarif['total_ttc_eur_mwh']

    return {
        # Household
        'menage_conso_actuelle_mwh': conso_menage_mwh,
        'menage_conso_electrifiee_mwh': conso_menage_electrifie_mwh,
        'menage_facture_actuelle_eur': facture_actuelle,
        'menage_chauffage_fossile_eur': cout_chauffage_fossile,
        'menage_cout_actuel_total_eur': cout_actuel_total,
        'menage_facture_transition_eur': facture_electrifiee,
        'menage_economie_eur': cout_actuel_total - facture_electrifiee,
        'menage_economie_pct': (cout_actuel_total - facture_electrifiee) / cout_actuel_total * 100,

        # Industry
        'industrie_facture_actuelle_eur': facture_industrie_actuelle,
        'industrie_facture_transition_eur': facture_industrie_transition,
        'industrie_variation_pct': (facture_industrie_transition - facture_industrie_actuelle) / facture_industrie_actuelle * 100,

        # Tariff comparison
        'tarif_actuel_menage_eur_mwh': config.prix_actuel_menage_eur_mwh,
        'tarif_transition_eur_mwh': tarif['total_ttc_eur_mwh'],
        'tarif_variation_pct': (tarif['total_ttc_eur_mwh'] - config.prix_actuel_menage_eur_mwh) / config.prix_actuel_menage_eur_mwh * 100,
    }


def analyse_sensibilite_tarif(
    config: Optional[TarificationConfig] = None,
) -> Dict[str, Dict[str, float]]:
    """
    Sensitivity analysis: how tariff changes with key parameters.

    Tests ±20% variations on main cost drivers.

    Args:
        config: Base pricing configuration

    Returns:
        Dict mapping parameter names to their impact on tariff
    """
    if config is None:
        config = TarificationConfig()

    base_tarif = tarif_equilibre_eur_mwh(config)['total_ttc_eur_mwh']

    sensibilites = {}

    # Test each parameter
    params = [
        ('solaire_lcoe', 'solaire_lcoe_eur_mwh', config.solaire_lcoe_eur_mwh),
        ('nucleaire_lcoe', 'nucleaire_lcoe_eur_mwh', config.nucleaire_lcoe_eur_mwh),
        ('gaz_lcoe', 'gaz_lcoe_eur_mwh', config.gaz_lcoe_eur_mwh),
        ('reseau', 'reseau_cout_annuel_eur_b', config.reseau_cout_annuel_eur_b),
        ('gaz_volume', 'gaz_twh', config.gaz_twh),
    ]

    for name, attr, base_val in params:
        # +20%
        config_high = TarificationConfig()
        setattr(config_high, attr, base_val * 1.2)
        tarif_high = tarif_equilibre_eur_mwh(config_high)['total_ttc_eur_mwh']

        # -20%
        config_low = TarificationConfig()
        setattr(config_low, attr, base_val * 0.8)
        tarif_low = tarif_equilibre_eur_mwh(config_low)['total_ttc_eur_mwh']

        sensibilites[name] = {
            'base_eur_mwh': base_tarif,
            'high_eur_mwh': tarif_high,
            'low_eur_mwh': tarif_low,
            'impact_eur_mwh': (tarif_high - tarif_low) / 2,
            'impact_pct': (tarif_high - tarif_low) / 2 / base_tarif * 100,
        }

    return sensibilites


def resume_tarification(config: Optional[TarificationConfig] = None) -> str:
    """
    Generate human-readable pricing model summary.

    Args:
        config: Pricing configuration

    Returns:
        Formatted summary string
    """
    if config is None:
        config = TarificationConfig()

    prod = cout_production_annuel(config)
    sys = cout_systeme_annuel(config)
    tarif = tarif_equilibre_eur_mwh(config)
    flux = flux_financiers(config)
    comp = comparaison_cout_consommateur(config)
    sensib = analyse_sensibilite_tarif(config)

    lines = [
        "Modele de Tarification en Regime Permanent",
        "=" * 50,
        "",
        "COUTS DE PRODUCTION ANNUELS",
        f"  Solaire ({config.solaire_twh:.0f} TWh × {config.solaire_lcoe_eur_mwh:.0f} EUR/MWh):  {prod['solaire_eur_b']:>6.1f} EUR B",
        f"  Nucleaire ({config.nucleaire_twh:.0f} TWh × {config.nucleaire_lcoe_eur_mwh:.0f} EUR/MWh):{prod['nucleaire_eur_b']:>6.1f} EUR B",
        f"  Hydro ({config.hydro_twh:.0f} TWh × {config.hydro_lcoe_eur_mwh:.0f} EUR/MWh):       {prod['hydro_eur_b']:>6.1f} EUR B",
        f"  Gaz ({config.gaz_twh:.0f} TWh × {config.gaz_lcoe_eur_mwh:.0f} EUR/MWh):        {prod['gaz_eur_b']:>6.1f} EUR B",
        f"  Stockage ({config.stockage_twh:.0f} TWh × {config.stockage_cout_eur_mwh:.0f} EUR/MWh):  {prod['stockage_eur_b']:>6.1f} EUR B",
        f"  TOTAL PRODUCTION:                      {prod['total_production_eur_b']:>6.1f} EUR B",
        "",
        "COUTS SYSTEME",
        f"  Reseau (operation + investissement):    {sys['reseau_eur_b']:>6.1f} EUR B",
        f"  Services systeme:                       {sys['services_systeme_eur_b']:>6.1f} EUR B",
        f"  Soutien ENR:                            {sys['soutien_enr_eur_b']:>6.1f} EUR B",
        f"  TOTAL SYSTEME:                          {sys['total_systeme_eur_b']:>6.1f} EUR B",
        "",
        "TARIF D'EQUILIBRE",
        f"  Production:  {tarif['composante_production_eur_mwh']:>6.1f} EUR/MWh",
        f"  Reseau:      {tarif['composante_reseau_eur_mwh']:>6.1f} EUR/MWh",
        f"  Services:    {tarif['composante_services_eur_mwh']:>6.1f} EUR/MWh",
        f"  Sous-total HT:{tarif['total_ht_eur_mwh']:>5.1f} EUR/MWh",
        f"  Taxes:       {tarif['composante_taxes_eur_mwh']:>6.1f} EUR/MWh",
        f"  TOTAL TTC:   {tarif['total_ttc_eur_mwh']:>6.1f} EUR/MWh ({tarif['total_ttc_eur_mwh']/10:.1f} c/kWh)",
        "",
        "FLUX FINANCIERS ANNUELS",
        f"  Revenus totaux:       {flux['revenus_totaux_eur_b']:>6.1f} EUR B",
        f"    dont menages:       {flux['revenus_menages_eur_b']:>6.1f} EUR B ({config.part_menages*100:.0f}%)",
        f"    dont industrie:     {flux['revenus_industrie_eur_b']:>6.1f} EUR B ({config.part_industrie*100:.0f}%)",
        f"    dont tertiaire:     {flux['revenus_tertiaire_eur_b']:>6.1f} EUR B ({config.part_tertiaire*100:.0f}%)",
        f"  Vers producteurs:     {flux['vers_producteurs_eur_b']:>6.1f} EUR B",
        f"  Vers reseau:          {flux['vers_reseau_eur_b']:>6.1f} EUR B",
        f"  Vers Etat (taxes):    {flux['vers_etat_eur_b']:>6.1f} EUR B",
        f"  Balance:              {flux['balance_eur_b']:>6.1f} EUR B (ecart)",
        "",
        "IMPACT CONSOMMATEUR",
        f"  Menage (chauffage fossile actuel: {comp['menage_chauffage_fossile_eur']:.0f} EUR/an):",
        f"    Actuel (elec + gaz):   {comp['menage_cout_actuel_total_eur']:>8.0f} EUR/an",
        f"    Transition (tout elec):{comp['menage_facture_transition_eur']:>8.0f} EUR/an",
        f"    Economie:              {comp['menage_economie_eur']:>8.0f} EUR/an ({comp['menage_economie_pct']:+.0f}%)",
        f"  Industrie:",
        f"    Variation tarif:       {comp['industrie_variation_pct']:>+7.0f}%",
        "",
        "SENSIBILITE DU TARIF (variation +/-20%)",
    ]

    for name, data in sensib.items():
        lines.append(
            f"  {name:<20} impact: {data['impact_eur_mwh']:>+5.1f} EUR/MWh ({data['impact_pct']:>+4.1f}%)"
        )

    return '\n'.join(lines)
