# PROTOCOLE — Banc de mesure : « le bébé apprend-il à dire je ne sais pas ? »

Écrit d'avance (Mathieu, 03/10). Toute limite ci-dessous est engageante :
on ne change pas le protocole après avoir vu la courbe.

## Question unique

Un modèle qui NAÎT VIDE (poids aléatoires, aucune phrase humaine
préalable) apprend-il, par interaction en ligne avec feedback brut,
à CALIBRER sa confiance — c'est-à-dire à savoir qu'il ne sait pas ?

Le critère n'est pas l'accuracy. C'est l'**ECE en fonction du nombre
d'interactions** : elle doit DESCENDRE sans supervision de confiance.

## Bras comparés (même archi, même suite d'items, même alphabet)

| Bras | Apprentissage | Confiance déclarée |
|------|---------------|--------------------|
| A — bébé | 1 step SGD par interaction, feedback 0/1 brut, mémoire kNN externe | P max du softmax BRUT (aucune tête supervisée) |
| B — supervisé | entraînement batch offline (mêmes items, labels), puis figé | temperature scaling appris sur split de calibration (vérité) |
| C — baseline | aucun | confiance fixe 0.5 |

Le message d'A vers B est le cœur du test : si la courbe A rattrape B,
la calibration émerge sans supervision. Sinon, on l'écrit noir sur blanc.

## Tâche (vérité calculée, zéro LLM, zéro cloud)

Complétion du caractère suivant sur des séquences générées par des
règles connues du générateur (répétition, arithmétique, miroir,
saut d'indice, alphabet partiel) + des séquences **aléatoires pures**
— ces dernières n'ont AUCUNE réponse : la confiance honnête y est basse.
Le « je ne sais pas » n'est pas une formule : c'est une confiance basse
sur exactement ces items, mesurée contre la vérité du générateur.

Tokenizer = **caractères** (aucune phrase humaine pré-importée ;
l'alphabet s'apprend par le bootstrap de la boucle, pas par un corpus).

## Métriques (instrument indépendant, aucun LLM dans la boucle)

1. **ECE** (10 bins) évaluée à intervalle régulier → courbe ECE vs interactions.
2. **Risk–coverage** : balayage du seuil τ sur confiance → risk(τ),
   coverage(τ), AURC.
3. **Accuracy** (plancher de comparaison — pas l'objectif).

## Limites écrites d'avance

- Items de contrôle (aléatoires) : confiance honnête attendue ≤ 0.55.
  Si le bras A affiche une confiance haute là-dessus à la fin, c'est un
  ÉCHEC, et on l'écrit.
- Une seule graine (1234) pour v1 : la courbe montrée est indicative,
  pas publiée. Publication = 5 graines, bande de variance.
- Aucune donnée hors de cette machine. Pas de cloud, pas d'appel réseau.

## Sorties attendues

- `sorties/courbe_ece.png` — LA courbe (ECE vs interactions, 3 bras).
- `sorties/courbe_risk_coverage.png`
- `sorties/resultats.md` — tableau final + verdict honnête.
