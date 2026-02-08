# Sources de Données / Data Sources

Ce document répertorie toutes les sources de données utilisées dans le modèle de transition énergétique. Chaque source est documentée avec son URL, sa date d'accès et une description de son utilisation.

---

## Production d'Électricité

### RTE - Réseau de Transport d'Électricité

| Paramètre | Valeur | Source |
|-----------|--------|--------|
| Production nucléaire (été) | ~30 GW | RTE Bilan Électrique 2020 |
| Production nucléaire (hiver) | ~50 GW | RTE Bilan Électrique 2020 |
| Production hydraulique moyenne | ~7.5 GW | RTE Bilan Électrique 2020 |
| Capacité solaire France (2024) | ~20 GWc | RTE Panorama ENR |

**URL**: https://www.rte-france.com/analyses-tendances-et-prospectives/bilan-electrique
**Dernière consultation**: Janvier 2026
**Description**: Données historiques de production électrique française par filière.

### PVGIS - Photovoltaic Geographical Information System

| Paramètre | Valeur | Source |
|-----------|--------|--------|
| Facteurs de capacité solaire mensuels | 7-22% | PVGIS EU JRC |
| Irradiance par région | Variable | PVGIS EU JRC |

**URL**: https://re.jrc.ec.europa.eu/pvg_tools/en/
**Dernière consultation**: Janvier 2026
**Description**: Outil de simulation de production PV du Joint Research Centre européen. Utilisé pour estimer la production solaire en fonction de la localisation et de l'orientation.

---

## Consommation d'Énergie

### ADEME - Agence de la Transition Écologique

| Paramètre | Valeur | Source |
|-----------|--------|--------|
| Part du chauffage dans le résidentiel | 67% | ADEME Chiffres clés |
| Consommation moyenne logement | Variable | ADEME |

**URL**: https://www.ademe.fr/
**Dernière consultation**: Janvier 2026
**Description**: Statistiques sur la consommation énergétique des bâtiments et les usages.

### INSEE - Institut National de la Statistique

| Paramètre | Valeur | Source |
|-----------|--------|--------|
| Nombre de maisons individuelles | ~20 millions | INSEE RP |
| Nombre de logements collectifs | ~10 millions | INSEE RP |

**URL**: https://www.insee.fr/fr/statistiques
**Dernière consultation**: Janvier 2026
**Description**: Données sur le parc de logements français.

---

## Données Temporelles

### WorldData.info - Heures de Coucher du Soleil

| Mois | Heure (Paris) | Source |
|------|---------------|--------|
| Janvier | 17:23 | WorldData |
| Février | 18:12 | WorldData |
| Mars | 18:56 | WorldData |
| Avril | 20:43 | WorldData |
| Mai | 21:27 | WorldData |
| Juin | 21:57 | WorldData |
| Juillet | 21:51 | WorldData |
| Août | 21:08 | WorldData |
| Septembre | 20:05 | WorldData |
| Octobre | 19:03 | WorldData |
| Novembre | 17:12 | WorldData |
| Décembre | 16:56 | WorldData |

**URL**: https://www.worlddata.info/europe/france/sunset.php
**Dernière consultation**: Janvier 2026
**Description**: Heures de lever et coucher du soleil pour Paris (latitude ~49°N).

---

## Coûts et Données Financières

### IRENA - International Renewable Energy Agency

| Paramètre | Valeur | Année | Source |
|-----------|--------|-------|--------|
| CAPEX solaire PV | €600/kW | 2024 | IRENA Renewable Power Generation Costs |
| Durée de vie solaire | 30 ans | 2024 | IRENA |

**URL**: https://www.irena.org/publications/2024/Sep/Renewable-Power-Generation-Costs-in-2023
**Dernière consultation**: Janvier 2026
**Description**: Coûts de référence pour les énergies renouvelables au niveau mondial.

### BNEF - BloombergNEF

| Paramètre | Valeur | Année | Source |
|-----------|--------|-------|--------|
| CAPEX stockage batterie | €200/kWh | 2024 | BNEF Energy Storage Outlook |
| Durée de vie batterie | 15 ans | 2024 | BNEF |

**URL**: https://about.bnef.com/energy-storage-outlook/
**Dernière consultation**: Janvier 2026
**Description**: Projections de coûts pour le stockage d'énergie.

### Données de Marché Européen

| Paramètre | Valeur | Source |
|-----------|--------|--------|
| Coût marginal gaz CCGT | €90/MWh | Marchés européens 2024 |

**URL**: https://www.eex.com/
**Dernière consultation**: Janvier 2026
**Description**: Prix de référence pour la production électrique au gaz (SRMC - Short Run Marginal Cost).

---

## Stockage d'Énergie

### Références de Capacité

| Installation | Capacité | Type | Source |
|--------------|----------|------|--------|
| Grand'Maison (France) | 5 GWh | STEP | EDF |
| Moss Landing (USA) | 3 GWh | Batterie Li-ion | Vistra |
| STEP France total | ~100 GWh | STEP | RTE |

**Sources**:
- EDF: https://www.edf.fr/groupe-edf/nos-energies/energies-renouvelables/hydraulique
- Vistra: https://vistracorp.com/energy-storage/

---

## Pompes à Chaleur

### Coefficients de Performance (COP)

| Type de PAC | COP moyen | Conditions | Source |
|-------------|-----------|------------|--------|
| Air-air | 2.5-3.5 | 7°C ext. | ADEME |
| Air-eau | 2.5-4.0 | 7°C ext. | ADEME |
| Géothermique | 3.5-5.0 | Sol 10°C | ADEME |

**Note**: Le modèle utilise un COP conservateur de 2.0 pour tenir compte des températures hivernales basses.

**URL**: https://www.ademe.fr/expertises/batiment/passer-a-laction/elements-dequipement/pompes-a-chaleur
**Dernière consultation**: Janvier 2026

---

## Hypothèses du Modèle

### Hypothèses Simplificatrices

| Hypothèse | Valeur | Justification |
|-----------|--------|---------------|
| Jours par mois | 30 | Simplification du calcul |
| Éolien | Non comptabilisé | Hypothèse conservatrice |
| Interconnexions | Non comptabilisées | Hypothèse conservatrice |
| Stockage intersaisonnier | Non comptabilisé | Hors périmètre initial |

### Scénario de Déploiement Solaire

| Segment | Capacité | Hypothèse |
|---------|----------|-----------|
| Maisons individuelles | 200 GWc | 20M maisons × 10 kWc |
| Logements collectifs | 50 GWc | 10M logements × 5 kWc |
| Centrales solaires | 250 GWc | Grandes installations |
| **TOTAL** | **500 GWc** | Scénario de base |

---

## Mise à Jour des Sources

Pour garantir l'auditabilité du modèle, les sources doivent être vérifiées et mises à jour régulièrement:

1. **Annuellement**: Prix (gaz, CAPEX solaire, stockage)
2. **Tous les 2 ans**: Données de production RTE, capacités installées
3. **Tous les 5 ans**: Hypothèses structurelles (COP, durées de vie)

---

## Contact

Pour toute question sur les sources de données:
- Projet: https://github.com/[repo]/energy_model
- Email: [contact]
