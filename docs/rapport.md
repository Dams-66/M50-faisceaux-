# Faisceau moteur M50B25 VANOS Turbo — rapport de vérification

*MaxxECU RACE Gen1 (REV9+) · révision D · 2026-10-08 · Étude — à valider sur véhicule*

> Généré par `tools/build_harness.py` depuis `harness/m50b25_vanos_turbo.yaml`. Ne pas éditer à la main.

**134 fils** · **177.6 m de fil coupé** · 15 épissures/barrettes · 12 fusibles · 4 relais

## Contrôle des règles électriques : 0 erreur(s), 0 alerte(s)

- ℹ️ PWR-01 : liaison batterie → fusible général, garder la plus courte possible

## Audit du plan d'origine

### 🛠 Corrigé — Retour du capteur AAC sur VR GND (CMC1 H2), pas sur Sensor GND (H1)

Sur le schéma officiel RACE REV9+, le capteur PMH et le capteur AAC (VR ou Hall) ont leur retour sur VR GND (H2) ; les blindages PMH, AAC et lambda vont sur SHIELD GND (E3), ceux des capteurs de cliquetis sur KNOCK GND (CMC2 E1, page 2 du schéma). Ton plan mettait la broche 2 de l'AAC sur H1. Les deux retours (PMH broche 3 + AAC broche 2) se rejoignent par l'épissure SPL-VRG au ras du connecteur.

### ➕ Ajouté — Alimentation et masses de l'ECU (absentes du plan)

CMC1 M4 = +12 V ECU (fusible 15 A après relais principal). CMC1 L4 ET CMC2 G4 = masses moteur, toutes deux au MÊME goujon de culasse (exigence MaxxECU). Relais principal commandé par le +15 de l'interrupteur de contact : la RACE Gen1 n'a pas de sortie de commande de relais principal.

### ➕ Ajouté — Boîte fusibles/relais complète (PDM)

Fusible général MAXI 80 A, 11 fusibles (F1 à F5, F7 à F12 ; F6 regroupé dans F5 en révision D) et 4 relais : chaque circuit a son fusible et chaque fil est protégé par un fusible adapté à sa section (contrôle automatique).

### 🛠 Corrigé — Section des +12 V bobines : 1,0 mm² et non 0,75

Le fusible bobines est à 15 A (préconisation MaxxECU). Un fil de 0,75 mm² n'est protégé que jusqu'à 10 A : chaque dérivation bobine passe en 1,0 mm². Masses broche 4 (puissance) en 1,0 mm², broche 2 (électronique) en 0,75 mm².

### ✅ Validé — VANOS en direct sur GPO3, sans relais

C'est le câblage de MaxxECU sur son propre faisceau M50 : GPO3, connecteur Bosch JPT 2 voies, aucun relais. L'électrovanne simple VANOS 11361738494 (M50TU / M52 / S50 / S52) est relevée autour de 8,5–12 Ω, soit 1,2 à 1,7 A pour une limite GPO de 2 A. La valeur de 3,3 Ω qui circule vient d'un article sur le S50 du Z3 M, pas de cette électrovanne. Un contrôle de 10 s au multimètre reste conseillé : entre 3,6 et 7,5 Ω, passer sur INJ7 (CMC1 L2, 4 A en continu) ; sous 3,6 Ω, passer par un relais.

### ➕ Ajouté — ECU et fusibles dans l'habitacle (E36 caisse vide)

Sur un M50 en E36 conduite à gauche, la boîte électronique d'origine est côté échappement, donc côté turbo. ECU et boîte fusibles/relais passent derrière la boîte à gants, au frais et au sec ; le faisceau moteur traverse le tablier par un passe-fil étanche à l'emplacement d'origine. La pédale, l'interrupteur de contact, le bouton démarreur et le pad sont câblés en direct : plus de connecteur de cloison.

### ➕ Ajouté — Pompe 280 l/h et ventilateur SPAL 385 mm

Pompe : relais K2, fusible 20 A, alimentation et masse en 4 mm² pour limiter la chute de tension sur le trajet jusqu'au réservoir. Ventilateur SPAL 385 mm aspirant (19,5 A d'après la fiche SPAL VA18-AP71/LL-59A) : relais K3 40 A, fusible 30 A, fils 4 mm². Les deux sont alimentés en direct batterie, hors relais principal.

### 🛠 Corrigé — Révision C : audit électrique indépendant

Quatre relectures séparées (alimentation et masses, brochage ECU, brochage des composants, fabrication), chaque point contre-vérifié. Corrigé : chauffage lambda D1 en 0,75 mm² (petite alvéole CMC) ; sorties injecteur à 4 A en continu ; blindages de cliquetis sur KNOCK GND ; boîte à fusibles à 2 barrettes indépendantes et supports de relais séparés ; contacts, bouchons et épissures dimensionnés ; connecteur lambda côté faisceau et côté froid ; protection thermique côté turbo ; +12 V du capteur PMH hors câble blindé ; notes MTune (pull-up du trigger, papillon, chauffage, compte-tours).

### ➕ Ajouté — Révision D : contact sans clé, pad 8 boutons, F6 regroupé dans F5

Plus de clé : un interrupteur de contact alimenté par F11 donne le +15 (relais principal K1) et alimente le bouton démarreur mécanique, qui commande K4 ; le démarreur ne peut donc pas être lancé contact coupé. F11 reste nécessaire : c'est lui qui protège le fil qui va de la barrette +30 jusqu'à l'interrupteur. Le +12 V du capteur PMH est pris sur F5 avec la VANOS et la MAC (épissure à l'arrière de la culasse, 0,75 mm²). Plus de combiné : la sortie compte-tours (GPO8, CMC1 A4) est libre. Les boutons 4 à 8 du pad arrivent sur DIN1, DIN2, DIN4, DIN5 et AIN8 par une platine de 10 résistances de 10 kΩ, pull-up des entrées désactivé dans MTune.

### ⚠️ À vérifier — F5 commun : un court-circuit VANOS / MAC arrête le moteur

Avec le capteur PMH sur F5, un court-circuit sur l'électrovanne VANOS ou la MAC fait fondre F5 et coupe aussi le capteur PMH : le moteur cale, alors qu'avec un fusible séparé il continuait à tourner sans VANOS ni boost. C'est le prix d'un fusible en moins ; l'emplacement F6 reste libre si tu veux revenir en arrière.

### ⚠️ À vérifier — Entrées DIN / VR toutes occupées par le pad

DIN1, DIN2, DIN4 et DIN5 sont les seules entrées capables de lire un capteur de vitesse de roue ou de boîte (VR / Hall). Si tu en ajoutes un plus tard, le bouton le moins utile devra passer sur DIN3 (CMC1 C1), qui a un pull-up fixe et ne se commande qu'à la masse : il faudra alors un relais ou un transistor inverseur à la place de la platine 10 kΩ pour ce bouton.

### ➕ Ajouté — Contact, démarreur et alternateur ajoutés (oubli de la révision B)

Caisse vide : rien n'alimentait le contacteur, le démarreur ni l'excitation de l'alternateur. Ajouts : F11 5 A alimente la borne 30 du contacteur ; la borne 50 commande un relais de démarreur K4 (fusible F12 30 A, 2,5 mm² jusqu'au solénoïde) ; l'alternateur est excité comme d'origine, par un voyant de charge 2 W entre le +12 V commuté et D+. Les gros câbles (batterie → démarreur, B+ alternateur → démarreur, tresses de masse) sont listés dans la nomenclature, hors faisceau.

### ➕ Ajouté — Épissures obligatoires

Une alvéole CMC ne reçoit qu'un fil. +5 V, Sensor GND, VR GND, Knock GND et Shield GND passent par des épissures dédiées, placées au ras de l'ECU pour les références et sur la branche moteur pour les distributions.

### ✅ Validé — Brochage ECU conforme au schéma officiel RACE REV9+

IGN1→6 (A2, A3, B2, B3, C2, C3), INJ1→6 (K1, K2, M1, M2, M3, L3), GPO1/2/3/6 (B4, C4, D4, B1), entrées DIN1/2/4/5 et AIN8 du pad (K3, K4, CMC2 F3/F4/F2), lambda (G3, F3, D1, G4, F4), cliquetis (CMC2 E1/E2/E3, blindages sur KNOCK GND E1), EGT1 (CMC2 C1/D1), AIN5-7 (CMC2 G3, E4, F1), moteur papillon (CMC2 H4 + / H2 −) : tout est conforme.

### ✅ Validé — Capteur AAC 12141726590 = bonne solution pour une culasse VANOS

MaxxECU indique : capteur VANOS d'origine (Hall 12 V) incompatible avec son câblage, solution recommandée = capteur 12141726590 (broche 1 signal, 2 masse, 3 blindage). Aucun +12 V sur ce capteur.

### ✅ Validé — Papillon et pédale : affectation identique au plug-in MaxxECU M54

MaxxECU câble le M54 avec le papillon sur GPO11/12 (= Motor 1 −/+) et les pistes sur TPS + AIN3/4/5, exactement ton choix. Brochage papillon identique à la VDO 408-242 BMW documentée par MaxxECU.

### ✅ Validé — Capteurs Bosch 0 261 544 01F

Brochage confirmé : 1 non assignée, 2 pression (0,5–4,5 V = 0–10 bar), 3 +5 V, 4 masse, 5 NTC.

### ✅ Validé — Lambda LSU 4.9 sur contrôleur interne

Brochage conforme au schéma MaxxECU (vue côté câble) : 1 IP → G3, 2 COM → F3, 3 chauffage − → D1, 4 +12 V, 5 RCAL → G4, 6 VS → F4. Vérifie que ton boîtier est bien REV9 ou plus (étiquette).

### ⚠️ À vérifier — Capteur PMH Hall M52 sur cible 60-2 du M50

Le M50 d'origine utilise un capteur inductif en face de la cible 60-2 avant. Le capteur M52 (Hall, 12 V) demande un support et un entrefer adaptés. Dans MTune : entrée trigger en mode Digital (hall), pull-up interne activé (sinon pas de régime, pas de démarrage).

### ⚠️ À vérifier — Une seule alimentation +5 V et une seule Sensor GND

La RACE Gen1 n'a qu'un +5 V (G1) et qu'une Sensor GND (H1) : pédale et papillon les partagent. C'est normal ; un court-circuit sur le +5 V fait passer le papillon en sécurité. Consommation totale estimée ≈ 45 mA.

### 🛠 Corrigé — Alvéoles CMC : chauffage lambda (D1) en 0,75 mm²

CMC1 (Molex 64320) : rangées A à K = petites alvéoles CP 0.6 (0,75 mm² maxi), rangées L et M = grandes alvéoles CP 1.5. CMC2 (Molex 64319) : rangées A à F = CP 0.6, G et H = CP 1.5. Le fil de chauffage lambda en D1 était en 1,0 mm² : impossible à sertir et à étancher, il passe en 0,75 mm². Contacts : 64322-1039 pour 0,5 mm² et 64322-1029 pour 0,75 mm² en petite alvéole (K1, K2, B4, D4, D1) ; 64323-1029 pour 0,5–1 mm² et 64323-1039 pour 1–2 mm² en grande alvéole (L4, CMC2 G4). Bouchons 64325-1010 / 64325-1023 sur les alvéoles vides.

### ✅ Validé — Injecteurs 870 cc

La RACE a 8 sorties injecteur peak & hold (8 A crête, 4 A en continu) : haute ou basse impédance acceptées. Mesure la résistance pour régler le type dans MTune.

### ✅ Validé — MAP interne

Capteur interne MaxxECU RACE : jusqu'à 3 bar de pression de suralimentation. Durite directe depuis le plénum, aucun câblage.

## Fusibles

| Fusible | Circuit | Calibre | Section mini | Charge estimée | Taux |
|---|---|---|---|---|---|
| F0 | Fusible général | 80 A | 10 mm² | 62.4 A | 78% |
| F1 | Fusible ECU | 15 A | 1 mm² | 1.5 A | 10% |
| F2 | Fusible bobines | 15 A | 1 mm² | 6.0 A | 40% |
| F3 | Fusible injecteurs | 10 A | 0,75 mm² | 6.0 A | 60% |
| F4 | Fusible chauffage lambda | 10 A | 0,75 mm² | 1.5 A | 15% |
| F5 | Fusible actionneurs + capteur PMH (VANOS, MAC, PMH) | 10 A | 0,75 mm² | 2.2 A | 22% |
| F7 | Fusible commandes (bobines relais pompe / ventilo, voyant de charge) | 5 A | 0,35 mm² | 0.5 A | 9% |
| F8 | Fusible pompe à essence | 20 A | 1,5 mm² | 15.0 A | 75% |
| F9 | Fusible ventilateur | 30 A | 2,5 mm² | 19.5 A | 65% |
| F10 | Fusible relais principal | 30 A | 2,5 mm² | 17.6 A | 59% |
| F11 | Fusible interrupteur de contact / bouton démarreur | 5 A | 0,35 mm² | 0.3 A | 6% |
| F12 | Fusible démarreur (borne 50) | 30 A | 2,5 mm² | 10.0 A | 33% |

## Sorties ECU chargées

| Broche | Fonction | Charge | Courant | Limite |
|---|---|---|---|---|
| CMC1.A2 | IGNITION CYL 1 | COIL1 | 1.00 A | — |
| CMC1.A3 | IGNITION CYL 2 | COIL2 | 1.00 A | — |
| CMC1.B1 | GP OUT 6 | K3 | 0.15 A | 2 A |
| CMC1.B2 | IGNITION CYL 3 | COIL3 | 1.00 A | — |
| CMC1.B3 | IGNITION CYL 4 | COIL4 | 1.00 A | — |
| CMC1.B4 | GP OUT 1 | MAC | 0.45 A | 2 A |
| CMC1.C2 | IGNITION CYL 5 | COIL5 | 1.00 A | — |
| CMC1.C3 | IGNITION CYL 6 | COIL6 | 1.00 A | — |
| CMC1.C4 | GP OUT 2 | K2 | 0.15 A | 2 A |
| CMC1.D1 | WBO2 HTR (pin 3 LSU 4.9) / GP OUT 9 | LSU | 1.50 A | 5 A |
| CMC1.D4 | GP OUT 3 | VANOS | 1.20–1.69 A | 2 A |
| CMC1.K1 | INJECTOR CYL 1 | INJ1 | 1.00 A | 4 A |
| CMC1.K2 | INJECTOR CYL 2 | INJ2 | 1.00 A | 4 A |
| CMC1.L3 | INJECTOR CYL 6 | INJ6 | 1.00 A | 4 A |
| CMC1.M1 | INJECTOR CYL 3 | INJ3 | 1.00 A | 4 A |
| CMC1.M2 | INJECTOR CYL 4 | INJ4 | 1.00 A | 4 A |
| CMC1.M3 | INJECTOR CYL 5 | INJ5 | 1.00 A | 4 A |
| CMC2.H2 | MOTOR 1- / GPO 11 | ETB | 0.00 A | — |
| CMC2.H4 | MOTOR 1+ / GPO 12 | ETB | 0.00 A | — |

## Chutes de tension (charges fortes, aller + retour)

| Charge | Courant | Fils | Résistance | Chute |
|---|---|---|---|---|
| PUMP Pompe à essence | 15 A | RLY-08, RLY-06, RLY-09 | 17.9 mΩ | 0.27 V (2.0 %) |
| FAN Ventilateur électrique | 19.5 A | RLY-10, RLY-07, RLY-11 | 13.6 mΩ | 0.27 V (2.0 %) |
| STARTER Démarreur | 10 A | DEM-06, DEM-05 | 20.8 mΩ | 0.21 V (1.5 %) |

Consommation estimée sur le +5 V capteurs (G1) : **45 mA**.

## Brochage ECU

| Broche | Fonction | Fil | Section | Couleur | Vers |
|---|---|---|---|---|---|
| CMC1.A2 | IGNITION CYL 1 | IGN-01 | 0,5 | BU | COIL1.3 (Commande IGN) |
| CMC1.A3 | IGNITION CYL 2 | IGN-02 | 0,5 | BU | COIL2.3 (Commande IGN) |
| CMC1.B1 | GP OUT 6 | RLY-02 | 0,5 | GN | K3.85 (Bobine − (GPO6)) |
| CMC1.B2 | IGNITION CYL 3 | IGN-03 | 0,5 | BU | COIL3.3 (Commande IGN) |
| CMC1.B3 | IGNITION CYL 4 | IGN-04 | 0,5 | BU | COIL4.3 (Commande IGN) |
| CMC1.B4 | GP OUT 1 | ACT-01 | 0,75 | GN | MAC.2 (Commande GPO1) |
| CMC1.C2 | IGNITION CYL 5 | IGN-05 | 0,5 | BU | COIL5.3 (Commande IGN) |
| CMC1.C3 | IGNITION CYL 6 | IGN-06 | 0,5 | BU | COIL6.3 (Commande IGN) |
| CMC1.C4 | GP OUT 2 | RLY-01 | 0,5 | GN | K2.85 (Bobine − (GPO2)) |
| CMC1.D1 | WBO2 HTR (pin 3 LSU 4.9) / GP OUT 9 | WBO-05 | 0,75 | GN | LSU.3 (Chauffage −) |
| CMC1.D4 | GP OUT 3 | ACT-02 | 0,75 | GN | VANOS.2 (Commande (masse)) |
| CMC1.E1 | CAN H (120 Ω intégrée) | COM-12 | 0,5 | YE/BK | CANDEV.H (CAN H) |
| CMC1.E2 | CAN L | COM-13 | 0,5 | GN/BK | CANDEV.L (CAN L) |
| CMC1.E3 | SHIELD GND | SYNC-07 | 0,5 | BK/WH | SPL-SHLD (Blindages → Shield GND) |
| CMC1.F1 | COOLANT SENSOR (CLT) | SNS-12 | 0,5 | YE | CLT.1 (Signal NTC) |
| CMC1.F2 | AIR TEMP SENSOR (IAT) | SNS-11 | 0,5 | YE/BK | IAT.1 (Signal NTC) |
| CMC1.F3 | WBO2 COM | WBO-02 | 0,5 | YE | LSU.2 (VM / COM) |
| CMC1.F4 | WBO2 VS / O2 IN | WBO-04 | 0,5 | BN | LSU.6 (VS (UN / Nernst)) |
| CMC1.G1 | +5 V SENSOR SUPPLY | SNS-01 | 0,5 | OG | SPL-5V-MAIN (+5 V — départ ECU) |
| CMC1.G2 | THROTTLE SENSOR (TPS) | DBW-03 | 0,5 | WH | ETB.1 (TPS 1) |
| CMC1.G3 | WBO2 IP | WBO-01 | 0,5 | WH | LSU.1 (IP (pompe)) |
| CMC1.G4 | WBO2 RCAL | WBO-03 | 0,5 | GN | LSU.5 (RCAL (IA)) |
| CMC1.H1 | SENSOR GND | SNS-05 | 0,5 | BN | SPL-SG-MAIN (Sensor GND — départ ECU) |
| CMC1.H2 | VR GND | SYNC-06 | 0,5 | BN | SPL-VRG (VR GND (PMH + AAC)) |
| CMC1.H3 | TRIGGER | SYNC-01 | 0,5 | WH | CRANK.2 (Signal Hall) |
| CMC1.H4 | HOME / CAM | SYNC-04 | 0,5 | WH | CAM.1 (Signal (+)) |
| CMC1.J1 | ANALOG IN 1 (TEMP) | SNS-13 | 0,5 | YE/BN | OIL.5 (Température NTC) |
| CMC1.J2 | ANALOG IN 2 (TEMP) | SNS-15 | 0,5 | YE/VT | FUEL.5 (Température NTC) |
| CMC1.J3 | ANALOG IN 3 (0-5 V) | DBW-04 | 0,5 | WH/BK | ETB.4 (TPS 2) |
| CMC1.J4 | ANALOG IN 4 (0-5 V) | DBW-10 | 0,5 | WH/BU | APP.4 (Signal piste 1) |
| CMC1.K1 | INJECTOR CYL 1 | INJ-01 | 0,75 | GY | INJ1.2 (Commande ECU) |
| CMC1.K2 | INJECTOR CYL 2 | INJ-02 | 0,75 | GY | INJ2.2 (Commande ECU) |
| CMC1.K3 | DIGITAL IN 1 | COM-06 | 0,5 | WH/RD | IF-PAD.6 (Sortie voie 1 → DIN1) |
| CMC1.K4 | DIGITAL IN 2 | COM-07 | 0,5 | WH/OG | IF-PAD.7 (Sortie voie 2 → DIN2) |
| CMC1.L3 | INJECTOR CYL 6 | INJ-06 | 0,75 | GY | INJ6.2 (Commande ECU) |
| CMC1.L4 | ENGINE GROUND | GND-01 | 1,5 | BK | GP-HEAD (Masse moteur ECU (goujon arrière culasse)) |
| CMC1.M1 | INJECTOR CYL 3 | INJ-03 | 0,75 | GY | INJ3.2 (Commande ECU) |
| CMC1.M2 | INJECTOR CYL 4 | INJ-04 | 0,75 | GY | INJ4.2 (Commande ECU) |
| CMC1.M3 | INJECTOR CYL 5 | INJ-05 | 0,75 | GY | INJ5.2 (Commande ECU) |
| CMC1.M4 | +12 V ECU | PWR-05 | 1 | RD/WH | F1.2 (Sortie) |
| CMC2.C1 | EGT1+ | WBO-07 | 0,5 | YE | EGT1.+ (K+ (chromel)) |
| CMC2.D1 | EGT1- | WBO-08 | 0,5 | RD | EGT1.- (K− (alumel)) |
| CMC2.E1 | KNOCK GND | KNK-05 | 0,5 | BN | SPL-KGND (Knock GND (2 capteurs)) |
| CMC2.E2 | KNOCK 1 | KNK-01 | 0,5 | WH | KS1.1 (Signal) |
| CMC2.E3 | KNOCK 2 | KNK-03 | 0,5 | WH | KS2.1 (Signal) |
| CMC2.E4 | ANALOG IN 6 (0-5 V) | SNS-14 | 0,5 | WH/BN | OIL.2 (Pression 0,5–4,5 V) |
| CMC2.F1 | ANALOG IN 7 (0-5 V) | SNS-16 | 0,5 | WH/VT | FUEL.2 (Pression 0,5–4,5 V) |
| CMC2.F2 | ANALOG IN 8 (0-5 V) | COM-10 | 0,5 | WH/YE | IF-PAD.10 (Sortie voie 5 → AIN8) |
| CMC2.F3 | DIGITAL / VR IN 4 | COM-08 | 0,5 | WH/GY | IF-PAD.8 (Sortie voie 3 → DIN4) |
| CMC2.F4 | DIGITAL / VR IN 5 | COM-09 | 0,5 | WH/PK | IF-PAD.9 (Sortie voie 4 → DIN5) |
| CMC2.G3 | ANALOG IN 5 (0-5 V) | DBW-12 | 0,5 | WH/GN | APP.6 (Signal piste 2) |
| CMC2.G4 | ENGINE GROUND 2 | GND-02 | 1,5 | BK | GP-HEAD (Masse moteur ECU (goujon arrière culasse)) |
| CMC2.H2 | MOTOR 1- / GPO 11 | DBW-06 | 1 | PK/BK | ETB.5 (Moteur −) |
| CMC2.H4 | MOTOR 1+ / GPO 12 | DBW-05 | 1 | PK | ETB.3 (Moteur +) |

Broches libres : CMC1.A1 (GP OUT 5), CMC1.A4 (TACH / GP OUT 8), CMC1.C1 (GP OUT 7 / DIGITAL IN 3), CMC1.D2 (IGNITION CYL 7), CMC1.D3 (IGNITION CYL 8), CMC1.E4 (GP OUT 4), CMC1.L1 (INJECTOR CYL 8), CMC1.L2 (INJECTOR CYL 7), CMC2.A1 (EGT5+), CMC2.A2 (EGT6+), CMC2.A3 (EGT7+), CMC2.A4 (EGT8+), CMC2.B1 (EGT5-), CMC2.B2 (EGT6-), CMC2.B3 (EGT7-), CMC2.B4 (EGT8-), CMC2.C2 (EGT2+), CMC2.C3 (EGT3+), CMC2.C4 (EGT4+), CMC2.D2 (EGT2-), CMC2.D3 (EGT3-), CMC2.D4 (EGT4-), CMC2.G1 (GP OUT 15 (+12 V, 2 A)), CMC2.G2 (GP OUT 16 (+12 V, 2 A)), CMC2.H1 (MOTOR 2+ / GPO 14), CMC2.H3 (MOTOR 2- / GPO 13)

## Réglages MTune liés au câblage

| Fonction | Réglage |
|---|---|
| Trigger | 60-2 vilebrequin sur TRIGGER H3 : Sensor type = Digital (hall), Trigger pullup resistor = ACTIVÉ (1 kΩ interne vers +5 V), seuils par défaut ; front à valider à l'oscilloscope MTune |
| Home / cam | Capteur inductif (VR) sur HOME H4 |
| Injecteurs | INJ1→6 séquentiel ; type selon résistance mesurée (haute / basse impédance) |
| Allumage | IGN1→6, bobines à allumeur intégré (sortie active 5 V) ; dwell selon doc bobine |
| E-throttle | Output config : GPO12 (CMC2 H4) = E-throttle 1 motor +, GPO11 (CMC2 H2) = E-throttle 1 motor − ; entrées : TPS G2 = E-throttle 1 position MAIN, AIN3 J3 = position BACKUP, AIN4 J4 = pedal position MAIN, AIN5 CMC2 G3 = pedal position BACKUP |
| CLT / IAT | Courbes Bosch NTC |
| AIN1 / AIN2 (temp.) | Température huile / essence, NTC Bosch du 0 261 544 01F |
| AIN6 / AIN7 | Pression huile / essence 0,5–4,5 V = 0–10 bar |
| Knock | Knock 1 (cyl. 1-2-3) et Knock 2 (cyl. 4-5-6) |
| Lambda | Output config : GPO9 (CMC1 D1) = internal lambda sensor heater (sensor 1) ; WBO2 interne, capteur Bosch LSU 4.9 sélectionné AVANT la première mise sous tension sonde montée |
| EGT | EGT1 type K |
| GPO1 | Boost control (MAC), PWM ~30 Hz |
| GPO2 | Fuel pump (relais K2) |
| GPO3 | VANOS tout-ou-rien (seuil de régime / charge à définir sur la cartographie) |
| GPO6 | Engine fan (relais K3) |
| Pad : DIN1, DIN2, DIN4, DIN5 | Inputs → Digital inputs : Input type = Digital input, Pullup = OFF (obligatoire avec la platine 10 kΩ), Latch = None (le bouton du pad en mode Toggle tient l'état), Active level = rising sauf ALS off |
| DIN1 (CMC1 K3) — bouton 4 | Ventilation forcée : Function = Fan override input (force la sortie Engine fan GPO6 quelle que soit la température) |
| DIN2 (CMC1 K4) — bouton 5 | Changement de carto : Function = Boost target switch (consigne de boost 2). Si la carto 2 change aussi l'avance ou la richesse : Internal output system, condition « DIN2 actif » → Extra fuel/ign table activation switch (all), tables extra réglées en « … when input active » |
| DIN4 (CMC2 F3) — bouton 6 | ALS off : Anti-lag → Activation method = Switch input ; DIN4 Function = Anti-lag enable, Active level = falling : ALS autorisé bouton éteint, coupé bouton allumé. Attention : pad éteint ou fil coupé = ALS autorisé ; pour l'inverse, Active level = rising et le bouton devient « ALS ON » (aucun recâblage). Garder Min CLT, Max EGT et le timeout |
| DIN5 (CMC2 F4) — bouton 7 | Carto de chauffe : Function = RPM limit, use secondary limit RPM (limiteur bas, ex. 4000 tr/min) ; option : Internal output system « DIN5 actif » → Extra ignition table 2 activation switch pour une avance de chauffe |
| AIN8 (CMC2 F2) — bouton 8 | Refroidissement : Analog input 8 → Use as = Digital input (seuil 3,0 V), Active level = rising, Function = FAN + Electric waterpump override input (ventilateur forcé) ; à compléter par l'Internal output system si tu veux aussi limiter le régime ou couper le boost pendant le tour de refroidissement |
