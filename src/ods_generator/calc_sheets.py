"""Calculation sheet generators for the ODS model.

Each sheet contains ODF formulas (of:=...) that reference the parametres
sheet, making every calculation traceable back to tuneable knobs.
Pre-computed Python values are stored alongside formulas for instant display.

Sheets generated:
    calc_industrie   -- Industrial sector flat kW demand
    calc_tertiaire   -- Tertiary sector flat kW demand
    calc_transport   -- Transport sector kW demand per time slot
    calc_agriculture -- Agriculture sector kW demand per month
    calc_chauffage   -- Heating sector kW demand (60 rows: 12 months x 5 slots)
"""

from .writer import ODSWriter
from .knob_registry import get_param_ref, PARAM_ROWS


# -----------------------------------------------------------------------
# Constants shared across sheets
# -----------------------------------------------------------------------

MOIS_ORDRE = (
    'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
    'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre',
)

PLAGES = ('8h-13h', '13h-18h', '18h-20h', '20h-23h', '23h-8h')

DUREES = {
    '8h-13h': 5.0,
    '13h-18h': 5.0,
    '18h-20h': 2.0,
    '20h-23h': 3.0,
    '23h-8h': 9.0,
}

JOURS_PAR_MOIS = 30  # Default model assumption


# =======================================================================
# Sheet 1: calc_industrie
# =======================================================================

def add_calc_industrie_sheet(writer: ODSWriter, db, industrie_config=None):
    """Add industry sector calculation sheet.

    Layout:
        Row 1: title
        Row 2: header
        Row 3: flat_kw (single formula, referenced by synthesis as [calc_industrie.B3])
        Row 4: explanation text

    Formula logic (matching bilan_industrie in secteurs.py):
        ht_elec  = chaleur_haute_temp_twh * haute_temp_electrifiable * haute_temp_efficacite
        mt_elec  = chaleur_moyenne_temp_twh * moyenne_temp_electrifiable / moyenne_temp_cop
        bt_elec  = chaleur_basse_temp_twh * basse_temp_electrifiable / basse_temp_cop
        total_elec_brut = ht_elec + mt_elec + bt_elec + force_motrice + electrochimie + autres
        total_elec = total_elec_brut * (1 - gain_efficacite_fraction)
        flat_kw = total_elec * 1e9 / 8760
    """
    from src.secteurs import bilan_industrie, IndustrieConfig

    cfg = industrie_config or IndustrieConfig()
    bilan = bilan_industrie(cfg)
    total_elec_twh = bilan['total_elec_twh']
    flat_kw = total_elec_twh * 1e9 / 8760.0

    # Parameter references
    ref_ht_twh = get_param_ref('ind_chaleur_haute_temp_twh')
    ref_ht_elec = get_param_ref('ind_haute_temp_electrifiable')
    ref_ht_eff = get_param_ref('ind_haute_temp_efficacite')
    ref_mt_twh = get_param_ref('ind_chaleur_moyenne_temp_twh')
    ref_mt_elec = get_param_ref('ind_moyenne_temp_electrifiable')
    ref_mt_cop = get_param_ref('ind_moyenne_temp_cop')
    ref_bt_twh = get_param_ref('ind_chaleur_basse_temp_twh')
    ref_bt_elec = get_param_ref('ind_basse_temp_electrifiable')
    ref_bt_cop = get_param_ref('ind_basse_temp_cop')
    ref_force = get_param_ref('ind_force_motrice_twh')
    ref_electrochimie = get_param_ref('ind_electrochimie_twh')
    ref_autres = get_param_ref('ind_autres_twh')
    ref_gain = get_param_ref('ind_gain_efficacite_fraction')

    # ODF formula for flat_kw:
    # (ht*elec*eff + mt*elec/cop + bt*elec/cop + force + electrochimie + autres) * (1-gain) * 1e9/8760
    formula_flat_kw = (
        f"of:=("
        f"{ref_ht_twh}*{ref_ht_elec}*{ref_ht_eff}"
        f"+{ref_mt_twh}*{ref_mt_elec}/{ref_mt_cop}"
        f"+{ref_bt_twh}*{ref_bt_elec}/{ref_bt_cop}"
        f"+{ref_force}"
        f"+{ref_electrochimie}"
        f"+{ref_autres}"
        f")*(1-{ref_gain})*1000000000/8760"
    )

    table = writer.add_formula_sheet(
        'calc_industrie',
        ['Resultat', 'Valeur (kW)'],
        title='Calcul industrie -- demande electrique constante',
    )

    # Row 3: flat_kw
    writer.add_formula_row(table, [
        {'value': 'Industrie flat_kw'},
        {'value': flat_kw, 'formula': formula_flat_kw},
    ])

    # Row 4: explanation
    writer.add_formula_row(table, [
        {'value': (
            'Formule: (HT*elec*eff + MT*elec/COP + BT*elec/COP '
            '+ force_motrice + electrochimie + autres) * (1-gain) * 1e9/8760'
        )},
        {'value': ''},
    ])


# =======================================================================
# Sheet 2: calc_tertiaire
# =======================================================================

def add_calc_tertiaire_sheet(writer: ODSWriter, db, tertiaire_config=None):
    """Add tertiary sector calculation sheet.

    Layout:
        Row 1: title
        Row 2: header
        Row 3: flat_kw (single formula, referenced by synthesis as [calc_tertiaire.B3])
        Row 4: explanation text

    Formula logic (matching bilan_tertiaire in secteurs.py):
        chauffage_apres_renovation = chauffage_twh * (1 - renovation_gain_chauffage)
        chauffage_fossile_pac = chauffage_apres_renovation * chauffage_fossile_fraction / chauffage_pac_cop
        chauffage_elec_existant = chauffage_apres_renovation * (1 - chauffage_fossile_fraction)
        chauffage_total = chauffage_fossile_pac + chauffage_elec_existant
        climatisation = climatisation_twh * (1 - climatisation_gain)
        eclairage = eclairage_twh * (1 - eclairage_gain_led)
        total_elec = chauffage_total + climatisation + eclairage + elec_specifique + eau_chaude + autres
        flat_kw = total_elec * 1e9 / 8760
    """
    from src.secteurs import bilan_tertiaire, TertiaireConfig

    cfg = tertiaire_config or TertiaireConfig()
    bilan = bilan_tertiaire(cfg)
    total_elec_twh = bilan['total_elec_twh']
    flat_kw = total_elec_twh * 1e9 / 8760.0

    # Parameter references
    ref_chauffage = get_param_ref('tert_chauffage_twh')
    ref_clim = get_param_ref('tert_climatisation_twh')
    ref_eclairage = get_param_ref('tert_eclairage_twh')
    ref_elec_spec = get_param_ref('tert_electricite_specifique_twh')
    ref_eau_chaude = get_param_ref('tert_eau_chaude_twh')
    ref_autres = get_param_ref('tert_autres_twh')
    ref_fossile_frac = get_param_ref('tert_chauffage_fossile_fraction')
    ref_pac_cop = get_param_ref('tert_chauffage_pac_cop')
    ref_gain_led = get_param_ref('tert_eclairage_gain_led')
    ref_gain_renov = get_param_ref('tert_renovation_gain_chauffage')
    ref_gain_clim = get_param_ref('tert_climatisation_gain')

    # ODF formula for flat_kw.
    # chauffage_total = chauffage*(1-renov) * fossile_frac / cop + chauffage*(1-renov) * (1-fossile_frac)
    #                 = chauffage*(1-renov) * (fossile_frac/cop + 1 - fossile_frac)
    # total_elec = chauffage_total + clim*(1-gain_clim) + eclairage*(1-gain_led) + elec_spec + eau_chaude + autres
    # flat_kw = total_elec * 1e9 / 8760
    formula_flat_kw = (
        f"of:=("
        # chauffage_total = chauffage*(1-renov)*(fossile/cop + (1-fossile))
        f"{ref_chauffage}*(1-{ref_gain_renov})*"
        f"({ref_fossile_frac}/{ref_pac_cop}+(1-{ref_fossile_frac}))"
        # + climatisation after efficiency gain
        f"+{ref_clim}*(1-{ref_gain_clim})"
        # + eclairage after LED gain
        f"+{ref_eclairage}*(1-{ref_gain_led})"
        # + unchanged sectors
        f"+{ref_elec_spec}"
        f"+{ref_eau_chaude}"
        f"+{ref_autres}"
        f")*1000000000/8760"
    )

    table = writer.add_formula_sheet(
        'calc_tertiaire',
        ['Resultat', 'Valeur (kW)'],
        title='Calcul tertiaire -- demande electrique constante',
    )

    # Row 3: flat_kw
    writer.add_formula_row(table, [
        {'value': 'Tertiaire flat_kw'},
        {'value': flat_kw, 'formula': formula_flat_kw},
    ])

    # Row 4: explanation
    writer.add_formula_row(table, [
        {'value': (
            'Formule: (chauffage*(1-renov)*(fossile/COP + 1-fossile) '
            '+ clim*(1-gain) + eclairage*(1-LED) + elec_spec + eau_chaude + autres) * 1e9/8760'
        )},
        {'value': ''},
    ])


# =======================================================================
# Sheet 3: calc_transport
# =======================================================================

def add_calc_transport_sheet(writer: ODSWriter, db, transport_config=None):
    """Add transport sector calculation sheet.

    Layout:
        Row 1: title
        Row 2: header ['Calcul', 'Valeur (TWh ou kW)']
        Row 3: direct_elec_twh (road + maritime + fluvial electric TWh)
        Row 4: rail_elec_twh
        Row 5: saf_elec_twh
        Row 6: rail_saf_flat_kw = (rail_elec + saf_elec) * 1e9 / 8760
        Row 7: slot 8h-13h   transport_kw  (synthesis references [calc_transport.B7])
        Row 8: slot 13h-18h  transport_kw  (synthesis references [calc_transport.B8])
        Row 9: slot 18h-20h  transport_kw
        Row 10: slot 20h-23h transport_kw
        Row 11: slot 23h-8h  transport_kw

    BUT: synthesis_sheet.py references [calc_transport.B{3+plage_idx}] which maps to:
        plage_idx=0 -> row 3  (8h-13h)
        plage_idx=1 -> row 4  (13h-18h)
        plage_idx=2 -> row 5  (18h-20h)
        plage_idx=3 -> row 6  (20h-23h)
        plage_idx=4 -> row 7  (23h-8h)

    So the 5 slot rows must be at rows 3-7. We put intermediate calculations
    in rows 8+ (after the slot rows) so synthesis references work correctly.

    Formula logic (matching consommation_electrifiee_twh + demande_recharge_par_plage):
        direct_elec_twh = routier_passagers_elec + routier_fret_elec + maritime_elec + fluvial_elec
        For each slot:
            charging_twh = direct_elec_twh * profil_recharge[slot]
            charging_kw = charging_twh * 1e9 / (duree * 365)
        rail_elec_twh = rail_total * elec_frac + rail_total*(1-elec_frac)*diesel_elec_frac*eff_elec
                        + rail_total*(1-elec_frac)*(1-diesel_elec_frac)
        saf_elec_twh = (avdom*(1-report_tgv) + av_intl) * saf_fraction * saf_facteur_elec
        rail_saf_kw = (rail_elec + saf_elec) * 1e9 / 8760
        transport_kw[slot] = charging_kw[slot] + rail_saf_kw
    """
    from src.transport import (
        consommation_electrifiee_twh, demande_recharge_par_plage, TransportConfig,
    )

    cfg = transport_config or TransportConfig()
    electrifie = consommation_electrifiee_twh(cfg)

    # Pre-compute values
    direct_elec_twh = (
        electrifie['routier_passagers_elec_twh']
        + electrifie['routier_fret_elec_twh']
        + electrifie['maritime_elec_twh']
        + electrifie['fluvial_elec_twh']
    )
    rail_elec_twh = electrifie['rail_elec_twh']
    saf_elec_twh = electrifie['aviation_elec_saf_twh']
    rail_saf_kw = (rail_elec_twh + saf_elec_twh) * 1e9 / 8760.0

    # Parameter references -- road passenger
    ref_voit_twh = get_param_ref('tr_voitures_twh')
    ref_voit_fac = get_param_ref('tr_voitures_facteur_elec')
    ref_2r_twh = get_param_ref('tr_deux_roues_twh')
    ref_2r_fac = get_param_ref('tr_deux_roues_facteur_elec')
    ref_bus_twh = get_param_ref('tr_bus_cars_twh')
    ref_bus_fac = get_param_ref('tr_bus_facteur_elec')
    ref_sobriete = get_param_ref('tr_gain_sobriete_fraction')
    ref_report = get_param_ref('tr_report_modal_fraction')

    # Road freight
    ref_pl_twh = get_param_ref('tr_poids_lourds_twh')
    ref_pl_bat_frac = get_param_ref('tr_pl_batterie_fraction')
    ref_pl_bat_fact = get_param_ref('tr_pl_batterie_facteur')
    ref_pl_h2_frac = get_param_ref('tr_pl_hydrogene_fraction')
    ref_pl_h2_fact = get_param_ref('tr_pl_hydrogene_facteur')
    ref_vul_twh = get_param_ref('tr_vul_twh')
    ref_vul_fac = get_param_ref('tr_vul_facteur_elec')
    ref_vul_elec_frac = get_param_ref('tr_vul_electrifiable_fraction')

    # Maritime / fluvial
    ref_mar_twh = get_param_ref('tr_maritime_twh')
    ref_mar_elec_frac = get_param_ref('tr_maritime_elec_fraction')
    ref_mar_elec_fact = get_param_ref('tr_maritime_elec_facteur')
    ref_flu_twh = get_param_ref('tr_fluvial_twh')
    ref_flu_elec_frac = get_param_ref('tr_fluvial_elec_fraction')
    ref_flu_elec_fact = get_param_ref('tr_fluvial_elec_facteur')

    # Rail
    ref_rail_twh = get_param_ref('tr_rail_total_twh')
    ref_rail_elec_frac = get_param_ref('tr_rail_electrique_fraction')
    ref_rail_diesel_elec = get_param_ref('tr_rail_diesel_elec_fraction')
    ref_rail_eff_elec = get_param_ref('tr_rail_efficacite_elec')

    # Aviation
    ref_av_dom_twh = get_param_ref('tr_aviation_domestique_twh')
    ref_av_int_twh = get_param_ref('tr_aviation_international_twh')
    ref_av_report_tgv = get_param_ref('tr_aviation_report_tgv_fraction')
    ref_av_saf_frac = get_param_ref('tr_aviation_saf_fraction')
    ref_av_saf_fact = get_param_ref('tr_aviation_saf_facteur_elec')

    # Charging profile
    ref_profil = {
        '8h-13h': get_param_ref('tr_profil_8h13h'),
        '13h-18h': get_param_ref('tr_profil_13h18h'),
        '18h-20h': get_param_ref('tr_profil_18h20h'),
        '20h-23h': get_param_ref('tr_profil_20h23h'),
        '23h-8h': get_param_ref('tr_profil_23h8h'),
    }

    # Build the direct_elec_twh formula (road + maritime + fluvial)
    # voitures_elec = voitures_twh * (1-sobriete) * (1-report) * voitures_facteur
    # deux_roues_elec = deux_roues_twh * deux_roues_facteur
    # bus_elec = bus_twh * bus_facteur
    # pl_bat = pl_twh * pl_bat_frac * pl_bat_fact
    # pl_h2 = pl_twh * pl_h2_frac * pl_h2_fact
    # vul_elec = vul_twh * vul_elec_frac * vul_fac
    # maritime_elec = maritime_twh * maritime_elec_frac * maritime_elec_fact
    # fluvial_elec = fluvial_twh * fluvial_elec_frac * fluvial_elec_fact
    formula_direct_elec = (
        f"{ref_voit_twh}*(1-{ref_sobriete})*(1-{ref_report})*{ref_voit_fac}"
        f"+{ref_2r_twh}*{ref_2r_fac}"
        f"+{ref_bus_twh}*{ref_bus_fac}"
        f"+{ref_pl_twh}*{ref_pl_bat_frac}*{ref_pl_bat_fact}"
        f"+{ref_pl_twh}*{ref_pl_h2_frac}*{ref_pl_h2_fact}"
        f"+{ref_vul_twh}*{ref_vul_elec_frac}*{ref_vul_fac}"
        f"+{ref_mar_twh}*{ref_mar_elec_frac}*{ref_mar_elec_fact}"
        f"+{ref_flu_twh}*{ref_flu_elec_frac}*{ref_flu_elec_fact}"
    )

    # Rail formula:
    # rail_deja_elec = rail_total * rail_elec_frac
    # rail_diesel_elec = rail_total * (1-rail_elec_frac) * diesel_elec_frac * eff_elec
    # rail_diesel_restant = rail_total * (1-rail_elec_frac) * (1-diesel_elec_frac)
    # rail_elec = rail_deja_elec + rail_diesel_elec + rail_diesel_restant
    formula_rail_elec = (
        f"{ref_rail_twh}*{ref_rail_elec_frac}"
        f"+{ref_rail_twh}*(1-{ref_rail_elec_frac})*{ref_rail_diesel_elec}*{ref_rail_eff_elec}"
        f"+{ref_rail_twh}*(1-{ref_rail_elec_frac})*(1-{ref_rail_diesel_elec})"
    )

    # SAF formula:
    # saf_elec = (avdom*(1-report_tgv) + av_intl) * saf_fraction * saf_facteur_elec
    formula_saf_elec = (
        f"({ref_av_dom_twh}*(1-{ref_av_report_tgv})+{ref_av_int_twh})"
        f"*{ref_av_saf_frac}*{ref_av_saf_fact}"
    )

    # ---------------------------------------------------------------
    # The synthesis references rows 3-7 for the 5 slot values.
    # So we put the per-slot transport_kw rows first (rows 3-7),
    # then the intermediate values in rows 8-11 for reference.
    # ---------------------------------------------------------------

    table = writer.add_formula_sheet(
        'calc_transport',
        ['Calcul', 'Valeur (TWh ou kW)'],
        title='Calcul transport -- demande electrique par plage',
    )

    # Rows 3-7: per-slot transport_kw (these are referenced by synthesis)
    # transport_kw[slot] = direct_elec_twh * profil[slot] * 1e9 / (duree * 365) + rail_saf_kw
    # rail_saf_kw = (rail_elec + saf_elec) * 1e9 / 8760
    # Combined into a single formula per slot:
    for plage in PLAGES:
        duree = DUREES[plage]
        ref_p = ref_profil[plage]

        slot_twh = demande_recharge_par_plage(plage, cfg)
        charging_kw = slot_twh * 1e9 / (duree * 365.0)
        transport_kw = charging_kw + rail_saf_kw
        precomputed = transport_kw

        # Formula: (direct_elec) * profil * 1e9 / (duree*365) + (rail+saf) * 1e9 / 8760
        formula = (
            f"of:=({formula_direct_elec})*{ref_p}*1000000000/{duree * 365.0:.1f}"
            f"+({formula_rail_elec}+{formula_saf_elec})*1000000000/8760"
        )

        writer.add_formula_row(table, [
            {'value': f'Transport {plage} (kW)'},
            {'value': precomputed, 'formula': formula},
        ])

    # Rows 8-11: intermediate values for auditability
    # Row 8: direct_elec_twh
    writer.add_formula_row(table, [
        {'value': 'direct_elec_twh (route+maritime+fluvial)'},
        {'value': direct_elec_twh, 'formula': f"of:={formula_direct_elec}"},
    ])

    # Row 9: rail_elec_twh
    writer.add_formula_row(table, [
        {'value': 'rail_elec_twh'},
        {'value': rail_elec_twh, 'formula': f"of:={formula_rail_elec}"},
    ])

    # Row 10: saf_elec_twh
    writer.add_formula_row(table, [
        {'value': 'saf_elec_twh (aviation SAF)'},
        {'value': saf_elec_twh, 'formula': f"of:={formula_saf_elec}"},
    ])

    # Row 11: rail_saf_flat_kw
    writer.add_formula_row(table, [
        {'value': 'rail_saf_flat_kw'},
        {
            'value': rail_saf_kw,
            'formula': f"of:=([.B9]+[.B10])*1000000000/8760",
        },
    ])


# =======================================================================
# Sheet 4: calc_agriculture
# =======================================================================

def add_calc_agriculture_sheet(writer: ODSWriter, db, agriculture_config=None):
    """Add agriculture sector calculation sheet.

    Layout:
        Row 1: title
        Row 2: header ['Calcul', 'Valeur']
        Rows 3-14: 12 monthly kW values (synthesis references [calc_agriculture.B{3+mois_idx}])

    Formula logic (matching consommation_mensuelle_twh + kW conversion):
        total_elec_twh = machinisme * elec_frac * eff_elec
                       + serres * pac_frac / pac_cop + serres * (1-pac_frac)
                       + irrigation + elevage + autres
        monthly_kw = total_elec_twh * profil[mois] / sum_profil * 1e9 / (24 * jours_par_mois)
    """
    from src.agriculture import (
        consommation_electrifiee_twh as agri_electrifiee_twh,
        consommation_mensuelle_twh as agri_mensuelle_twh,
        AgricultureConfig,
    )

    cfg = agriculture_config or AgricultureConfig()
    elec = agri_electrifiee_twh(cfg)
    total_elec_twh = elec['total_elec_twh']

    # Parameter references
    ref_mach_twh = get_param_ref('agri_machinisme_twh')
    ref_mach_frac = get_param_ref('agri_machinisme_elec_fraction')
    ref_mach_eff = get_param_ref('agri_machinisme_eff_elec')
    ref_serres_twh = get_param_ref('agri_serres_twh')
    ref_serres_pac_frac = get_param_ref('agri_serres_pac_fraction')
    ref_serres_pac_cop = get_param_ref('agri_serres_pac_cop')
    ref_irrigation = get_param_ref('agri_irrigation_twh')
    ref_elevage = get_param_ref('agri_elevage_twh')
    ref_autres = get_param_ref('agri_autres_twh')
    ref_jours = get_param_ref('jours_par_mois')

    # Monthly profile references
    profil_refs = {
        'Janvier': get_param_ref('agri_profil_janvier'),
        'Février': get_param_ref('agri_profil_fevrier'),
        'Mars': get_param_ref('agri_profil_mars'),
        'Avril': get_param_ref('agri_profil_avril'),
        'Mai': get_param_ref('agri_profil_mai'),
        'Juin': get_param_ref('agri_profil_juin'),
        'Juillet': get_param_ref('agri_profil_juillet'),
        'Août': get_param_ref('agri_profil_aout'),
        'Septembre': get_param_ref('agri_profil_septembre'),
        'Octobre': get_param_ref('agri_profil_octobre'),
        'Novembre': get_param_ref('agri_profil_novembre'),
        'Décembre': get_param_ref('agri_profil_decembre'),
    }

    # total_elec formula:
    # machinisme * elec_frac * eff_elec + serres * pac_frac / cop + serres * (1-pac_frac) + irrig + elevage + autres
    formula_total_elec = (
        f"{ref_mach_twh}*{ref_mach_frac}*{ref_mach_eff}"
        f"+{ref_serres_twh}*{ref_serres_pac_frac}/{ref_serres_pac_cop}"
        f"+{ref_serres_twh}*(1-{ref_serres_pac_frac})"
        f"+{ref_irrigation}"
        f"+{ref_elevage}"
        f"+{ref_autres}"
    )

    # sum_profil formula: sum of all 12 monthly coefficients
    all_profil_refs = [profil_refs[m] for m in MOIS_ORDRE]
    formula_sum_profil = "+".join(all_profil_refs)

    table = writer.add_formula_sheet(
        'calc_agriculture',
        ['Calcul', 'Valeur'],
        title='Calcul agriculture -- demande electrique par mois',
    )

    # Rows 3-14: one per month
    for mois in MOIS_ORDRE:
        ref_profil_mois = profil_refs[mois]

        # Pre-compute
        monthly_twh = agri_mensuelle_twh(mois, cfg)
        monthly_kw = monthly_twh * 1e9 / (24.0 * JOURS_PAR_MOIS)

        # Formula: total_elec * profil_mois / sum_profil * 1e9 / (24 * jours_par_mois)
        formula = (
            f"of:=({formula_total_elec})"
            f"*{ref_profil_mois}"
            f"/({formula_sum_profil})"
            f"*1000000000/(24*{ref_jours})"
        )

        writer.add_formula_row(table, [
            {'value': f'Agriculture {mois} (kW)'},
            {'value': monthly_kw, 'formula': formula},
        ])


# =======================================================================
# Sheet 5: calc_chauffage
# =======================================================================

def _build_cop_formula(t_cell_ref):
    """Build a nested IF ODF formula for COP interpolation.

    Replicates the Python interpoler_cop() function as an ODF formula.
    Uses the COP(T) parametres references from the knob registry.

    COP table from parametres:
        -15C -> cop_t_m15  (1.5)
        -10C -> cop_t_m10  (1.8)
         -5C -> cop_t_m5   (2.1)
          0C -> cop_t_0    (2.5)
          5C -> cop_t_5    (3.0)
         10C -> cop_t_10   (3.5)
         15C -> cop_t_15   (4.0)

    Linear interpolation between breakpoints.  Clamped at boundaries.

    Args:
        t_cell_ref: ODF cell reference for temperature, e.g. "[.C5]"

    Returns:
        ODF formula string (without the "of:=" prefix)
    """
    ref_cop_m15 = get_param_ref('cop_t_m15')
    ref_cop_m10 = get_param_ref('cop_t_m10')
    ref_cop_m5 = get_param_ref('cop_t_m5')
    ref_cop_0 = get_param_ref('cop_t_0')
    ref_cop_5 = get_param_ref('cop_t_5')
    ref_cop_10 = get_param_ref('cop_t_10')
    ref_cop_15 = get_param_ref('cop_t_15')

    T = t_cell_ref

    # Linear interpolation formula between two breakpoints:
    # cop_low + (T - T_low) / (T_high - T_low) * (cop_high - cop_low)
    # Since breakpoints are 5C apart, (T_high - T_low) = 5 always.

    # Segment -15 to -10: cop_m15 + (T+15)/5 * (cop_m10 - cop_m15)
    seg_m15_m10 = f"{ref_cop_m15}+({T}+15)/5*({ref_cop_m10}-{ref_cop_m15})"

    # Segment -10 to -5: cop_m10 + (T+10)/5 * (cop_m5 - cop_m10)
    seg_m10_m5 = f"{ref_cop_m10}+({T}+10)/5*({ref_cop_m5}-{ref_cop_m10})"

    # Segment -5 to 0: cop_m5 + (T+5)/5 * (cop_0 - cop_m5)
    seg_m5_0 = f"{ref_cop_m5}+({T}+5)/5*({ref_cop_0}-{ref_cop_m5})"

    # Segment 0 to 5: cop_0 + T/5 * (cop_5 - cop_0)
    seg_0_5 = f"{ref_cop_0}+{T}/5*({ref_cop_5}-{ref_cop_0})"

    # Segment 5 to 10: cop_5 + (T-5)/5 * (cop_10 - cop_5)
    seg_5_10 = f"{ref_cop_5}+({T}-5)/5*({ref_cop_10}-{ref_cop_5})"

    # Segment 10 to 15: cop_10 + (T-10)/5 * (cop_15 - cop_10)
    seg_10_15 = f"{ref_cop_10}+({T}-10)/5*({ref_cop_15}-{ref_cop_10})"

    # Build nested IFs from coldest to warmest:
    # IF(T<=-15; cop_m15;
    #   IF(T<=-10; seg_m15_m10;
    #     IF(T<=-5; seg_m10_m5;
    #       IF(T<=0; seg_m5_0;
    #         IF(T<=5; seg_0_5;
    #           IF(T<=10; seg_5_10;
    #             IF(T<=15; seg_10_15;
    #               cop_15)))))))
    cop_formula = (
        f"IF({T}<=-15;{ref_cop_m15};"
        f"IF({T}<=-10;{seg_m15_m10};"
        f"IF({T}<=-5;{seg_m10_m5};"
        f"IF({T}<=0;{seg_m5_0};"
        f"IF({T}<=5;{seg_0_5};"
        f"IF({T}<=10;{seg_5_10};"
        f"IF({T}<=15;{seg_10_15};"
        f"{ref_cop_15})))))))"
    )

    return cop_formula


def add_calc_chauffage_sheet(writer: ODSWriter, db, heating_config=None):
    """Add heating sector calculation sheet.

    Layout:
        Row 1: title
        Row 2: header (8 columns A-H)
        Rows 3-62: 60 data rows (12 months x 5 time slots)

    Column layout:
        A: Mois
        B: Plage
        C: T_ext (reference to parametres)
        D: COP(T) formula (nested IF interpolation)
        E: Volume = surface * hauteur (formula)
        F: coeff_plage (reference to parametres)
        G: delta_T = MAX(0, T_int - T_ext) (formula)
        H: besoin_electrique_kw = G_coeff * Volume * delta_T / COP * N_maisons * coeff / 1000
           (synthesis references [calc_chauffage.H{r}])

    Formula logic (matching besoin_national_chauffage_kw in heating.py):
        P = G * V * max(0, T_int - T_ext) / COP(T_ext) * N_maisons * coeff_plage / 1000
    """
    from src.heating import (
        besoin_national_chauffage_kw, interpoler_cop, HeatingConfig,
        COEFFICIENTS_PLAGE,
    )

    cfg = heating_config or HeatingConfig()

    # Parameter references
    ref_surface = get_param_ref('chauf_surface_moyenne_m2')
    ref_hauteur = get_param_ref('chauf_hauteur_plafond_m')
    ref_g = get_param_ref('chauf_coefficient_g')
    ref_t_int = get_param_ref('chauf_temperature_int')
    ref_n_maisons = get_param_ref('nombre_maisons')

    # Temperature references per month
    temp_refs = {
        'Janvier': get_param_ref('temp_ext_janvier'),
        'Février': get_param_ref('temp_ext_fevrier'),
        'Mars': get_param_ref('temp_ext_mars'),
        'Avril': get_param_ref('temp_ext_avril'),
        'Mai': get_param_ref('temp_ext_mai'),
        'Juin': get_param_ref('temp_ext_juin'),
        'Juillet': get_param_ref('temp_ext_juillet'),
        'Août': get_param_ref('temp_ext_aout'),
        'Septembre': get_param_ref('temp_ext_septembre'),
        'Octobre': get_param_ref('temp_ext_octobre'),
        'Novembre': get_param_ref('temp_ext_novembre'),
        'Décembre': get_param_ref('temp_ext_decembre'),
    }

    # Coefficient plage references
    coeff_plage_refs = {
        '8h-13h': get_param_ref('coeff_plage_8h13h'),
        '13h-18h': get_param_ref('coeff_plage_13h18h'),
        '18h-20h': get_param_ref('coeff_plage_18h20h'),
        '20h-23h': get_param_ref('coeff_plage_20h23h'),
        '23h-8h': get_param_ref('coeff_plage_23h8h'),
    }

    headers = [
        'Mois',                    # A
        'Plage',                   # B
        'T_ext (C)',               # C
        'COP(T)',                  # D
        'Volume (m3)',             # E
        'Coeff plage',             # F
        'Delta T (C)',             # G
        'Besoin electrique (kW)',  # H
    ]

    table = writer.add_formula_sheet(
        'calc_chauffage',
        headers,
        title='Calcul chauffage -- modele Roland, COP variable',
    )

    # Data rows 3-62 (60 rows: 12 months x 5 time slots)
    row_num = 3
    for mois in MOIS_ORDRE:
        t_ext = cfg.temperatures_exterieures.get(mois, 10.0)
        cop_value = interpoler_cop(t_ext, cfg.cop_par_temperature) if cfg.avec_pompe_a_chaleur else 1.0
        volume = cfg.volume_moyen_m3

        ref_temp_mois = temp_refs[mois]

        for plage in PLAGES:
            coeff_plage = COEFFICIENTS_PLAGE.get(plage, 1.0)
            ref_coeff = coeff_plage_refs[plage]

            # Pre-compute
            p_kw = besoin_national_chauffage_kw(cfg, mois, plage)

            r = row_num

            # C: T_ext formula (reference to parametres)
            formula_t_ext = f"of:={ref_temp_mois}"

            # D: COP(T) formula (nested IF interpolation on T_ext cell)
            cop_formula_body = _build_cop_formula(f"[.C{r}]")
            formula_cop = f"of:={cop_formula_body}"

            # E: Volume = surface * hauteur
            formula_volume = f"of:={ref_surface}*{ref_hauteur}"

            # F: coeff_plage (reference to parametres)
            formula_coeff = f"of:={ref_coeff}"

            # G: delta_T = MAX(0, T_int - T_ext)
            formula_delta_t = f"of:=MAX(0;{ref_t_int}-[.C{r}])"

            # H: besoin_electrique_kw = G * Volume * delta_T / COP * N_maisons * coeff / 1000
            formula_besoin = (
                f"of:={ref_g}*[.E{r}]*[.G{r}]/[.D{r}]"
                f"*{ref_n_maisons}*[.F{r}]/1000"
            )

            # Pre-computed values for each column
            delta_t = max(0.0, cfg.temperature_interieure - t_ext)

            cells = [
                # A: Mois
                {'value': mois},
                # B: Plage
                {'value': plage},
                # C: T_ext
                {'value': t_ext, 'formula': formula_t_ext},
                # D: COP
                {'value': cop_value, 'formula': formula_cop},
                # E: Volume
                {'value': volume, 'formula': formula_volume},
                # F: Coeff plage
                {'value': coeff_plage, 'formula': formula_coeff},
                # G: Delta T
                {'value': delta_t, 'formula': formula_delta_t},
                # H: Besoin electrique (kW)
                {'value': p_kw, 'formula': formula_besoin},
            ]

            writer.add_formula_row(table, cells)
            row_num += 1
