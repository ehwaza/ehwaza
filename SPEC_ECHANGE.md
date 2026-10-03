# SPEC_ECHANGE — Format d'échange des fragments « le bébé » (v1.2)

> DRAFT de travail. Auteurs : Claude (v1) + LYNX (v1.1, 7 points) + revue
> code de Claude (v1.2, clauses C1-C5 — écarts spec/code, le code fait foi).
> **Statut : EN ATTENTE DE CONTRESIGNATURE (Claude) + VALIDATION (Mathieu).**
> Tant que ce contrat n'est pas signé, aucun code permanent ne s'y aligne.
> Protocole engage d'AVANCE : on ne le change pas après avoir vu les courbes.
>
> **Journal des révisions**
> - v1.2 (03/10, Claude) : C1 arch réel du module (d/nl/heads/nv) · C2 meta +
>   cycle/parent_n/n_new · C3 y_counts **int32** (int16 déborde : une clé du
>   pool de 1200 passe 32767+ sur plusieurs cycles) · C4 `parent` = identité
>   NON AMBIGUE `<fragment>@<code_sha>#<cycle>` · C5 noms de champs npz FIGÉS
>   en anglais (`keys`, pas `cles` — les noms SONT le contrat).

---

## 1. Le paquet d'état (ce qu'un fragment sauvegarde / restaure)

| Fichier       | Contenu                                                            | Taille estimée |
|---------------|--------------------------------------------------------------------|----------------|
| `model.pt`    | `torch.save(state_dict)`                                           | ~1.7 Mo        |
| `memoire.npz` | kNN externe, **consolidé par clé** (voir §1.1)                     | ~10-15 Mo      |
| `hist.npz`    | courbes `ece[] acc[] conf[] loss[] n[]` — vectorisé, préalloué     | <1 Mo          |
| `meta.json`   | voir §2                                                            | ~2 Ko          |

Total estimé ~25 Mo/fragment — très en dessous des 2 Go de release.

### 1.1 memoire.npz — format FIGÉ v1 (point LYNX, ancré dans le code)

**Fait de code (banc.py:139)** : `MemoireKNN` est append-only SANS cap, et `run_bras`
utilise un POOL FINI de 1200 items qui repasse en boucle (banc.py:178-180).
À 50k interactions, ~48.8k entrées sur 50k sont des DOUBLONS de contextes déjà vus.
Le O(n²) de débit vient de la duplication, pas du choix d'un cap.

**Règle** : une clé = un contexte. Chaque `add()` MET À JOUR l'entrée existante
(consolidation), il n'en crée pas une nouvelle.

```
keys      [M, NV]      float32   vecteurs de comptage normalisés   (C5)
y_counts  [M, |VOCAB|] int32     votes par label                   (C3)
ok        [M]          float32   sommes de succès
n         [M]          int32     nombre d'occurrences
last_seen [M]          int64     horodatage logique (pour LRU)
k         scalaire     int       paramètre kNN (consult en dépend)  (C5)
```

**C5 — noms de champs FIGÉS** : `keys, y_counts, ok, n, last_seen, k`.
Les noms de champs npz SONT le contrat : un seul nom, celui du code
(`etat.save_bundle` écrit `keys=`...). Toute divergence = paquet non conforme.
**C3 — y_counts en int32** : une clé consolidée du pool de 1200 peut être
vue des dizaines de milliers de fois sur plusieurs cycles → int16 (32767)
déborde. Le code utilise int32 partout, la spec s'aligne.

- Cap : **50k entrées POST-consolidation**, éviction **LRU** (`last_seen`).
  Localement M converge vers ~1200 (pool fini) ; le cap ne sert qu'au
  fragment réseau (Wikipedia, contextes divers).
- Conséquence débit : `consult()` devient O(distinct) ≈ O(1200) — le O(n²)
  meurt structurellement, pas par plafond arbitraire.
- Conséquence fusion : la règle « dedup par (clé,label) » devient LE MÊME
  code que l'insertion — une seule voie, pas deux.
- Toute extension du format = `bebe-etat/2`, jamais un champ caché en v1.

---

## 2. meta.json (schéma)

```json
{
  "format": "bebe-etat/1",
  "fragment": "local" | "gh-<run_id>-<shard>",
  "parent": "<fragment>@<code_sha>#<cycle>",
  "created_utc": "...",
  "n_interactions": 12345,
  "arch": {"d": 128, "nl": 2, "heads": 4, "nv": 39},
  "seeds": {"init": 1234, "data": 5678, "eval": 999},
  "cycle": 3,
  "parent_n": 400000,
  "n_new": 40000,
  "heldout_sha256": "<sha256 de heldout.npz>",
  "code_sha": "<git commit du genome>",
  "metrics": {"ece": 0.022, "acc": 0.595, "conf": 0.593, "aurc": 0.183}
}
```

**C1 — arch = valeurs LUES DU MODULE, jamais en dur.** Le modèle réel est
`Bebe(d=128, nl=2, heads=4, nv=39)` (banc.py:84). Les champs sont
`d / nl / heads / nv`, tels que `etat.arch_of()` les écrit — un fragment
doit pouvoir se RECONSTRUIRE à partir de ce seul objet.
**C2 — 3 champs exigés par §3/§6** : `cycle` (règle de doublon),
`parent_n` (pas de double compte), `n_new` (interactions locales du cycle,
et `n_interactions = parent_n + n_new`).

**Règle dure** : les seeds sont lues des valeurs EFFECTIVES du run
(banc.py a `SEED = 1234` en dur + `manual_seed(SEED+1)`) — jamais une
constante dupliquée dans ce document.

---

## 3. Discipline de seeds (contrainte dure)

- `seed_init` : **PARTAGÉE** — identique dans tous les fragments issus du même parent.
- `seed_data` : **PAR (FRAGMENT, CYCLE)** — DOIT différer. Sinon fragments
  identiques → fusion nulle. Le fragment local traverse plusieurs cycles ;
  la graine change à chaque cycle.
- `seed_eval` : **PARTAGÉE** — held-out fixe, 5000 items, `heldout.npz`
  COMMITÉ, sha dans meta.
- **Doublon** : même parent + même (fragment, cycle, seed_data) → refus à la
  fusion (on log, on ne fusionne pas de l'identique).

---

## 4. Identité du held-out

`heldout.npz` généré UNE fois, commité (petit). Toute fusion l'exige :
`heldout_sha256` divergent entre deux paquets → **fusion REFUSÉE**
(on ne compare pas sur des évals différents). C'est ce qui rend
l'alpha-sweep valide.

---

## 5. Invariants DURS de fusion (v1.1, complétés v1.2)

| Condition                                            | Décision            |
|------------------------------------------------------|---------------------|
| `heldout_sha256` différent                           | REFUS               |
| `arch` différent                                     | REFUS               |
| **`code_sha` différent** (ajout LYNX)                | **REFUS** — même init ne suffit pas si le genome a bougé : le bassin de perte n'est plus le même |
| même parent + même (fragment, cycle, seed_data)      | REFUS (doublon)     |
| `parent` différent                                   | REFUS (pas la même famille) |

**C4 — `parent` doit porter une identité NON AMBIGUE** : `<fragment>@<code_sha>#<cycle>`
(ou sha256 de son meta.json). Le nom du fragment seul ("local", "root") est
trop faible : la clause « parent différent → REFUS » serait inopérante.
`etat.check_invariants` vérifie l'égalité de `parent` — le format d'identité
est celui ci-dessus.

---

## 6. Critère de fusion

Entrée : N paquets partageant le MÊME parent + le même `heldout_sha`.

- **Fusion poids** : θ(α) = Σ wᵢ θᵢ.
  - N=2 : balayage 1-D de α (grille 0.05, puis raffinement ±0.02 par pas 0.005).
  - N>1 : **sweeps pairwise itérés** jusqu'à convergence — chaque sweep =
    N(N-1)/2 balayages 1-D sur le simplex, on boucle tant que l'ECE bouge.
    Coût réel : une eval = 5000 forwards (~secondes). Pour le balayage
    grossier, subsampler le held-out puis valider sur les 5000 complets.
    La grille G^(N-1) est exponentielle : jetée.
- **Fusion mémoire** : union consolidée (mêmes clés que l'insertion),
  y_counts SOMMÉS, ok SOMMÉ, n SOMMÉ, cap partagé 50k, LRU.
- **Fusion hist** : CONCAT des hist LOCAUX uniquement + `n_interactions` =
  `parent_n + SOMME des nouvelles par fragment` (pas de double compte :
  chaque fragment ne stocke QUE les points après le parent).
- **VERDICT MESURÉ** : si ECE(θ_fused) > min_i ECE(θ_i) → **ÉCHEC**, écrit
  noir sur blanc. Fallback = meilleur fragment. L'ENSEMBLE (moyenne des
  predictions) est testé comme TÉMOIN (voir §8).

---

## 7. Échange

Release tag `etat-courant` = paquet partagé + `heldout.npz` (**release,
JAMAIS en commit** — sinon le dépôt gonfle et meurt ; runners éphémères →
restore/train/upload à chaque job).
Chaque fragment : download → entraîne → upload son paquet.

---

## 8. Ensemble : TÉMOIN obligatoire, livrable interdit par défaut

- Coût : N forwards par interaction en ligne → divise le débit par N.
  Il tue exactement le point « débit » du chantier.
- Conceptuel : le sujet est la calibration qui ÉMERGE chez UN apprenant,
  pas la moyenne de N. L'ensemble est le plafond supérieur mesuré :
  - si le fused rattrape l'ensemble → la fusion est bonne ;
  - si l'ensemble dépasse nettement → **arbitrage de Mathieu**
    (performance vs pureté du sujet).

---

## 9. Qui fait quoi

| Outil       | Propriétaire | Rôle                                                        |
|-------------|--------------|-------------------------------------------------------------|
| `etat.py`   | Claude       | save/load conforme §1-2 + vérification des invariants §3-5  |
| `fusion.py` | Claude       | §6, avec VERDICT mesuré                                      |
| `banc.py`   | LYNX         | ÉMETTEUR — produit les paquets conformes (format figé §1.1) |
| `workflow`  | Claude       | §7 (.github/workflows)                                       |
| débit       | LYNX         | optimisation de la boucle (profil 5k en main)                |
| Spéc       | ENSEMBLE     | ce document, cosigné + Mathieu                               |

ToS : les runners servent de benchmarks pour ce projet — le README du dépôt
le dit explicitement. Aucun calcul hors projet.

---

## 10. Questions tranchées (v1.1, revue v1.2)

- (a) cap mémoire : **50k POST-consolidation, LRU** (§1.1).
- (b) N>1 : **sweeps pairwise itérés**, ni grille complète ni greedy pur (§6).
- (c) ensemble : **témoin obligatoire, livrable interdit par défaut** (§8).

---

*Signatures : Claude ______ / LYNX ______ / Mathieu ______ (date : ____)*
