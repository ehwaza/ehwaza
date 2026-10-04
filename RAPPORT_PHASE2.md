# RAPPORT — PHASE 2 : LE MIEL AJOUTE-T-IL SUR UNE ABEILLE COMPÉTENTE ?

**Date :** 2026-10-04 · **Auteurs :** Claude (harnais, agrégateur, éval) × LYNX (protocole, entraineur, abeilles) ·
**Statut :** compute-matched ET step-matched rendus (2 lots, S = 10 × 3 niches, 54 runs step tous rc 0, `step_matched_strict=true`).

---

## 0. Question

Phase 1 (répondue) : *le miel PORTE-t-il du signal ?* → OUI (corrige un neuf **gelé à la chance**).
**Phase 2 :** *le miel ajoute-t-il un gain MARGINAL sur une abeille neuve **COMPÉTENTE** (acc base ~.6–.7) ?*

---

## 1. ENGAGEMENT / GÉNÉALOGIE (scellé avant tout run)

| Élément | Valeur |
|---|---|
| Probe scellé | `probe_phase2.npz` — sha256 `29444f0e451bacb0a878252ebd5d9b90911ab0e0f5f02b2941dd1ad853b14c78` (sha1 `03be8a18…`) |
| Graine probe | `20261005`, n = 2000 (⊥ niches 7/8/9) ; déterminisme vérifié |
| Miel (fold → npz) | `miel_phase1.npz` — sha256 `619105c33f5aed5e60b2c156a94b24bf815c405ea7a0e6eb20081a1fb70997af` (unigramme, k=5) |
| Graines | n0 = data 17…26 / init 2017…2026 · n1 = 27…36 / 2027…2036 · n2 = 37…46 / 2037…2046 |
| Réutilisation | n0 17/18/19 = `p2_pilote` (pilote) ; step n0 17/18/19 = `p2_step` |
| Genome | heldout `03ff6fbc…` + code_sha `1ac15d6fc88c` + arch nv=39, **identiques sur tous les runs** |
| β | 0.5 **figé avant tout résultat** ; cible-miel knob-free (seuil 0.5 = spec DUR v1) |
| Chance (base) | 1/39 = 0.026 · **base compétente ~0.6–0.7** (le point nouveau de Phase 2) |
| Erratum | consult k=5 (le run v1 de Phase 1 utilisait k=39 par erreur — corrigé) |

---

## 2. HEADLINE

1. **Le miel est un OUTIL DE TROUS :** sur une abeille compétente, il ajoute **+0.29 à +0.40** d'accuracy (compute) / **+0.31 à +0.43** (step) là où la bee est **ignorante** (les autres niches), et **~0 à légèrement négatif** sur **sa propre niche**.
2. **Le miel est un POISON AU CUIT :** faire *apprendre* la bee avec la cible-miel (bras A) **dégrade sa niche propre** — robuste sur 10 graines × 3 niches, **ET à pas égal** : essence A = −0.036 / −0.007 / −0.034 (step), IC < 0 les 3 niches ; le signe tient, le déficit de pas n'en portait qu'une partie de la magnitude.

---

## 3. MÉTHODE — 4 cellules appariées

| | éval **sans** miel | éval **avec** miel (souple β=0.5) |
|---|---|---|
| entraînement **T_nu** (cibles onehot y) | **E0** | **E1** |
| entraînement **T_miel** (cible miel §protocole) | **E2** | **E3** |

- **(B) primaire = E1 − E0** — valeur d'inférence sur un compétent.
- **(A) primaire = E2 − E0** — effet PUR des poids (éval sans consult).
- Appariement strict : même graine d'init, même ordre de données ; **seul le miel-cible diffère** (T_miel vs T_nu).
- Gel à l'éval : poids figés, miel au `consult` seulement ; la bee est **entraînée** (compétente, ~.6–.7).
- Cible-miel (A) : `sk>0.5 → target = sk·onehot(maj) + (1−sk)·onehot(y)`, sinon `onehot(y)`.
- **P6 (obligatoire)** : taux d'activation de la cible-miel mesuré — un non-usage rendrait un nul **mécanique**.

---

## 4. RÉSULTATS — compute-matched (primaire, 10 graines × 3 niches)

Chaque abeille est lue **sur sa propre niche** (essence) vs les autres (transfert). IC95 bootstrap 2000/graine5.

### (B) inférence sur un compétent — B = E1−E0

| niche | taux act. | essence (sa niche) | transfert (angles morts) |
|---|---|---|---|
| n0 rep | ~45 % | −0.0020 IC[−0.0081, +0.0048] *(croise 0)* | **+0.3176** IC[+0.2970, +0.3361] |
| n1 arith\|miroir | ~25 % | **−0.0217** IC[−0.0278, −0.0150] *(nég.)* | **+0.2861** IC[+0.2628, +0.3076] |
| n2 saut\|rnd | ~35 % | −0.0006 IC[−0.0017, +0.0004] *(croise 0)* | **+0.4045** IC[+0.3933, +0.4155] |

→ **Angles morts : +0.29 à +0.40, les 3 niches, IC > 0.** Niche propre : ~0 (n0/n2) ou **négatif** (n1, −0.022).

### (A) entraînement avec la cible-miel — A = E2−E0

| niche | essence (sa niche) | transfert |
|---|---|---|
| n0 rep | **−0.0362** IC[−0.0468, −0.0263] | +0.0187 IC[+0.0140, +0.0237] |
| n1 arith\|miroir | **−0.0311** IC[−0.0412, −0.0212] | +0.0003 IC[−0.0005, +0.0010] |
| n2 saut\|rnd | **−0.0419** IC[−0.0509, −0.0317] | +0.0014 IC[+0.0002, +0.0028] |

→ **Cuire le miel dans les poids NUIT à la niche propre, les 3 niches (−0.031 à −0.042, robuste 10 graines).** Transfert : ~nul (n1/n2) à petit positif (n0).

**Lecture** : deux mécanismes opposés et tous deux mesurés — l'**épisodique se consulte** (B transfert ≫ 0), le **générique ne se cuit pas** (A essence < 0).

---

## 5. RÉSULTATS — step-matched (n = 50000 fixe, 54 runs, `step_matched_strict=true`)

Lot step rendu (9 vagues de 6 runs, **tous rc 0**). Même verdict lu **côte à côte** : le négatif de (A) essence tenait-il à **pas égal** (effet réel) ou était-il porté par le **déficit de pas** du bras miel (~6 %, partie du traitement) ? Réponse : **il tient** — signe négatif conservé, IC < 0, les 3 niches, 30 graines.

### (B) inférence — B = E1−E0 (compute | step)

| niche | taux act. | essence compute | essence step | transfert compute | transfert step |
|---|---|---|---|---|---|
| n0 rep | ~45 / 44.6 % | −0.0020 *(croise 0)* | +0.0063 *(croise 0)* | +0.3176 | +0.3122 |
| n1 arith\|miroir | ~25 / 25.0 % | −0.0217 *(nég.)* | −0.0278 *(nég.)* | +0.2861 | +0.3175 |
| n2 saut\|rnd | ~35 / 34.5 % | −0.0006 *(croise 0)* | −0.0008 *(croise 0)* | +0.4045 | +0.4297 |

→ **Transfert stable et fort aux deux budgets** (+0.31 / +0.32 / +0.43), IC > 0 partout. La valeur du miel sur les **angles morts** ne dépend pas du budget de pas.

### (A) entraînement avec la cible-miel — A = E2−E0 (compute | step)

| niche | essence compute | essence step | transfert compute | transfert step |
|---|---|---|---|---|
| n0 rep | −0.0362 IC[−0.0468,−0.0263] | **−0.0365** IC[−0.0468,−0.0258] | +0.0187 | +0.0186 |
| n1 arith\|miroir | −0.0311 IC[−0.0412,−0.0212] | **−0.0074** IC[−0.0133,−0.0016] | +0.0003 | +0.0000 |
| n2 saut\|rnd | −0.0419 IC[−0.0509,−0.0317] | **−0.0339** IC[−0.0403,−0.0274] | +0.0014 | +0.0008 |

→ **Le négatif de (A) essence est un EFFET, pas un artefact de pas** : signe conservé, IC < 0, 30 graines. Le déficit de pas gonflait la magnitude sur n1 (−0.031 → −0.007) et n2 (−0.042 → −0.034) ; il ne portait **pas** le signe. n0 est identique (−0.0362 → −0.0365).

### Lecture globale (les deux lots)

- **(B) transfert ≫ 0** aux deux budgets → « l'épisodique se consulte », robuste.
- **(A) essence < 0** aux deux budgets → « le générique ne se cuit pas », robuste.
- **Secondaires** (step) : E3−E0 essence = −0.084 / −0.032 / −0.057 (tout-miel + consult pire que rien sur sa niche) ; E3−E1 essence = −0.091 / −0.005 / −0.057.
- **P6** : taux d'activation de la cible-miel, step = 44.6 / 25.0 / 34.5 % (compute 45 / 25 / 35) → le levier s'est déclenché aux deux budgets ; le négatif de (A) n'est **pas** mécanique.

---

## 6. GLOSSAIRE

- **Compute-matched** : même budget machine. **Step-matched** : même nombre de pas (`n=50000`).
- **(B)** = inférence (miel consulté à l'éval). **(A)** = entraînement (miel dans la cible).
- **Essence** = règles de la niche de la bee ; **transfert** = règles des autres (ses angles morts).
- **P6** = taux d'activation de la cible-miel ; sans activation, un nul de (A) est mécanique.

---

## 7. LIMITES

- Base **compétente** (acc ~0.6–0.7) : le verdict est « miel marginal sur un compétent », plus « bat le hasard ».
- **S = 10** (plancher protocole) : verdict **directionnel + largeur par bloc** ; δ = 0.02 **non promis**.
- Chevauchement probe = upper bound (histogramme). Condition de run : machine partagée avec les outils LYNX (~14 % résiduel).
- **Step-matched rendu** (§5) : le **signe** de (A) essence tient à pas égal (30 graines, IC < 0) ; la **magnitude** était partiellement gonflée par le déficit de pas sur n1/n2 (n0 inchangé).

---

## 8. OUVERTURE — Phase 3 (hors scope, voir PROTOCOLE_PHASE2.md annexe)

Candidats notés, **non validés** : miel **bigramme** (observation unigramme = ranking quasi-nul sur un corpus de prose N≈12 ; à figer comme *préliminaire sur ce corpus*), = **un** candidat parmi d'autres (n-grammes, vec IDF, hashing). Tout chiffre d'utilité exige **nouveau probe scellé + 2×2 cellules + S graines**. Ordre : Phase 2 CLOSE d'abord.

---

*Fichiers : `test_de_vie_phase2.py`, `charger_miel.py`, `runs_plein_local.json`, `rapport_p2_plein.json` (compute) · `runs_step_plein_local.json`, `rapport_p2_step_plein.json`, `step_plein_meta.json` (step).*
