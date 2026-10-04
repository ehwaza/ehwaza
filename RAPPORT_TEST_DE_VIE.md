# RAPPORT — TEST DE VIE DE LA RUCHE (premier verdict sur données réelles)

**Date :** 2026-10-04 · **Auteurs :** Claude (agrégateur + harnais) × LYNX (writer + abeilles) ·
**Statut :** verdict primaire rendu, décomposition pré-enregistrée appliquée.

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
| Bootstrap | 2000 rééchantillons, graine 5 (reproductible) |
| β | **0.5, figé AVANT tout résultat réel** — pas de sweep (un degré de liberté en moins) |
| Graines | 10 (abaissées ; voir §5.e) |
| Chance (base) | 1/39 = 0.026 |
| Gel | poids init graine `s`, **aucun entraînement**, miel au `consult` seulement ; les deux bras d'une paire partagent les poids |

---

## 2. HEADLINE

1. **Un miel de ruche A CORRIGÉ une abeille neuve GELÉE (chance → .3–.4) sur sa niche ET sur les autres.**
2. **Mais la décomposition montre que le transfert est dominé par les contextes VUS ; la généralisation au neuf est faible.**

---

## 3. MÉTHODE

Miel = fold du nectar des 3 abeilles (`charger_miel`, union des clés + somme des compteurs, plafond
par abeille — ici inactif, aucune abeille ne domine en volume). Abeille neuve = poids **gelés**
(graine `s`, jamais entraînés) + mémoire **vide** vs **miel**. Deux bras appariés, mêmes poids.
Deux modes d'usage du miel :

- **SOUPLE (verdict primaire)** : `p = (1−β)·p_modele + β·p_knn`, `p_knn = one-hot(maj)·sk`.
- **DUR (témoin)** : si `sk>0.5` → `pred=maj`, `conf=sk`.

Probe scellé → 2 blocs **essence** (règles de SA niche) / **transfert** (règles des autres), croisés
avec **vu / non-vu** (le contexte du probe a-t-il déjà été vu par les abeilles ? 59.1 % oui).

---

## 4. RÉSULTATS

### 4.1 Verdict primaire — MIEL UTILE sur les 3 niches, les 2 modes

| niche | mode | essence (vide→miel) | transfert (vide→miel) |
|---|---|---|---|
| n0 (rep) | souple | **+0.304** (.0235→.3271) | **+0.369** (.0340→.4034) |
| n1 (arith\|miroir) | souple | **+0.434** (.0313→.4653) | **+0.305** (.0324→.3369) |
| n2 (saut\|rnd) | souple | **+0.305** (.0367→.3416) | **+0.392** (.0288→.4205) |
| n0 | dur | +0.000 (.0235→.0235) | +0.065 (.0340→.0993) |
| n1 | dur | +0.013 (.0313→.0447) | +0.079 (.0324→.1116) |
| n2 | dur | +0.117 (.0367→.1538) | +0.009 (.0288→.0378) |

Les deux bras sont un modèle **à la chance** (.024–.045). Donc « MIEL UTILE » se lit ici comme
« **le miel bat un neuf au hasard** » (conséquence de l'accord *gel*) — PAS « un neuf compétent ».

### 4.2 Décomposition vu / non-vu (SOUPLE) — le cœur du résultat

| niche | strate | vide→miel | diff |
|---|---|---|---|
| n0 | essence **vu** | .0234→.4269 | **+0.404** |
| n0 | essence non-vu | .0237→.2194 | +0.196 |
| n0 | transfert **vu** | .0376→.5424 | **+0.505** |
| n0 | transfert non-vu | .0283→.1877 | +0.159 |
| n1 | essence **vu** | .0324→.4638 | **+0.431** |
| n1 | essence non-vu | .0283→.4690 | +0.441 |
| n1 | transfert **vu** | .0379→.5796 | **+0.542** |
| n1 | transfert non-vu | .0269→.0902 | +0.063 |
| n2 | essence **vu** | .0451→.6561 | **+0.611** |
| n2 | essence non-vu | .0283→.0310 | **+0.003** |
| n2 | transfert **vu** | .0301→.4543 | +0.424 |
| n2 | transfert non-vu | .0262→.3563 | +0.330 |

**Lecture :** sur le **vu**, le miel atteint .42–.66 ; sur le **non-vu**, il tombe à .03–.36.
Le « transfert d'essence » est donc **surtout de la récupération** de contextes déjà vus ; la
**généralisation au contexte réellement neuf est faible** (cf. §5.b).

---

## 5. AJOUTS EXIGÉS (conditions d'accord LYNX — pris tels quels)

**a) Engagement** → §1 (bloc dédié dans `rapport_reel.json`).

**b) Seule cellule où l'IC croise zéro = pas d'effet détectable.** `souple / n2 / essence_nonvu` :
diff **+0.003**, IC95 **[−0.0007, +0.0062]** → **traverse zéro**. C'est la cellule la plus forte du
niveau 2 (le miel n'aide pas sur la niche `saut|rnd` pour un contexte neuf), pas une anecdote.

**c) IC dégénérés σ=0 = résultats identiques entre graines, IC non informative.** Blocs concernés :
`dur / n0 / essence`, `dur / n0 / essence_vu`, `dur / n0 / essence_nonvu`, `dur / n1 / essence_vu`,
`dur / n2 / transfert_vu`. Ne pas y lire une précision inexistante.

**d) DUR vs SOUPLE — couverture contre précision, même verdict.** Sommet de vérification dur :
n_ov = **132/2000** overrides, précision **.879**. Souple : n_ov = **1692/2000**, précision **.452**.
Le verdict seul (« MIEL UTILE » partout) lirait une fausse **équivalence d'amplitude** : le dur donne
+0.000/+0.013 là où le souple donne +0.30/+0.43. Même direction, **amplitude très différente**.

**e) n_requis par bloc.** `n_requis > 10` sur **13 blocs**, maximum **145** (`souple / n2 / essence_vu`).
→ **10 graines n'atteignent PAS la cible de largeur** sur ces blocs : le verdict reste **directionnel** ;
la précision de l'IC y est en dessous de δ = 0.02.

`sk` (distribution, identique aux 2 modes — même consultation) : moy **.275**, p50 .283, p90 .454,
p99 .585, max **.705**. La masse est **sous 0.5** : le dur ne mord qu'à la queue (132), mais juste
quand il mord (précision .88).

---

## 6. GLOSSAIRE

- **Gel** — l'abeille neuve n'est pas entraînée : ses poids restent à l'init. On mesure donc le
  miel **seul**, pas un apprentissage.
- **Récupération vs généralisation** — le miel restitue d'abord ce que les abeilles ont **vu**
  (récupération) ; il généralise faiblement à des contextes **neufs**.

---

## 7. LIMITES

- Base à la **chance** (gel) : « MIEL UTILE » = bat un neuf au hasard, pas un neuf compétent.
- Probe à **graine distincte** (pas disjoint en contexte : 59.1 % vu).
- **10 graines** : suffisant pour la direction, insuffisant pour la largeur sur 13 blocs (§5.e).
- Chevauchement = upper bound (histogramme de caractères).

---

## 8. OUVERTURE (NON TESTÉE ICI)

Le **warm-start d'un neuf compétent** (apprendre *avec* le miel, au sens des poids) est la **Phase 2** :
même protocole, mais un neuf entraîné. **Non testé dans ce rapport.**

---

*Fichiers : `F:\becvide\test_de_vie.py` (harnais), `charger_miel.py` (agrégateur), `bebe/nectar.py`
(writer vendorfé), `rapport_reel.json` (données brutes + engagement + drapeaux).*
