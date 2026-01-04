# Modèle de Transition Énergétique - France

Ce document décrit le modèle de simulation énergétique contenu dans le fichier `modélisation générale.ods`, qui évalue les besoins en énergie d'appoint pour un scénario de transition énergétique en France.

## Résultat Principal

> **Le modèle estime un besoin brut de ~114 TWh (100 milliards de kWh) d'énergie d'appoint (gaz) pour assurer l'équilibre électrique pendant la saison hivernale.**

---

## Structure du Modèle

### Feuille Principale: "moulinette simplifiée avec PAC"

Le calcul se fait par **mois** et par **plage horaire** (5 plages par jour):

| Plage | Durée | Caractéristique |
|-------|-------|-----------------|
| 8h-13h | 5h | Production solaire maximale |
| 13h-18h | 5h | Production solaire maximale |
| 18h-20h | 2h | Variable selon saison (voir analyse coucher du soleil) |
| 20h-23h | 3h | Solaire partiel en été, nuit en hiver |
| 23h-8h | 9h | Nuit (généralement en surplus) |

### Colonnes Clés

| Colonne | Contenu |
|---------|---------|
| A | Mois et plage horaire |
| B-D | Production PV (maisons, collectif, centrales) |
| E | Production hydraulique |
| F | Production éolienne (ignorée) |
| G | Production nucléaire |
| **H** | **Total production (kW)** |
| I-O | Consommation par secteur |
| **P** | **Total consommation (kW)** |
| **Q** | **Déficit = P - H si positif (kW)** |
| **R** | **Durée de la plage (heures)** |
| **S** | **Énergie gaz nécessaire (TWh)** |

---

## Formule de Calcul

L'énergie d'appoint nécessaire est calculée selon:

```
S (TWh) = Q (kW) × R (heures/jour) × 30 (jours/mois) / 10⁹
```

Où:
- **Q**: Puissance manquante (consommation - production) en kW
- **R**: Nombre d'heures par jour de cette plage
- **30**: Nombre de jours par mois (approximation)
- **10⁹**: Conversion kWh → TWh

### Exemple: Janvier 8h-13h

```
Production:   158.6 GW (159 millions kW)
Consommation: 244.1 GW (244 millions kW)
Déficit Q:     85.3 GW (85.3 millions kW)
Durée R:       5 heures/jour

Énergie = 85,300,000 × 5 × 30 / 1,000,000,000 = 12.80 TWh
```

---

## Hypothèses de Production

### Photovoltaïque (500 GWc installés)

| Source | Capacité | Détail |
|--------|----------|--------|
| Maisons individuelles | 200 GWc | 20 millions × 10 kWc |
| Logements collectifs | 50 GWc | 10 millions × 5 kWc |
| Centrales solaires | 250 GWc | Grandes installations |

La production effective varie selon le mois (facteur de charge ~7-22%).

### Nucléaire

- Maintenu au niveau actuel (données RTE 2020)
- Variation saisonnière: ~30 GW (été) à ~50 GW (hiver)
- Pas de construction de nouvelles capacités dans ce scénario

### Hydraulique

- Maintenu au niveau actuel (données RTE 2020)
- Moyenne: ~5-10 GW selon les mois
- Inclut barrages et fil de l'eau

### Éolien

- **Non comptabilisé** dans le modèle
- Justification: production trop irrégulière
- C'est une hypothèse conservatrice (pessimiste)

---

## Hypothèses de Consommation

### Secteur Résidentiel

| Composante | Traitement |
|------------|------------|
| Chauffage (67% du résidentiel) | Électrifié via **pompes à chaleur** (PAC) |
| Autres usages (33%) | Maintenu au niveau actuel |

**Pompes à chaleur:**
- COP moyen = 2 (coefficient de performance)
- La consommation thermique est divisée par 2 lors de la conversion en électrique
- Répartition mensuelle selon les degrés-jours de chauffage

### Secteur Transport

| Type | Correction |
|------|------------|
| Marchandises | ×0.4 (rendement moteur thermique → électrique) |
| Voyageurs | ×0.2 (efficacité + report modal) |
| Déjà électrique | Maintenu |

### Secteurs Industrie et Tertiaire

- Consommation maintenue au niveau actuel
- Pas d'hypothèse de décarbonation industrielle

---

## Résultats Détaillés

### Répartition Mensuelle du Besoin Gaz

| Mois | Énergie (TWh) | % du total |
|------|---------------|------------|
| Janvier | 29.4 | 25% |
| Décembre | 28.6 | 24% |
| Novembre | 26.2 | 22% |
| Février | 16.9 | 14% |
| Octobre | 9.8 | 9% |
| Mars | 2.4 | 2% |
| Avril | 1.6 | 1% |
| Mai-Sept | 0 | 0% |
| **TOTAL** | **~117 TWh** | 100% |

### Observations

1. **Saisonnalité marquée**: 100% du besoin gaz est concentré sur octobre-avril
2. **Pics hivernaux**: Janvier et décembre représentent ~50% du besoin annuel
3. **Heures critiques**: Les plages 8h-18h concentrent l'essentiel du déficit
4. **Nuits excédentaires**: La plage 23h-8h est généralement en surplus

---

## Analyse du Coucher du Soleil

La France (latitude ~49°N, Paris) a des heures de coucher du soleil très variables selon la saison. Cela impacte directement la production solaire sur les plages 18h-20h et 20h-23h.

### Heures de Coucher du Soleil (Paris)

| Mois | Coucher | 18h-20h | 20h-23h |
|------|---------|---------|---------|
| Janvier | 17:23 | Nuit | Nuit |
| Février | 18:12 | ~6% solaire | Nuit |
| Mars | 18:56 | ~45% solaire | Nuit |
| Avril | 20:43 | Plein soleil | ~24% solaire |
| Mai | 21:27 | Plein soleil | ~49% solaire |
| Juin | 21:57 | Plein soleil | ~66% solaire |
| Juillet | 21:51 | Plein soleil | ~64% solaire |
| Août | 21:08 | Plein soleil | ~36% solaire |
| Septembre | 20:05 | Plein soleil | ~2% solaire |
| Octobre | 19:03 | ~52% solaire | Nuit |
| Novembre | 17:12 | Nuit | Nuit |
| Décembre | 16:56 | Nuit | Nuit |

*Source: [worlddata.info](https://www.worlddata.info/europe/france/sunset.php)*

### Implications pour le Modèle

1. **Été (Mai-Août)**: La plage 18h-20h bénéficie de plein soleil. Des productions de 180+ GW sont physiquement cohérentes.

2. **Hiver (Nov-Fév)**: Le soleil se couche avant 18h30. La production 18h-20h devrait être ~50-60 GW (nucléaire + hydro uniquement).

3. **Intersaison (Mars, Avril, Sept, Oct)**: Production solaire partielle sur 18h-20h.

### Anomalies Détectées dans le Tableur

L'analyse croisée des heures de coucher du soleil et des productions du tableur révèle **3 anomalies**:

| Mois | Plage | Production | Attendu max | Écart |
|------|-------|------------|-------------|-------|
| Mars | 18h-20h | 215.9 GW | ~132 GW | +84 GW |
| Juillet | 20h-23h | 183.3 GW | ~160 GW | +23 GW |
| Octobre | 18h-20h | 170.7 GW | ~148 GW | +23 GW |

Ces anomalies sont probablement des erreurs de copier-coller où la production solaire de jour a été reportée sur des plages avec ensoleillement partiel.

**Impact**: Ces erreurs créent des surplus artificiels qui réduisent légèrement le déficit calculé. Le besoin réel en gaz pourrait être marginalement supérieur à 114 TWh.

---

## Limites du Modèle

### Ce qui n'est PAS pris en compte

1. **Stockage intersaisonnier**: Pas de batteries, STEP, ou hydrogène
2. **Éolien**: Ignoré malgré sa contribution potentielle en hiver
3. **Interconnexions européennes**: Pas d'import/export
4. **Flexibilité de la demande**: Pas d'effacement ou décalage
5. **Véhicules électriques**: Pas de vehicle-to-grid (V2G)

### Hypothèses simplificatrices

- 30 jours par mois (au lieu des jours réels)
- Facteurs solaires moyens par mois (pas de variabilité journalière)
- Consommation constante au sein de chaque plage horaire

### Impact sur le résultat

Ces simplifications tendent à **surestimer** le besoin en gaz:
- L'éolien produirait davantage en hiver
- Le stockage permettrait de valoriser les surplus estivaux
- Les interconnexions offriraient une marge de sécurité

---

## Analyse Financière

### Paramètres de Coût (2024)

| Paramètre | Valeur | Source |
|-----------|--------|--------|
| Électricité gaz (SRMC) | €90/MWh = €90M/TWh | Coût marginal CCGT Europe |
| Solaire PV (CAPEX) | €600/kW = €600M/GWc | IRENA Europe 2024 |
| Stockage batterie (CAPEX) | €200/kWh = €200M/GWh | BNEF Europe 2024 (turnkey) |
| Durée de vie solaire | 30 ans | Standard industrie |
| Durée de vie stockage | 15 ans | Standard industrie |

### Analyse de Sensibilité (100 → 1000 GWc)

L'analyse étendue explore l'impact de différentes capacités solaires sur le besoin en gaz:

| Capacité solaire | Gaz (sans stockage) | Gaz (avec stockage) |
|------------------|---------------------|---------------------|
| 100 GWc | ~390 TWh | ~390 TWh |
| 300 GWc | ~181 TWh | ~181 TWh |
| 500 GWc (modèle initial) | ~115 TWh | ~88 TWh |
| 700 GWc | ~51 TWh | ~39 TWh |
| 950 GWc | ~13 TWh | **0 TWh** |

### Comparaison des Scénarios (coût total sur 30 ans)

| Scénario | CAPEX | Gaz/an | Total 30 ans | vs Optimum |
|----------|-------|--------|--------------|------------|
| France ×5 (100 GWc) | €118B | €35.1B | €1,171B | +€620B |
| Intermédiaire (300 GWc) | €258B | €16.3B | €746B | +€196B |
| Modèle initial (500 GWc) | €365B | €7.9B | €602B | +€52B |
| **Optimum (700 GWc)** | **€444B** | **€3.5B** | **€550B** | **—** |
| Zéro gaz (950 GWc) | €596B | €0 | €596B | +€46B |

### Conclusions Financières

1. **Optimum économique à 700 GWc**: Le coût total sur 30 ans (CAPEX + gaz) est minimisé à 700 GWc de capacité solaire, soit 35× la capacité actuelle de la France (~20 GWc en 2024).

2. **Rendement décroissant**: Au-delà de 700 GWc, chaque GWc supplémentaire coûte plus cher à installer qu'il ne permet d'économiser en gaz.

3. **Scénario zéro-gaz**: Nécessite ~950 GWc + 128 GWh de stockage (€596B CAPEX). Coûte €46B de plus que l'optimum sur 30 ans, mais garantit l'indépendance énergétique totale.

4. **Coût de référence**: Sans investissement solaire, le gaz seul coûterait ~€1,600B sur 30 ans (scénario théorique à 0 GWc).

---

## Sources de Données

| Donnée | Source |
|--------|--------|
| Production nucléaire/hydro | RTE - Données 2020 |
| Facteurs solaires | PVGIS (EU JRC) |
| Consommation sectorielle | Statistiques françaises corrigées |
| Températures | Moyennes mensuelles France métropolitaine |
| Heures de coucher du soleil | [worlddata.info](https://www.worlddata.info/europe/france/sunset.php) |

---

## Fichiers Associés

| Fichier | Description |
|---------|-------------|
| `modélisation générale.ods` | Tableur original (17 feuilles) |
| `france_energy_transition.ipynb` | Reproduction Python du modèle |
| `bilan_energetique_mensuel.csv` | Données détaillées exportées |
| `resume_par_mois.csv` | Résumé mensuel |
| `bilan_energetique_114twh.png` | Visualisations principales |
| `sensibilite_solaire_gaz.png` | Analyse de sensibilité |
| `analyse_financiere.png` | Analyse financière |

---

## Utilisation

```bash
# Installer les dépendances
cd energy_model
uv sync

# Lancer le notebook
uv run jupyter lab france_energy_transition.ipynb
```

---

## Conclusion

### Résultats Énergétiques

Le modèle initial (500 GWc de PV) démontre un besoin d'environ **114-117 TWh** d'énergie d'appoint pendant l'hiver, principalement pour compenser:

1. La faible production solaire hivernale (facteur de charge ~7-12%)
2. La forte demande de chauffage (malgré le COP=2 des PAC)
3. L'absence de stockage intersaisonnier

### Résultats Financiers

L'analyse financière étendue (100 → 1000 GWc) révèle:

| Résultat | Valeur |
|----------|--------|
| **Optimum économique** | 700 GWc de solaire + 122 GWh de stockage |
| **Coût total optimal (30 ans)** | €550 milliards |
| **Gaz résiduel à l'optimum** | 39 TWh/an = €3.5B/an |
| **Capacité pour zéro gaz** | 950 GWc + 128 GWh stockage |
| **Surcoût zéro-gaz vs optimum** | +€46 milliards sur 30 ans |

### Enseignements Clés

1. **L'optimum économique se situe à 700 GWc**, soit 35× la capacité française actuelle (~20 GWc).

2. **Rendement décroissant**: au-delà de 700 GWc, chaque GWc supplémentaire coûte plus qu'il n'économise.

3. **Le stockage journalier** (efficacité 85%) réduit significativement le besoin en gaz en valorisant les surplus nocturnes.

4. **L'indépendance énergétique totale** (zéro gaz) est atteignable à ~950 GWc avec un surcoût modéré (+€46B sur 30 ans).

### Limites

- Éolien non comptabilisé (hypothèse conservatrice)
- Pas de stockage inter-saisonnier
- Pas d'interconnexions européennes
- Coûts 2024 (les prix du solaire et du stockage continuent de baisser)
