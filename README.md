# Faisceau moteur M50B25 VANOS Turbo — MaxxECU RACE Gen1

Plan de fabrication complet d'un faisceau moteur sur mesure : BMW M50B25 VANOS
turbo en E36 (caisse vide), gestion MaxxECU RACE Gen1 (REV9+), papillon
motorisé, LSU 4.9, EGT, bobines intelligentes, injecteurs 870 cc, pompe 280 l/h,
ventilateur SPAL 385 mm.

Tout est généré depuis **un seul fichier** : on modifie la définition, on
relance le générateur, et planches, liste de coupe, nomenclature et contrôles
suivent. Aucun schéma n'est dessiné à la main, donc rien ne peut diverger.

## Ce que contient le dossier

| Fichier | Contenu |
|---|---|
| [`harness/m50b25_vanos_turbo.yaml`](harness/m50b25_vanos_turbo.yaml) | **Source de vérité** : brochage ECU officiel, composants, fils, épissures, fusibles/relais, topologie, audit, contrôles |
| [`docs/faisceau.html`](docs/faisceau.html) | Dossier interactif : brochage ECU cliquable, 13 planches, liste de coupe filtrable, fiches connecteurs, bilan énergie, formboard à l'échelle, check-lists |
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

### Utiliser le dossier à l'atelier (téléphone)

- **Barre du bas** : Coupe · Brochages (ECU et composants) · Planches · Contrôles · Plus (autres sections et recherche).
- **Planches** : glisser pour déplacer, pincer ou double-toucher pour zoomer, bouton plein écran.
  Toucher un fil l'encadre à taille lisible ; le panneau du bas donne longueur, couleur,
  saut vers chaque extrémité et fil précédent / suivant. Chaque fil porte son repère aux deux bouts.
- **Liens croisés** (coupe → planche → fiche connecteur…) : la pastille « ‹ Retour » en haut
  remonte niveau par niveau, à la même position dans la liste.
- **Liens directs** : ajouter `#IGN-03` (fil), `#COIL3` (composant), `#SNS` (planche) ou
  `#CMC1.A2` (broche ECU) à l'adresse ouvre directement l'élément.
- Les fils coupés et les contrôles cochés sont gardés sur l'appareil ; si le navigateur bloque
  le stockage (navigation privée), un avertissement l'indique.

### Contrôles automatiques (ERC)

- une broche ECU = un seul fil (sinon : épissure obligatoire) ;
- aucune masse de référence (Sensor GND, VR GND, Knock GND, blindages) reliée à la caisse ou au moteur ;
- aucun mélange +5 V / +12 V / +15 / masses dans un même réseau, aucune double source ;
- chaque fil protégé par un fusible compatible avec sa section ;
- charge de chaque fusible (alerte au-delà de 80 %) ;
- courant de chaque sortie ECU sous sa limite (GPO 2 A, GPO9 5 A, INJ 4 A en continu) ;
- section de chaque fil compatible avec son alvéole Molex CMC (0,75 mm² maxi en petite alvéole) ;
- chute de tension aller + retour des charges fortes (pompe, ventilateur), alerte au-delà de 3 % ;
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
6. **VANOS en direct sur GPO3**, comme sur le faisceau M50 de MaxxECU (électrovanne ≈ 8,5–12 Ω, 1,2–1,7 A < 2 A).
7. **ECU et boîte fusibles/relais dans l'habitacle** (E36 : la boîte électronique d'origine est côté turbo).
8. **Pompe et ventilateur en 4 mm²** sur relais, alimentés en direct batterie.
9. **Contact, démarreur et alternateur** : contacteur alimenté par F11 (5 A), relais de démarreur K4
   (F12 30 A, 2,5 mm² jusqu'à la borne 50), alternateur excité par un voyant de charge 2 W sur D+
   comme d'origine. Les câbles de puissance (batterie, B+ alternateur, tresses de masse) sont dans la nomenclature.

Le détail, les points validés et les sources sont dans `docs/rapport.md`.

## Hypothèses à confirmer

- E36 conduite à gauche ; ECU et PDM derrière la boîte à gants, traversée du tablier par passe-fil.
- Fusible général MAXI 80 A sur la borne B+ de la baie moteur.
- Pompe 280 l/h estimée à 15 A, ventilateur SPAL 385 mm aspirant à 19,5 A : à confirmer sur les étiquettes.
- Longueurs de tronçons estimées : à mesurer sur la voiture (dont démarreur et alternateur).
- Démarreur : solénoïde estimé à 10 A en maintien (30–40 A à l'appel, absorbé par le fusible 30 A temporisé).
