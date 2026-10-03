# le bébé — banc de mesure : « apprend-il à dire je ne sais pas ? »

Un modèle qui **naît vide** (poids aléatoires, zéro pré-entraînement) apprend-il,
par interaction en ligne, à **calibrer sa confiance** — c'est-à-dire à savoir
qu'il ne sait pas ? Le critère n'est pas l'accuracy : c'est l'**ECE**.

Projet de recherche. Instrument indépendant (0 LLM, 0 cloud dans la boucle).

## Résultats (graine unique — indicatif, pas publiable)

| run | bras A (bébé) | bras B (supervisé) | bras C (contrôle) |
|---|---|---|---|
| 20k | ECE 0.038 · acc 0.511 | 0.014 · 0.978 | 0.474 · 0.026 |
| 50k | ECE 0.022 · acc 0.595 | 0.008 · 0.992 | 0.475 · 0.025 |

La calibration **émerge sans supervision** de confiance. Levier unique validé :
**« le monde revient »** (un pool fini d'items qui repasse).

## Fichiers

- `banc.py` — les 3 bras A/B/C, l'instrument de mesure (ECE, risk-coverage, accuracy).
- `client_reseau.py` — client Wikipedia (données du fragment réseau).
- `etat.py` — **format d'état** d'un fragment (`model.pt` + `memoire.npz` + `hist.npz` + `meta.json`).
- `fusion.py` — fusion de fragments (interpolation des poids + balayage α sur held-out) + **verdict mesuré**.
- `fragment.py` — **un fragment** : restore → entraîne en ligne → sauvegarde un paquet. C'est le code que la CI lance.
- `heldout.npz` — held-out **commun et figé** (5 000 items, graine `seed_eval`). Commité : toute fusion l'exige.
- `PROTOCOLE.md` — protocole du banc, **écrit d'avance** (on ne le change pas après avoir vu la courbe).
- `SPEC_ECHANGE.md` — contrat du format d'état et du critère de fusion (co-signé Claude + LYNX, validé Mathieu).

## Le bébé est DISTRIBUÉ

Deux instances du même **génome** (ce code), évoluant séparément :

- **fragment local** (`F:\becvide\`) — apprend en continu ;
- **fragment GitHub Actions** (`.github/workflows/fragment.yml`) — N runners en parallèle, sessions bornées ;
- échange par **paquets d'état** ; **fusion** par synthèse pondérée par la calibration (`fusion.py`).

Règle dure : les fragments partagent `seed_init` et le held-out, mais chaque
fragment a sa **propre `seed_data`** — sinon les fragments sont identiques et la
fusion est nulle.

## Usage local

```bash
python banc.py --interactions 20000          # le banc complet (3 bras)
python etat.py selftest                       # verifie le format d'etat
python fragment.py --fragment local --init-seed 1234 --data-seed 1001 \
    --n 5000 --out sorties_frag/local         # un fragment
python fusion.py sorties_frag/a sorties_frag/b --heldout heldout.npz --out sorties_frag/fusion
```

## Note d'usage (runners)

Les runners GitHub Actions de ce dépôt servent de **benchmarks du projet bébé** :
tout le calcul qui y tourne est l'entraînement et la mesure de **son propre
modèle**, dans le cadre de ce projet. Aucun usage de calcul hors projet.

---

*Direction : Mathieu. Conception et code : Claude + LYNX 555.*
