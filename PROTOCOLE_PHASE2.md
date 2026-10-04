# PROTOCOLE PHASE 2 — PRÉ-ENREGISTRÉ

**Statut :** BROUILLON POUR COUNTER-SIGNATURE (Claude) → SCELLÉ (nouveau probe) → **VERT MATHIEU** (aucun run avant).
**Date :** 2026-10-04 · **Auteurs :** LYNX (protocole + futur code cible-miel) × Claude (harnais, scellement probe, fold).
**Règle :** ce document est figé AVANT tout run. Toute déviation = nouvelle version datée + justification, jamais d'ajustement après tirage.

---

## 1. Question (une seule, énoncée avant tout)

Phase 1 (répondu) : *le miel PORTE-t-il du signal ?* → OUI (corrige un neuf **gelé à la chance**, souple + dur, 3 niches).
**Phase 2 :** *le miel ajoute-t-il un gain MARGINAL sur une abeille neuve COMPÉTENTE (acc base ~.6–.7) ?*

Deux modalités déclarées, rendues **côte à côte** comme (souple, dur) en Phase 1 :
- **(A) — entraînement :** le miel influence les POIDS (cible modulée, §3).
- **(B) — inférence :** entraînement identique dans les 2 bras, miel consulté **à l'eval seulement**.

---

## 2. Cellules (2×2) et appariement

| | eval **sans** miel | eval **avec** miel (souple β=0.5) |
|---|---|---|
| entraînement **T_nu** (cibles `onehot(y)`) | **E0** (référence) | **E1** |
| entraînement **T_miel** (cibles §3) | **E2** | **E3** |

**Contrasts déclarés :**
- **(B) primaire = E1 − E0** — valeur marginale d'inférence sur compétent (héritage direct de Phase 1, base compétente).
- **(A) primaire = E2 − E0** — effet PUR des poids, éval sans consult (isole « cuit dans les poids »).
- Secondaires : **E3 − E0** (tout-miel vs rien), **E3 − E1** (apport de l'entraînement quand on consulte déjà).

**Appariement STRICT :** même graine d'init, même ordre de données, même archi/pools ; **seul le miel-cible diffère** entre T_miel et T_nu. Éval des 4 cellules sur le même probe scellé.

**Consult (eval) = le miel de ruche FIXE seul** — le fold des 3 lignes Phase 1 (`cfebe88d…`), chargé t=0, **jamais mis à jour pendant le run**, jamais la mémoire propre du neuf en croissance (anti-auto-leak). Identique aux 4 cellules → comparable aux chiffres Phase 1.

---

## 3. Mécanisme (A) — cible miel, KNOB-FREE

Pour un item **entraîné**, consult sur le miel fixe **avant** `add` :
- si **sk > 0.5** : `target = sk·onehot(maj) + (1−sk)·onehot(y)`
- sinon : `target = onehot(y)`

- Pas de λ libre : le seul coefficient est **sk lui-même** ; le seuil 0.5 est **déjà** celui du mode DUR de la spec v1 (pas un nouveau knob).
- T_nu : aucune cible miel, jamais.
- **Télémétrie obligatoire (sinon un nul est non-interprétable) :** taux d'activation de la cible-miel (fraction des items d'entraînement avec sk>0.5), par niche et par strate ; distribution sk des consultations d'entraînement (moy/p50/p90/p99/max).

---

## 4. Modes d'éval

- **SOUPLE (primaire) :** `p = (1−β)·p_modele + β·p_knn`, **β = 0.5 FIGÉ** (même valeur que Phase 1, figée avant tout résultat — pas de sweep).
- **DUR (témoin) :** `sk>0.5 → pred=maj, conf=sk`. Rendu, jamais lu seul.

---

## 5. Strates et blocs (pré-déclarés, verbatim Phase 1)

- Blocs : **essence** (règles de la niche du neuf) / **transfert** (règles des autres).
- Strates : **vu / non-vu** (contexte du probe déjà vu par le miel ?), méthode identique Phase 1 : octets de `vec(src)` f32 dans l'union des clés — **upper bound** (histogramme), note écrite.
- Glossaire + headline 2 étages : **mêmes phrases que Phase 1**, avec le recadrage (iv) :
  1. Phase 1 = « le miel PORTE du signal » (neuf à la chance).
  2. Phase 2 = « le miel ajoute-t-il MARGINALEMENT sur un COMPÉTENT ».

---

## 6. Probe (cérémonie identique)

- **Nouveau probe :** générateur identique, **graine 20261005**, n = 2000 ; **sha256 publié AVANT tout run** par Claude (cérémonie : hash indépendant des deux côtés).
- L'ancien `probe_vie.npz` (sha `1c34d5…`) **reste en test de non-régression** : un re-run gelé doit rendre les chiffres de Phase 1 à l'octet près.
- Le probe ne sert **qu'à l'éval** ; `cible` lue uniquement par le harnais d'eval, jamais par l'entraînement.

---

## 7. Graines, pilot, budget

- **Pilot :** 1 niche × **3 graines** × 2 bras (T_nu, T_miel), budget 600 s (parité Phase 1) → calcul du **n_requis au pilote** (sigma observé, base compétente).
- **Plein :** 3 niches (rep · arith|miroir · rnd|saut) × 2 bras × **S graines**, **S = cible 20 si le budget tient, plancher 10**.
- **Déclaré d'entrée :** verdict **directionnel + largeur affichée par bloc** ; **δ = 0.02 NON promis** (leçon §5.e du rapport Phase 1).
- Graines déclarées : data_seed du neuf = **17/18/19** (≠ 7/8/9 du rucher, ≠ graine probe) ; init = **2017/2018/2019** ; eval seed du harnais = déclaré par Claude au scellement.
- Estimation de compute (ordre de grandeur, pour le vert de Mathieu) : pilot ~12 min (parallèle), plein ~1,5–3 h selon S et parallélisme.

### 7bis. PLEIN — GRAINES FIGÉES (contre-signé Claude, 04/10 ~05:30)

- **S = 10** (plancher §7) : le déclencheur step-matched rend le 2ᵉ lot obligatoire (gap ~6 % reproduit au pilote **ET** A-essence < 0) → 2 lots × S=20 ≈ 6,5 h > budget 3 h → plancher. Le pilote donne déjà `n_requis = 10` sur les blocs lus.
- **data_seed :** n0 = 17…26 · n1 = 27…36 · n2 = 37…46. **init :** n0 = 2017…2026 · n1 = 2027…2036 · n2 = 2037…2046. Appariement data↔init **par index**.
- **Unicité** par abeille (règle C4) ; ≠ 7/8/9 (rucher) ; ≠ 20261004 / 20261005 (probes).
- Les graines pilot **n0 17/18/19** (`p2_pilote` + `p2_step`, déjà poussées) sont **réutilisées** comme 3 premières graines de n0.
- **2 lots obligatoires** (compute-matched + step-matched), mêmes graines/bras/pools.
- **Condition de run à documenter :** lots lancés sur la même machine que les outils LYNX (charge résiduelle ~14 % au repos, aucune autre charge lourde pendant les vagues).

---

## 8. Métriques et IC

- Verdicts (A) et (B) : diff d'accuracy appariée par graine, **IC95 bootstrap 2000 rééchantillons, graine 5 fixe** (identique Phase 1).
- `n_requis` affiché **par bloc** ; drapeaux `ic_croise_zero` / `sigma_zero` / `n_requis_gt10` conservés.
- Stats sk + ov_prec + n_ov + taux_consult (jamais lu seul) — même schéma que Phase 1.
- **Engagement dans `rapport_reel.json` :** nouveau probe sha, blob nectar, commits git, code_sha du code modifié, les 4 h de lignes si un fold est refait, β, graines, chance 1/39, gel.

---

## 9. Risques ÉCRITS D'AVANCE (avant tout résultat)

1. **(Claude)** La précision du miel (.452 global / .879 confiant en **v1** — **v2** après erratum
   consult k=39→5 : DUR .706 / SOUPLE .517, rapport §4bis du 04/10 ~05:00) est **cuite dans les
   poids** de T_miel : un miel faux apprend des erreurs au neuf. C'est la question, pas un biais à
   corriger après coup.
2. **(LYNX — prior ajouté)** Sur ce pool **synthétique à labels propres**, la cible-miel (§3) **ne peut pas apporter d'information de label neuve** (maj ≠ y n'est utile que si y est bruité). Prior honnête : **(A) ≈ 0 ± petit** ; un positif = bénéfice d'optimisation/calibration ; un négatif = contamination par les erreurs du miel. Écrire ce prior dans le rapport QUEL QUE SOIT le signe — pas de surprise a posteriori.
3. **(Claude)** Chevauchement probe : même méthode, même note « upper bound histogramme », nouveau taux calculé et écrit.
4. **(LYNX)** Si le taux d'activation de la cible-miel est faible en entraînement, un nul en (A) est **mécanique** (le levier ne s'est pas déclenché) : la télémétrie §3 est donc obligatoire pour INTERPRÉTER (A).

---

## 10. Hors scope (écrit pour ne pas dériver)

Pas de sweep β · pas de changement d'archi · pas de nouvelles niches · pas de re-run de Phase 1 sauf non-régression · rien de tout ceci n'est lancé sans le **vert de Mathieu**.

---

## 11. Rôles et gates

1. LYNX rédige (ce document) → 2. Claude **counter-signe** (écarts listés en §12) → 3. Claude **scelle le nouveau probe** (sha publié) → 4. Implémentation cible-miel (LYNX, `entrainer_local` + `--miel`, code_sha capturé) + harnais 4 cellules (Claude) → 5. **VERT MATHIEU** → 6. pilot → 7. plein → 8. rapport (mêmes 8 sections, headline 2 étages).

---

## 12. Points posés par LYNX, à counter-signer explicitement par Claude

- **(P1)** (A) primaire = **E2 − E0** (éval SANS consult pour isoler les poids) — tu n'avais pas fixé l'état d'eval de (A) ; je l'isole.
- **(P2)** Consult (entraînement ET eval) = **miel fixe scellé t=0 seul**, jamais la mémoire propre en croissance (anti-auto-leak).
- **(P3)** data_seed néophyte **17/18/19**, init **2017-2019** (≠ rucher, ≠ probe) — ou ta contre-proposition si tu veux caler sur 7/8/9.
- **(P4)** Nouveau probe **graine 20261005**, n=2000.
- **(P5)** Prior (A)≈0 sur labels propres (risque §9.2) — à écrire dans le rapport quel que soit le signe.
- **(P6)** Télémétrie taux d'activation obligatoire (§3) pour interpréter un nul en (A).

---

## 13. COUNTER-SIGNATURE CLAUDE (2026-10-04)

**P1–P6 : CONTRE-SIGNÉS.** Notes :

- **P1 (A primaire = E2 − E0)** — signé. Seule isolation PROPRE de l'effet poids (éval SANS consult). `E3 − E1` reste secondaire (apport de l'entraînement quand on consulte déjà = confondu par le canal d'éval). ✓
- **P2** — signé. Anti-auto-leak : le neuf ne consulte jamais sa propre mémoire en croissance ; le miel = fold scellé Phase 1 (`cfebe88d…`), figé t=0. ✓
- **P3 (data_seed 17/18/19)** — signé, **PAS** de bascule sur 7/8/9. Raison : avec 7/8/9, le miel serait **redondant sur les items mêmes** que le neuf entraîne → le marginal s'écrase artificiellement à ~0 **et** la strate « vu » dégénère (~100 %). 17/18/19 = mêmes RÈGLES, items NEUFS → miel non-redondant. ✓
- **P4** — signé (graine 20261005, n=2000). ✓
- **P5 (prior (A) ≈ 0)** — signé, avec un canal précisé : le POSITIF plausible n'est **pas** de l'info de label (impossible sur labels propres) mais de la **RÉGULARISATION** — la cible `sk·onehot(maj)+(1−sk)·onehot(y)` est un label DOUX (≈ label smoothing + structure distributionnelle des voisins kNN). Positif = régularisation/calibration ; négatif = erreurs du miel cuites dans les poids. Écrit AVANT tirage, quel que soit le signe. ✓
- **P6** — signé (télémétrie d'activation obligatoire ; sinon un nul est non-interprétable). ✓

**Amendement §7 (mineur) :** le pilote fixe 3 graines (init 2017-19 / data 17-19). Le PLEIN (S = 10–20) exige une **liste complète** de graines init+data — à figer au scellement, AVANT le run. Proposition : data_seed = 17…17+S−1, init = 2017…2017+S−1.

### PROBE PHASE 2 — SCELLÉ (publié AVANT tout run)

| Élément | Valeur |
|---|---|
| Fichier | `probe_phase2.npz` (générateur identique) |
| Graine | **20261005** |
| n | 2000 |
| **sha256** | `29444f0e451bacb0a878252ebd5d9b90911ab0e0f5f02b2941dd1ad853b14c78` |
| **sha1** (double hash) | `03be8a183bcbfd25ad3af49a86dd87c1d6d09fc4` |
| Taille | 160 760 o |
| Déterminisme | vérifié (2 générations → même sha256) |
| Non-régression | `probe_vie.npz` (`1c34d5…`) conservé |

**Prochain gate : VERT MATHIEU. Rien ne tourne avant.**
