# Faisceau moteur M50B25 VANOS Turbo — MaxxECU RACE Gen1

Plan de fabrication complet d'un faisceau moteur sur mesure : BMW M50B25 VANOS
turbo, gestion MaxxECU RACE Gen1 (REV9+), papillon motorisé, LSU 4.9, EGT,
bobines intelligentes, injecteurs 870 cc.

Tout est généré depuis **un seul fichier** : on modifie la définition, on
relance le générateur, et planches, liste de coupe, nomenclature et contrôles
suivent. Aucun schéma n'est dessiné à la main, donc rien ne peut diverger.

## Ce que contient le dossier

| Fichier | Contenu |
|---|---|
| [`harness/m50b25_vanos_turbo.yaml`](harness/m50b25_vanos_turbo.yaml) | **Source de vérité** : brochage ECU officiel, composants, fils, épissures, fusibles/relais, topologie, audit, contrôles |
| [`docs/faisceau.html`](docs/faisceau.html) | Dossier interactif : brochage ECU cliquable, 12 planches, liste de coupe filtrable, fiches connecteurs, bilan énergie, formboard à l'échelle, check-lists |
| [`docs/rapport.md`](docs/rapport.md) | Rapport de vérification lisible sur GitHub (audit, ERC, fusibles, brochage) |
| [`docs/liste_de_coupe.csv`](docs/liste_de_coupe.csv) | Liste de coupe triée par section puis couleur (ouvrable dans Excel / LibreOffice, séparateur `;`) |
| [`docs/brochage_ecu.csv`](docs/brochage_ecu.csv) | Les 80 broches CMC1/CMC2 avec fil, section, couleur, destination |
| [`docs/nomenclature.csv`](docs/nomenclature.csv) | Connecteurs, contacts, fusibles, relais, épissures, mètres de fil par section/couleur, gaine, étiquettes |
| [`docs/harness.json`](docs/harness.json) | Données calculées complètes (pour d'autres outils) |
| [`tools/build_harness.py`](tools/build_harness.py) | Générateur + contrôle des règles électriques (ERC) |

## Utilisation

```bash
pip install pyyaml          # seule dépendance
python3 tools/build_harness.py
```

Le générateur affiche le bilan et **sort en erreur** si une règle est violée.
Ouvre ensuite `docs/faisceau.html` dans un navigateur.

### Contrôles automatiques (ERC)

- une broche ECU = un seul fil (sinon : épissure obligatoire) ;
- aucune masse de référence (Sensor GND, VR GND, Knock GND, blindages) reliée à la caisse ou au moteur ;
- aucun mélange +5 V / +12 V / +15 / masses dans un même réseau, aucune double source ;
- chaque fil protégé par un fusible compatible avec sa section ;
- charge de chaque fusible (alerte au-delà de 80 %) ;
- courant de chaque sortie ECU sous sa limite (GPO 2 A, GPO9 5 A, INJ 8 A) ;
- broches de composants non raccordées, épissures trop chargées.

### Modifier le faisceau

- **Longueurs** : section `topology`. Les tronçons sont des *estimations* ; mesure
  chaque tronçon sur la voiture (ficelle le long du trajet réel), reporte la
  valeur, régénère : toutes les longueurs de coupe et la gaine suivent.
- **Couleurs** : section `colors` / champ `color` de chaque fil.
- **Déplacer un fil** (ex. VANOS sur INJ7) : change `from: CMC1.D4` en `from: CMC1.L2`, régénère.

## Corrections apportées au plan d'origine

1. **Retour du capteur AAC sur VR GND (CMC1 H2)**, pas sur Sensor GND (H1) — schéma officiel RACE REV9+.
2. **Alimentation et masses ECU ajoutées** : M4 +12 V (15 A), L4 + CMC2 G4 au même goujon de culasse.
3. **Boîte fusibles/relais complète** : relais principal sur +15 clé, 11 fusibles, relais pompe et ventilateur.
4. **+12 V bobines en 1,0 mm²** (0,75 mm² non protégé par le fusible 15 A).
5. **Épissures** pour +5 V, Sensor GND, VR GND, Knock GND, blindages.
6. **À mesurer** : résistance de l'électrovanne VANOS (≥ 7,5 Ω → GPO3, sinon INJ7).

Le détail, les points validés et les sources sont dans `docs/rapport.md`.

## Hypothèses à confirmer

- ECU et boîte fusibles/relais dans le boîtier électronique d'origine (E-box).
- Pédale raccordée par un connecteur de cloison Deutsch DT 12 voies.
- Consommations pompe (15 A) et ventilateur (20 A) à ajuster selon tes modèles.
