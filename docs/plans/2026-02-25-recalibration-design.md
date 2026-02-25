# Design — Recalibration du modele sur le referentiel SDES 2023

**Date** : 2026-02-25
**Prerequis** : `docs/plans/2026-02-25-reference-consumption-table.md`
**Approche** : B — Reconstruction guidee par le referentiel
**Tests** : Repartir de zero, alignes sur le referentiel

---

## 1. Probleme

Le modele v0.7.0 sous-estime la consommation de 42% (935 TWh vs 1 615 TWh SDES 2023).
Cause racine : le modele part de la consommation deja electrifiee au lieu de partir
de la consommation actuelle et d'appliquer les conversions.

## 2. Architecture cible

### 2.1 Nouveau coeur : `consumption.py`

```
consumption.py
  |
  +- ReferenceData          SDES 2023 encode : 6 secteurs x sous-usages x vecteurs
  |   +- SectorReference    Un secteur (ex: residentiel, 422 TWh)
  |   +- UsageReference     Un usage (ex: chauffage, 312 TWh, decompose par vecteur)
  |
  +- ElectrificationParams  Knobs de conversion (COP, facteurs VE, rendements)
  |
  +- SectorBalance          Resultat par secteur : {elec, h2, bio_enr, fossile, total}
  +- SystemBalance          Resultat systeme : 6 secteurs + agregats + verifications
  |
  +- sdes_2023()                     -> ReferenceData pre-rempli (1 615 TWh)
  +- calculate_system_balance()      -> SystemBalance (733 TWh elec total)
  +- convert_residential()           -> SectorBalance (175 elec, 127 bio, 0 H2)
  +- convert_tertiary()              -> SectorBalance (120 elec, 8 bio, 2 fos)
  +- convert_industry()              -> SectorBalance (162 elec, 23 H2, 22 bio, 15 fos)
  +- convert_transport()             -> SectorBalance (118 elec, 33 H2, 45 bio, 49 fos)
  +- convert_agriculture()           -> SectorBalance (16 elec, 5 H2, 11 bio, 4 fos)
  +- convert_non_energy()            -> SectorBalance (5 elec, 28 H2, 27 bio, 35 fos)
```

Verifications integrees :
- `ReferenceData.__post_init__()` : total == 1 615 TWh
- `UsageReference.__post_init__()` : somme vecteurs == total
- `SystemBalance.check_consistency()` : elec + h2_prod == total_electricity

### 2.2 Dataclasses

**UsageReference** : un usage dans un secteur
```
name, total_twh, elec_twh, gaz_twh, petrole_twh, charbon_twh, enr_twh, reseau_twh
Controle : somme des vecteurs == total_twh
```

**SectorReference** : un secteur complet
```
name, usages: list[UsageReference]
Controle : somme des usages == total du secteur
```

**ReferenceData** : les 6 secteurs
```
residential (422), tertiary (229), industry (283),
transport (513), agriculture (55), non_energy (113)
Controle : grand total == 1 615
```

**ElectrificationParams** : tous les knobs de conversion
```
Residentiel : res_chauffage_cop=3.5, res_ecs_cop=3.0, res_elec_specifique_gain=0.15
Tertiaire   : ter_renovation_gain=0.30, ter_chauffage_cop=3.0, ter_led_gain=0.50
Industrie   : ind_ht_elec_fraction=0.30, ind_ht_h2_fraction=0.24, ind_mt_cop=2.25
Transport   : tpt_vp_ev_factor=0.33, tpt_pl_battery_fraction=0.50, tpt_pl_h2_fraction=0.25
Agriculture : agr_machinisme_ev_fraction=0.40, agr_serres_cop=3.0
Systeme     : electrolyse_efficiency=0.65, ccgt_efficiency=0.55
```

**SectorBalance** : resultat par secteur
```
name, current_twh, elec_twh, h2_twh, bio_enr_twh, fossil_residual_twh,
total_target_twh, reduction_pct
```

**SystemBalance** : resultat global
```
sectors: dict[str, SectorBalance]
current_total_twh: 1615
direct_electricity_twh: 596
h2_demand_twh: 89
h2_production_elec_twh: 137
total_electricity_twh: 733
bio_enr_twh: 240
fossil_residual_twh: 105
```

### 2.3 Logique de conversion

Principe commun pour chaque usage :
1. Prendre la decomposition par vecteur actuel (SDES)
2. Fossile (gaz + petrole + charbon) -> PAC/COP ou facteur electrification
3. Bois/EnR/reseau -> maintenu (sauf renovation qui reduit le besoin)
4. Electrique existant -> maintenu avec gains efficacite
5. Verifier que la somme des vecteurs cible == total cible

Cas special industrie : 3 niveaux de temperature + H2 pour HT/MT.
Cas special transport : etapes sequentielles (modal shift, sobriete, puis conversion).
Cas special non-energie : H2 pour engrais (Haber-Bosch), e-chemicals, pas de COP.

### 2.4 Role des modules existants : profils temporels

Les modules existants ne calculent plus les totaux. Ils fournissent des
profils normalises (somme = 1.0) que l'on multiplie par les totaux de consumption.py.

```
consumption.py  ->  "combien" (totaux annuels par vecteur)
heating.py      ->  "quand"   (repartition mensuelle chauffage, physique Roland)
transport.py    ->  "quand"   (profil recharge VE par creneau horaire)
agriculture.py  ->  "quand"   (profil saisonnier irrigation, moisson)
```

Controle : sum(profil × total) sur 60 creneaux == total annuel de consumption.py.

### 2.5 Flux de donnees

```
SDES 2023 (ReferenceData) + Hypotheses (ElectrificationParams)
          |
          v
    consumption.py -> SystemBalance (totaux annuels)
          |
          +-->  heating.py     -> profil mensuel chauffage (normalise)
          +-->  transport.py   -> profil recharge VE (normalise)
          +-->  agriculture.py -> profil saisonnier (normalise)
          |
          v
    energy_balance  -> bilan offre/demande par creneau (60 periodes)
          |
          v
    sensitivity.py  -> gaz backup (~190 TWh)
          |
          v
    tarification.py -> prix au MWh (derive, pas hard-code)
```

## 3. Impact sur les fichiers existants

### Conserves tels quels (5)
- sources.py, temporal.py, data_ingestion.py, emissions.py, trajectory.py

### Modifies (10)
- config.py : supprimer ConsumptionConfig legacy, garder ProductionConfig/StorageConfig
- heating.py : bilan_chauffage_annuel() -> profil_chauffage_normalise() (12 coeff)
- transport.py : bilan_transport() -> profil_recharge_normalise() (60 coeff)
- agriculture.py : bilan_agriculture() -> profil_agriculture_normalise() (12 coeff)
- secteurs.py : supprimer IndustrieConfig/TertiaireConfig (migrent vers consumption.py)
- sensitivity.py : recevoir total_electricity_twh de consumption.py
- tarification.py : supprimer consommation_totale_twh=700, deriver de consumption.py
- rapport.py : source unique = consumption.py, ajouter section bilan referentiel
- energy.py : verifier compatibilite (formule kW*h->TWh inchangee)
- production.py : inchange dans la logique

### Crees (3)
- src/consumption.py : nouveau coeur
- tests/test_consumption.py : tests niveaux 1-3 (~60 tests)
- tests/test_profiles.py : tests niveau 4 (~20 tests)

### Supprimes
- Tous les tests existants (repartir de zero)

## 4. Strategie de tests (~80 tests)

### Niveau 1 — Bilan systeme (<10 tests)
- Total SDES == 1615, electricite == 733, H2 == 89, fossile == 105
- Somme des vecteurs == total pour chaque secteur
- Somme des vecteurs actuels == total pour chaque usage

### Niveau 2 — Sectoriels (~30 tests)
- 6 secteurs x 5 metriques (elec, h2, bio, fossile, reduction%)
- Valeurs cibles du referentiel avec tolerance +-5 TWh

### Niveau 3 — Sensibilite (~20 tests)
- COP plus haut -> moins d'electricite
- Plus de H2 PL -> plus de H2 total
- Facteur VE plus bas -> moins d'electricite transport
- Direction + amplitude raisonnable

### Niveau 4 — Profils temporels (~20 tests)
- Profils normalises somment a 1.0
- Chauffage : janvier > juillet
- Agriculture : ete > hiver (irrigation)
- Total distribue sur 60 creneaux == total annuel

## 5. Ecarts combles par la recalibration

| Ecart                  | Avant (v0.7.0) | Apres     |
|------------------------|----------------|-----------|
| Consommation totale    | ~935 TWh       | 1 615 TWh |
| Residentiel chauffage  | 55-92 TWh elec | 312 TWh actuel -> 175 TWh elec |
| Industrie              | 205 TWh bloc   | 283 TWh x 7 usages |
| Usages non-energetiques| absent         | 113 TWh x 6 usages |
| Production H2          | absent         | 89 TWh H2 -> 137 TWh elec |
| Tarification base      | 700 TWh fixe   | 733 TWh derive |
| Gaz backup             | 114 TWh        | ~190 TWh (recalcule) |
| Controle exhaustivite  | aucun          | assertions automatiques |
