# RAPPORT — TEST DE VIE DE LA RUCHE (premier verdict sur données réelles)

**Date :** 2026-10-04 · **Auteurs :** Claude (agrégateur + harnais) × LYNX (writer + abeilles) ·
**Version :** **v2 — chiffres corrigés** (voir §4bis ERRATUM) · **Statut :** verdict primaire rendu, décomposition pré-enregistrée appliquée.

---

## 0. Pourquoi ce test existe

Le held-out classique est **contaminé** (au-delà de ~300k interactions, il ne mesure plus la
calibration mais la mémorisation). On l'a jeté. Le nouveau verdict de la ruche est **le test de vie** :
*une abeille neuve apprend-elle mieux AVEC le miel (la mémoire collective) qu'SANS ?*

---

## 1. ENGAGEMENT / GÉNÉALOGIE (scellé avant tout tirage)

| Élément | Valeur |
|---|---|
| Probe (scellé) | `probe_vie.npz` — sha256 `1c34d5efa67638bef639a72204bf6033cb4863dbe36fef2512854616a9af228b` |
| Graine probe | `20261004` (⊥ des niches `data_seed` 7/8/9) — n = 2000 items |
| Déterminisme probe | vérifié : 2 générations → même sha |
| Nectar | `ehwaza/bebe-ia`, commit `b871661`, `resultats/nectar_lignes.jsonl` |
| Nectar — blob git (LF) | sha256 `cfebe88d112820d2ccefc1cf2705bd69bcce4be9ab79e57c121beabc4b80e0a4` (844 164 o) |
| Nectar — fichier local (CRLF) | sha256 `293e7734d1875b94e0ab21b4097c30ed60c4460382529f168ed730df2edf4615` (844 167 o) |
| Écart blobs | 3 octets = 3 fins de ligne (`core.autocrlf`) |
| Lignes `h[:16]` | `caf9ea4280a3fa73` · `ed28088771caafad` · `dcbc2b08701b687e` |
| Chevauchement contexte | **0.591** — calculé par LYNX ET recalculé par Claude (convergents) |
| Chevauchement — note | **UPPER BOUND** : `vec` = histogramme de caractères ; 2 `src` distincts peuvent partager le même octet |
| Miel (fold → npz) | `miel_phase1.npz` — sha256 `619105c33f5aed5e60b2c156a94b24bf815c405ea7a0e6eb20081a1fb70997af` (1925 clés, Σn = 260 392) |
| Consult (k voisins) | **k = 5** (banc/harnais/loader LYNX) — voir §4bis |
| Bootstrap | 2000 rééchantillons, graine 5 (reproductible) |
| β | **0.5, figé AVANT tout résultat réel** — pas de sweep |
| Graines | 10 |
| Chance (base) | 1/39 = 0.026 |
| Gel | poids init graine `s`, **aucun entraînement**, miel au `consult` seulement |

---

## 2. HEADLINE

1. **Un miel de ruche A CORRIGÉ une abeille neuve GELÉE (chance → .4–.5) sur sa niche ET sur les autres.**
2. **Mais la décomposition montre que le transfert est dominé par les contextes VUS ; la généralisation au neuf est faible.**

---

## 3. MÉTHODE

Miel = fold du nectar des 3 abeilles (`charger_miel`, union des clés + somme des compteurs, plafond
par abeille — ici inactif). Abeille neuve = poids **gelés** (graine `s`, jamais entraînés) + mémoire
**vide** vs **miel**. Deux bras appariés, mêmes poids. Deux modes d'usage du miel :

- **SOUPLE (verdict primaire)** : `p = (1−β)·p_modele + β·p_knn`, `p_knn = one-hot(maj)·sk`.
- **DUR (témoin)** : si `sk>0.5` → `pred=maj`, `conf=sk`.

Probe scellé → 2 blocs **essence** (règles de SA niche) / **transfert** (règles des autres), croisés
avec **vu / non-vu** (le contexte du probe a-t-il déjà été vu par les abeilles ? 59.1 % oui).

---

## 4. RÉSULTATS (v2)

### 4.1 Verdict primaire — MIEL UTILE sur les 3 niches, les 2 modes

| niche | mode | essence (vide→miel) | transfert (vide→miel) |
|---|---|---|---|
| n0 (rep) | souple | **+0.373** (.0235→.3966) | **+0.434** (.0340→.4676) |
| n1 (arith\|miroir) | souple | **+0.480** (.0313→.5110) | **+0.383** (.0324→.4153) |
| n2 (saut\|rnd) | souple | **+0.388** (.0367→.4243) | **+0.445** (.0288→.4739) |
| n0 | dur | +0.228 (.0235→.2512) | +0.212 (.0340→.2458) |
| n1 | dur | +0.170 (.0313→.2016) | +0.245 (.0324→.2774) |
| n2 | dur | +0.253 (.0367→.2900) | +0.189 (.0288→.2177) |

Les deux bras sont un modèle **à la chance** (.024–.045). Donc « MIEL UTILE » se lit ici comme
« **le miel bat un neuf au hasard** » (conséquence de l'accord *gel*) — PAS « un neuf compétent ».

### 4.2 Décomposition vu / non-vu (SOUPLE) — le cœur du résultat

| niche | strate | vide→miel | diff |
|---|---|---|---|
| n0 | essence **vu** | .0234→.5025 | **+0.479** |
| n0 | essence non-vu | .0237→.2823 | +0.259 |
| n0 | transfert **vu** | .0376→.6299 | **+0.592** |
| n0 | transfert non-vu | .0283→.2158 | +0.188 |
| n1 | essence **vu** | .0324→.5050 | **+0.473** |
| n1 | essence non-vu | .0283→.5265 | +0.498 |
| n1 | transfert **vu** | .0379→.7076 | **+0.670** |
| n1 | transfert non-vu | .0269→.1181 | +0.091 |
| n2 | essence **vu** | .0451→.8105 | **+0.765** |
| n2 | essence non-vu | .0283→.0429 | **+0.015** |
| n2 | transfert **vu** | .0301→.5044 | +0.474 |
| n2 | transfert non-vu | .0262→.4163 | +0.390 |

**Lecture :** sur le **vu**, le miel atteint .50–.81 ; sur le **non-vu**, il tombe à .03–.53, et
s'effondre par endroits (`n2 essence non-vu` +0.015 ; `n1 transfert non-vu` +0.091). Le « transfert
d'essence » est donc **surtout de la récupération** de contextes déjà vus ; la **généralisation au
contexte réellement neuf est faible**.

`sk` : moy **.397**, p50 .413, p90 .735, p99 .866, max **.996**.

---

## 4bis. ERRATUM — correction du `consult` (v1 → v2)

**Défaut trouvé (04/10, ~05:00).** L'agrégateur réglait le `k` du `consult` sur la **dimension des
clés** (`k` = 39 = NV) au lieu du **nombre de voisins** (`k` = **5**, la valeur de `banc.MemoireConsolidee`).
Conséquence : les chiffres de la **v1** (rapport publié et audité) étaient calculés avec **39 voisins**.

**Fix.** `charger_miel` force `k = 5` ; l'export `miel_phase1.npz` est **inchangé** (il ne contient que
les tableaux, pas `k`). **Croisement prouvé** : le miel chargé par le **loader de LYNX**
(`entrainer_local._charger_miel`, `banc.MemoireConsolidee(k=5)`) rend des `sk` **identiques** à mon
fold — `max |Δsk| = 0.00` sur 2000 items. Aucun décalage train/éval ne subsiste.

**Ce qui change :** les chiffres (acc, `sk`, `ov_prec`) montent (avec k=5 la masse `sk>0.5` est bien
plus fournie). **Ce qui ne change pas : la conclusion** — MIEL UTILE partout, transfert dominé par le vu.

**Effet sur les addenda v1 :**
- L'addendum **(b)** (« seule cellule où l'IC croise 0 » = `n2 essence non-vu`) **ne s'applique plus** :
  avec k=5, **aucune** cellule ne croise 0 ; `n2 essence non-vu` = **+0.0145**, IC [+0.0101, +0.0185]
  (petit mais positif). Le défaut k=39 créait un artefact de cellule croisant 0.
- L'addendum **(c)** (σ=0) **ne s'applique plus** : plus aucun bloc dégénéré.

---

## 5. AJOUTS (conditions d'accord LYNX — appliqués au format v2)

**a) Engagement** → §1 (+ bloc dans `rapport_reel.json`).

**b)** cf. §4bis : la cellule qui croisait 0 était un artefact de k=39. En **v2**, la cellule la plus
faible est `souple / n2 / essence_non-vu` = **+0.0145** IC [+0.0101, +0.0185] → **positive** (exclut 0),
mais d'amplitude ~30× plus petite que le vu.

**c)** None retiré. Blocs σ=0 : **aucun** en v2.

**d) DUR vs SOUPLE — couverture contre précision, même verdict.** DUR : n_ov = **637/2000**, précision
**.706**. SOUPLE : n_ov = **1722/2000**, précision **.517**. En v2, le DUR **se déclenche fortement**
(sk monte à .996), donc les deux modes ne divergent plus d'amplitude (+0.23/+0.17/+0.25 vs
+0.37/+0.48/+0.39) — mais restent **distincts** (le souple voit plus, le dur est plus précis).

**e) n_requis par bloc.** `n_requis > 10` sur **13 blocs**, maximum **147**.
→ **10 graines n'atteignent PAS la cible de largeur** sur ces blocs : le verdict reste **directionnel**.

---

## 6. GLOSSAIRE

- **Gel** — l'abeille neuve n'est pas entraînée : ses poids restent à l'init. On mesure le miel **seul**.
- **Récupération vs généralisation** — le miel restitue d'abord ce que les abeilles ont **vu** ; il
  généralise faiblement à des contextes **neufs**.

---

## 7. LIMITES

- Base à la **chance** (gel) : « MIEL UTILE » = bat un neuf au hasard, pas un neuf compétent.
- Probe à **graine distincte** (pas disjoint en contexte : 59.1 % vu).
- **10 graines** : direction OK, largeur insuffisante sur 13 blocs (§5.e).
- Chevauchement = upper bound (histogramme de caractères).
- **v1 corrigée en v2** (§4bis) : le `consult` utilise k=5.

---

## 8. OUVERTURE (NON TESTÉE ICI)

Le **warm-start d'un neuf compétent** (apprendre *avec* le miel, au sens des poids) est la **Phase 2** :
protocole pré-enregistré, nouveau probe scellé (`probe_phase2.npz`, graine 20261005). **Non testé ici.**

---

*Fichiers : `F:\becvide\test_de_vie.py` (harnais), `charger_miel.py` (agrégateur, k=5), `bebe/nectar.py`
(writer vendorfé), `miel_phase1.npz`, `rapport_reel.json`, `_check_croise_miel.py` (preuve Δsk=0).*
