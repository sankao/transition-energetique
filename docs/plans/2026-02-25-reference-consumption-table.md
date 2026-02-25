# Tableau de reference — Consommation energetique France

**Date** : 2026-02-25
**Objet** : Cadre de controle d'exhaustivite pour le modele de transition energetique
**Source primaire** : SDES, Bilan energetique de la France pour 2023 (publie avril 2025)
**Perimetre** : Consommation finale totale, tous usages (energetiques + non-energetiques)
**Annee de reference** : 2023

---

## 1. Principes

Ce document est le **referentiel unique** du modele. Toute valeur produite par le
code doit etre confrontee a ce tableau. Les regles sont :

1. **Exhaustivite** — La somme des secteurs doit reconstituer 1 615 TWh (SDES 2023).
2. **Bilan complet** — Chaque poste montre : electricite directe, H2, biomasse/EnR,
   fossile residuel. La somme des vecteurs = total du poste.
3. **Tracabilite** — Chaque hypothese d'electrification est explicite (methode, COP,
   rendement, source).
4. **Coherence offre/demande** — La demande electrique totale (733 TWh) doit etre
   confrontee au bilan de production (solaire + nucleaire + hydro + gaz backup).

---

## 2. Situation actuelle — France 2023 (SDES)

### 2.1 Synthese par secteur

| Secteur              | TWh total | Elec | Gaz  | Petrole | Charbon | EnR  | Reseau |
|----------------------|-----------|------|------|---------|---------|------|--------|
| Residentiel          | 422       | 147  | 119  | 36      | —       | 127  | 13     |
| Tertiaire            | 229       | 124  | 62   | 21      | —       | 11   | 11     |
| Industrie            | 283       | 102  | 102  | 28      | 6       | 25   | 17     |
| Transport            | 513       | 13   | 5    | 457     | —       | 38   | —      |
| Agriculture + Peche  | 55        | 7    | 3    | 40      | —       | 5    | —      |
| Usages non-energ.    | 113       | —    | 25   | 88      | —       | —    | —      |
| **TOTAL FRANCE**     | **1 615** | **393** | **316** | **670** | **6** | **206** | **41** |

Controle SDES : electricite ~24%, gaz ~20%, petrole ~41%, EnR ~13%, reseau ~3%.

### 2.2 Residentiel — detail par usage (422 TWh)

| Usage              | TWh | Elec | Gaz | Petrole | EnR (bois) | Reseau |
|--------------------|-----|------|-----|---------|------------|--------|
| Chauffage          | 312 | 50   | 94  | 31      | 125        | 12     |
| ECS                | 38  | 15   | 15  | 5       | 2          | 1      |
| Elec specifique    | 68  | 68   | —   | —       | —          | —      |
| Cuisson            | 22  | 12   | 10  | —       | —          | —      |
| Climatisation      | 2   | 2    | —   | —       | —          | —      |
| **Total**          | **422** | **147** | **119** | **36** | **127** | **13** |

Sources : SDES (150.7 TWh elec, 101.3 gaz, 35.7 petrole, 119.4 EnR, 14.9 chaleur).
Sous-repartition par usage : estimations CEREN/ADEME.

### 2.3 Tertiaire — detail par usage (229 TWh)

| Usage                          | TWh | Elec | Gaz | Petrole | EnR | Reseau |
|--------------------------------|-----|------|-----|---------|-----|--------|
| Chauffage                      | 85  | 12   | 42  | 10      | 11  | 10     |
| Climatisation / ventilation    | 20  | 20   | —   | —       | —   | —      |
| Eclairage                      | 28  | 28   | —   | —       | —   | —      |
| Elec specifique (IT, ascens.)  | 48  | 48   | —   | —       | —   | —      |
| ECS                            | 18  | 6    | 10  | 2       | —   | —      |
| Cuisson (restauration coll.)   | 10  | 3    | 6   | 1       | —   | —      |
| Autres                         | 20  | 7    | 4   | 8       | —   | 1      |
| **Total**                      | **229** | **124** | **62** | **21** | **11** | **11** |

Sources : SDES (54% elec, 27% gaz, 9% petrole). Sous-repartition : CEREN/ADEME.

### 2.4 Industrie — detail par usage (283 TWh)

| Usage                                           | TWh | Elec | Gaz | Petrole | Charbon | EnR | Reseau |
|-------------------------------------------------|-----|------|-----|---------|---------|-----|--------|
| Chaleur HT (>400C) — acier, ciment, verre       | 75  | 10   | 35  | 10      | 6       | 5   | 9      |
| Chaleur MT (100-400C) — chimie, agroalim, papier | 55  | 4    | 30  | 8       | —       | 8   | 5      |
| Chaleur BT (<100C) — sechage, lavage             | 40  | 4    | 20  | 5       | —       | 8   | 3      |
| Force motrice — moteurs, compresseurs            | 65  | 60   | 3   | 2       | —       | —   | —      |
| Electrochimie — aluminium, chlore                | 18  | 18   | —   | —       | —       | —   | —      |
| Eclairage / IT / support                         | 15  | 3    | 7   | 2       | —       | 3   | —      |
| Autres — froid industriel, air comprime          | 15  | 3    | 7   | 1       | —       | 1   | —      |
| **Total**                                        | **283** | **102** | **102** | **28** | **6** | **25** | **17** |

Sources : SDES (36% elec, 36% gaz, 10% petrole, 9% EnR, 6% reseau, 2% charbon).
Sous-repartition par temperature : ADEME/CEREN.

### 2.5 Transport — detail par mode (513 TWh)

| Mode                        | TWh | Petrole | Biocarb. | Elec | Gaz |
|-----------------------------|-----|---------|----------|------|-----|
| Voitures particulieres      | 200 | 180     | 17       | 2    | 1   |
| Poids lourds (>3.5t)        | 140 | 126     | 10       | —    | 4   |
| Utilitaires legers (<3.5t)  | 40  | 36      | 4        | —    | —   |
| Deux-roues                  | 10  | 10      | —        | —    | —   |
| Bus / cars                  | 15  | 13      | 1        | 1    | —   |
| Ferroviaire                 | 15  | 5       | —        | 10   | —   |
| Aviation domestique         | 10  | 9       | 1        | —    | —   |
| Aviation internationale     | 55  | 50      | 5        | —    | —   |
| Maritime + fluvial          | 18  | 18      | —        | —    | —   |
| Autres (pipelines)          | 10  | 10      | —        | —    | —   |
| **Total**                   | **513** | **457** | **38** | **13** | **5** |

Sources : SDES (89% petrole, 7.5% biocarb, 2.6% elec, 0.8% gaz).

### 2.6 Agriculture + Peche — detail par usage (55 TWh)

| Usage                              | TWh | Petrole | Elec | Gaz | EnR |
|------------------------------------|-----|---------|------|-----|-----|
| Machinisme (tracteurs, engins)     | 30  | 29      | —    | —   | 1   |
| Serres (chauffage)                 | 7   | 1       | 1    | 3   | 2   |
| Irrigation (pompage)               | 3   | —       | 3    | —   | —   |
| Batiments elevage                  | 5   | 2       | 2    | —   | 1   |
| Sechage / stockage                 | 3   | 2       | —    | —   | 1   |
| Peche                              | 4   | 4       | —    | —   | —   |
| Autres                             | 3   | 2       | 1    | —   | —   |
| **Total**                          | **55** | **40** | **7** | **3** | **5** |

Sources : SDES (74% petrole, 13% elec, 9% EnR, 4% gaz). Sous-repartition : Agreste/ADEME.

### 2.7 Usages non-energetiques (113 TWh)

| Usage                                      | TWh | Petrole | Gaz |
|--------------------------------------------|-----|---------|-----|
| Petrochimie (naphta -> ethylene, plastiques) | 60  | 55      | 5   |
| Engrais azotes (gaz -> NH3 -> uree)        | 18  | —       | 18  |
| Bitumes (routes)                           | 15  | 15      | —   |
| Lubrifiants                                | 5   | 5       | —   |
| Solvants                                   | 5   | 5       | —   |
| Autres (paraffines, cires)                 | 10  | 8       | 2   |
| **Total**                                  | **113** | **88** | **25** |

---

## 3. Scenario electrifie — Hypotheses de conversion

### 3.1 Residentiel (422 -> 302 TWh, -28%)

| Usage           | Methode                                                     | Elec | H2 | EnR | Fos. | Total |
|-----------------|-------------------------------------------------------------|------|----|-----|------|-------|
| Chauffage (312) | PAC COP 3.5 moy pour gaz+fioul. Bois maintenu. Reseau maint. Elec existant optimise PAC. | 71 | 0 | 125 | 0 | 196 |
| ECS (38)        | PAC / chauffe-eau thermo COP 3.0 pour fossile. Elec maintenu. | 22 | 0 | 2 | 0 | 24 |
| Elec spe. (68)  | Gains efficacite -15% (LED, appareils A+++).                | 58 | 0 | 0 | 0 | 58 |
| Cuisson (22)    | Induction pour gaz (efficacite +20%).                       | 20 | 0 | 0 | 0 | 20 |
| Clim (2)        | Maintenu + croissance moderee.                              | 4  | 0 | 0 | 0 | 4  |
| **Total**       |                                                             | **175** | **0** | **127** | **0** | **302** |

### 3.2 Tertiaire (229 -> 140 TWh, -39%)

| Usage             | Methode                                                       | Elec | H2 | EnR | Fos. | Total |
|-------------------|---------------------------------------------------------------|------|----|-----|------|-------|
| Chauffage (85)    | Renovation -30% besoin. PAC COP 3.0 pour fossile. EnR + reseau maintenus. | 20 | 0 | 8 | 0 | 38 |
| Clim/ventil (20)  | Efficacite +20%.                                              | 16 | 0 | 0 | 0 | 16 |
| Eclairage (28)    | LED generalise -50%.                                          | 14 | 0 | 0 | 0 | 14 |
| Elec spe. (48)    | Efficacite -15% (IT, moteurs).                                | 41 | 0 | 0 | 0 | 41 |
| ECS (18)          | Chauffe-eau thermo COP 3.0 pour fossile.                     | 9  | 0 | 0 | 0 | 9  |
| Cuisson (10)      | Induction pour gaz.                                           | 8  | 0 | 0 | 0 | 8  |
| Autres (20)       | Reduction -30%. Residuel groupes secours.                     | 12 | 0 | 0 | 2 | 14 |
| **Total**         |                                                               | **120** | **0** | **8** | **2** | **140** |

### 3.3 Industrie (283 -> 222 TWh, -22%)

| Usage              | Methode                                                                    | Elec | H2 | EnR | Fos. | Total |
|--------------------|----------------------------------------------------------------------------|------|----|-----|------|-------|
| Chaleur HT (75)    | EAF acier. Fours elec verre. H2 pour ciment/chimie HT. Process ciment incompressible. Efficacite +10%. | 22 | 18 | 5 | 15 | 60 |
| Chaleur MT (55)    | PAC industrielles COP 2.0-2.5 (100-200C). Fours elec au-dela. H2 chimie specifique. Efficacite +15%. | 28 | 5 | 8 | 0 | 41 |
| Chaleur BT (40)    | PAC industrielles COP 3.0-3.5. EnR maintenue. Efficacite +15%.            | 14 | 0 | 8 | 0 | 22 |
| Force motrice (65) | Deja 92% elec. Variateurs -12%. Diesel residuel -> elec.                  | 57 | 0 | 0 | 0 | 57 |
| Electrochimie (18) | Deja 100% elec. Maintenu.                                                 | 18 | 0 | 0 | 0 | 18 |
| Eclairage/IT (15)  | LED, efficacite IT -20%.                                                   | 12 | 0 | 0 | 0 | 12 |
| Autres (15)        | Froid + air comprime : efficacite -15%.                                    | 11 | 0 | 1 | 0 | 12 |
| **Total**          |                                                                            | **162** | **23** | **22** | **15** | **222** |

Note : electricite industrie 102 -> 162 TWh (+60 TWh). Coherent avec RTE Futurs
Energetiques 2050 qui projette +65 TWh pour l'industrie.

### 3.4 Transport (513 -> 245 TWh, -52%)

| Mode                   | Methode                                                              | Elec | H2 | Biocarb | Fos. | Total |
|------------------------|----------------------------------------------------------------------|------|----|---------|------|-------|
| VP (200)               | Modal -10%, sobriete -5%. VE x0.33. Flotte 95% VE.                  | 53 | 0 | 5 | 4 | 62 |
| PL (140)               | Report rail -10%. 50% batterie x0.35, 25% H2 PAC, 15% bio, 10% fos. | 22 | 22 | 17 | 12 | 73 |
| VUL (40)               | Quasi-100% VE x0.33. Logistique optimisee -5%.                      | 12 | 0 | 1 | 0 | 13 |
| 2-roues (10)           | VE x0.30.                                                           | 3  | 0 | 0 | 0 | 3  |
| Bus/cars (15)          | Bus urbains 100% elec. Cars longue distance H2.                     | 4  | 2 | 0 | 0 | 6  |
| Ferroviaire (15)       | Electrification lignes diesel. H2 lignes isolees.                   | 13 | 1 | 0 | 0 | 14 |
| Avia. dom. (10)        | Report TGV -50%. SAF pour residuel.                                 | 1  | 0 | 4 | 0 | 5  |
| Avia. int. (55)        | Sobriete -10%. SAF 30%, H2 court-courrier 10%, fossile 50%.         | 0  | 5 | 15 | 25 | 45 |
| Maritime+fluv. (18)    | Cotier/fluvial elec. Haute mer H2 + fossile.                        | 2  | 3 | 3 | 8 | 16 |
| Autres (10)            | Pipelines pompage electrique. Efficacite -20%.                      | 8  | 0 | 0 | 0 | 8  |
| **Total**              |                                                                      | **118** | **33** | **45** | **49** | **245** |

Note : le gain majeur vient de la physique du moteur electrique (~90% rendement
vs ~30% thermique), soit un facteur ~3x sur l'energie consommee.

### 3.5 Agriculture + Peche (55 -> 36 TWh, -35%)

| Usage              | Methode                                                          | Elec | H2 | Bio/EnR | Fos. | Total |
|--------------------|------------------------------------------------------------------|------|----|---------|------|-------|
| Machinisme (30)    | 40% VE petits engins x0.35. 30% biocarburants gros tracteurs. 20% H2 grandes exploit. 10% fos. | 4 | 4 | 7 | 3 | 18 |
| Serres (7)         | PAC COP 3.0 pour gaz+fioul. EnR geothermie/biomasse maintenue.  | 2  | 0 | 2 | 0 | 4  |
| Irrigation (3)     | Deja quasi-tout elec. Maintenu.                                  | 3  | 0 | 0 | 0 | 3  |
| Bat. elevage (5)   | PAC COP 3.0 pour fossile. Elec maintenu + efficacite -10%.      | 3  | 0 | 1 | 0 | 4  |
| Sechage (3)        | Sechage solaire + PAC elec. Biomasse maintenue.                  | 1  | 0 | 1 | 0 | 2  |
| Peche (4)          | Cotier elec 30%. Haute mer H2 25%. Fossile res. 25%. Effic -20%. | 1 | 1 | 0 | 1 | 3  |
| Autres (3)         | Electrification directe. Efficacite -30%.                        | 2  | 0 | 0 | 0 | 2  |
| **Total**          |                                                                  | **16** | **5** | **11** | **4** | **36** |

### 3.6 Usages non-energetiques (113 -> 95 TWh, -16%)

| Usage               | Methode                                                          | Elec | H2 | Bio/rec. | Fos. | Total |
|---------------------|------------------------------------------------------------------|------|----|----------|------|-------|
| Petrochimie (60)    | Recyclage chimique -20%. Bio-source 30%. E-chemicals H2+CO2 20%. Fossile res. 30%. | 3 | 10 | 15 | 20 | 48 |
| Engrais (18)        | H2 vert -> NH3 vert (Haber-Bosch, seul H2 change). Quasi-total. | 0  | 16 | 0 | 2 | 18 |
| Bitumes (15)        | Recyclage asphalte -20%. Biobitumes 30%. Fossile res. 50%.       | 0  | 0 | 5 | 7 | 12 |
| Lubrifiants (5)     | Bio-lubrifiants 50%. Fossile 50%.                                | 0  | 0 | 2 | 2 | 4  |
| Solvants (5)        | Chimie verte 60%. Fossile 40%.                                   | 0  | 0 | 3 | 2 | 5  |
| Autres (10)         | Mix bio-source + recyclage.                                      | 2  | 2 | 2 | 2 | 8  |
| **Total**           |                                                                  | **5** | **28** | **27** | **35** | **95** |

Note : taux de fossile residuel le plus eleve (37%) — normal, le carbone est
ici une matiere premiere, pas une source d'energie.

---

## 4. Bilan systeme complet

### 4.1 Synthese demande par vecteur

| Secteur             | Actuel | -> Elec | -> H2 | -> Bio/EnR | -> Fos. res. | Total cible |
|---------------------|--------|---------|-------|------------|--------------|-------------|
| Residentiel         | 422    | 175     | 0     | 127        | 0            | 302         |
| Tertiaire           | 229    | 120     | 0     | 8          | 2            | 140         |
| Industrie           | 283    | 162     | 23    | 22         | 15           | 222         |
| Transport           | 513    | 118     | 33    | 45         | 49           | 245         |
| Agriculture         | 55     | 16      | 5     | 11         | 4            | 36          |
| Non-energie         | 113    | 5       | 28    | 27         | 35           | 95          |
| **Sous-total conso** | **1 615** | **596** | **89** | **240** | **105**    | **1 040**   |

### 4.2 Production H2

Les 89 TWh de H2 consomme doivent etre produits par electrolyse :

| Poste                           | TWh       |
|---------------------------------|-----------|
| H2 consomme (usages finaux)     | 89        |
| Rendement electrolyse           | ~65%      |
| **Electricite pour H2**         | **+137**  |

### 4.3 Demande electrique totale

| Poste                           | TWh       |
|---------------------------------|-----------|
| Electricite directe (6 secteurs)| 596       |
| Electricite pour production H2  | 137       |
| **TOTAL ELECTRICITE A PRODUIRE**| **733**   |

Controle RTE : Futurs Energetiques 2050 projette 645-755 TWh selon scenarios.
Notre 733 TWh = fourchette haute, coherent avec hypothese d'electrification maximale.

### 4.4 Bilan production electrique

| Source                                       | TWh elec    |
|----------------------------------------------|-------------|
| Solaire (500 GWc x ~1 100 h eq.)            | ~550 brut   |
| Nucleaire (maintenu)                         | ~350        |
| Hydro (maintenu)                             | ~65         |
| **Production brute**                         | **~965**    |
| Curtailment solaire ete (surplus)            | -150        |
| Pertes stockage batterie/STEP (rend. 85%)    | -20         |
| **Production utile decarbonee**              | **~795**    |

### 4.5 Deficit hivernal et gaz backup

Le bilan annuel est excedentaire (+62 TWh), mais le desequilibre saisonnier
impose un complement gaz :

| Periode            | Prod. decarb. | Demande | Solde     |
|--------------------|---------------|---------|-----------|
| Nov-Fev (4 mois)   | ~160          | ~280    | **-120**  |
| Mar-Avr, Sep-Oct   | ~270          | ~240    | +30       |
| Mai-Aout (4 mois)  | ~365          | ~213    | +152      |

| Poste                                      | Valeur      |
|--------------------------------------------|-------------|
| Deficit hivernal net (apres stockage)      | ~100-110 TWh elec |
| Rendement CCGT                             | ~55%        |
| **Gaz consomme pour backup**               | **~190 TWh gaz** |

### 4.6 Bilan fossile complet

| Poste fossile                              | TWh         |
|--------------------------------------------|-------------|
| Usages finaux residuels (6 secteurs)       | 105         |
| Gaz backup centrales (production elec)     | 190         |
| **TOTAL FOSSILE RESIDUEL**                 | **~295**    |

### 4.7 Comparaison avec 2023

| Indicateur                  | 2023       | Scenario cible | Evolution |
|-----------------------------|------------|----------------|-----------|
| Consommation finale totale  | 1 615 TWh  | 1 230 TWh      | -24%      |
| Fossile total               | 992 TWh    | 295 TWh        | **-70%**  |
| Electricite produite        | ~475 TWh   | 733 TWh        | +54%      |
| Bio/EnR (hors elec)         | 206 TWh    | 240 TWh        | +17%      |

---

## 5. Parametres cles a calibrer dans le modele

Le modele doit reproduire ces valeurs. Les parametres critiques sont :

| Parametre                   | Valeur     | Sensibilite | Module concerne    |
|-----------------------------|------------|-------------|--------------------|
| COP PAC residentiel moyen   | 3.5        | Haute       | heating.py         |
| COP PAC tertiaire moyen     | 3.0        | Haute       | secteurs.py        |
| COP PAC industrielle BT     | 3.0-3.5    | Moyenne     | secteurs.py        |
| COP PAC industrielle MT     | 2.0-2.5    | Moyenne     | secteurs.py        |
| Facteur VE / thermique VP   | 0.33       | Haute       | transport.py       |
| Facteur VE / thermique PL   | 0.35       | Haute       | transport.py       |
| Modal shift transport       | -10%       | Moyenne     | transport.py       |
| Renovation tertiaire        | -30% besoin| Moyenne     | secteurs.py        |
| LED tertiaire               | -50%       | Basse       | secteurs.py        |
| Rendement CCGT backup       | 55%        | Basse       | config.py          |
| Rendement electrolyse H2    | 65%        | Moyenne     | (nouveau module)   |
| Capacite solaire             | 500 GWc   | Tres haute  | config.py          |

---

## 6. Ecarts identifies avec le modele actuel (v0.7.0)

| Ecart                                    | Modele actuel | Reference | Delta     |
|------------------------------------------|---------------|-----------|-----------|
| Consommation totale                      | ~935 TWh      | 1 615 TWh | **-42%**  |
| Residentiel chauffage                    | 55-92 TWh     | 312 TWh   | **-70%**  |
| Industrie                                | 205 TWh bloc  | 283 TWh detail | -28%  |
| Transport                                | 480 TWh       | 513 TWh   | -6%       |
| Tertiaire                                | 200 TWh       | 229 TWh   | -13%      |
| Usages non-energetiques                  | absent        | 113 TWh   | **manquant** |
| Tarification base                        | 700 TWh       | 733 TWh   | -5%       |
| Gaz backup                               | 114 TWh       | ~190 TWh  | -40%      |
| Production H2 (electricite)              | absent        | 137 TWh   | **manquant** |

L'ecart principal vient du residentiel : le modele ne comptait que la
consommation electrique de chauffage (post-PAC), pas la consommation
energetique totale actuelle. Le tableau de reference impose de partir du
total reel (312 TWh) pour ensuite appliquer les conversions.

---

## 7. Sources

| Source | Donnees | Lien |
|--------|---------|------|
| SDES | Bilan energetique 2023, consommation finale par secteur et par energie | https://www.statistiques.developpement-durable.gouv.fr/bilan-energetique-de-la-france-pour-2023-0 |
| SDES | Chiffres cles de l'energie, edition 2025 | https://www.statistiques.developpement-durable.gouv.fr/edition-numerique/chiffres-cles-energie/fr/7-consommation-finale-denergiepar-secteur-et |
| SDES | Detail residentiel 2023 | https://www.statistiques.developpement-durable.gouv.fr/edition-numerique/bilan-energetique/fr/28-53-residentiel--baisse-de |
| RTE | Futurs Energetiques 2050 | https://www.rte-france.com/analyses-tendances-et-prospectives/bilan-previsionnel-2050-futurs-energetiques |
| ADEME | Guide Pompes a Chaleur, efficacites industrielles | https://www.ademe.fr |
| CEREN | Enquetes consommation par usage, residentiel et tertiaire | via SDES |
| Agreste | Consommation agricole par usage | via SDES |
