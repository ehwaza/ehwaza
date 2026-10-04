# -*- coding: utf-8 -*-
"""Check croisé : le miel exporté (miel_phase1.npz), chargé par un loader IDENTIQUE à
celui de LYNX (entrainer_local._charger_miel), doit rendre les MEMES sk que mon fold
en mémoire -> aucun decalage train/eval."""
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent / "bebe"))
import banc                      # noqa: E402
import nectar                    # noqa: E402
import charger_miel as cm        # noqa: E402
import test_de_vie as tv         # noqa: E402

# mon fold en memoire
miel, _ = cm.charger_miel(nectar.lire_jsonl("nectar_reel.jsonl"))

# loader IDENTIQUE a entrainer_local._charger_miel (LYNX, commit 1c2a832)
z = np.load("miel_phase1.npz")
m2 = banc.MemoireConsolidee(k=5, cap=None)
m2.keys = np.asarray(z["keys"], np.float32)
m2.y_counts = np.asarray(z["y_counts"], np.int32)
m2.n = np.asarray(z["n"], np.int32)
m2.ok = np.asarray(z["ok"], np.float32)

assert np.array_equal(miel.keys, m2.keys), "keys divergent"
assert np.array_equal(miel.y_counts, m2.y_counts), "y_counts divergent"
assert np.array_equal(miel.n, m2.n), "n divergent"
assert np.array_equal(miel.ok, m2.ok), "ok divergent"
print("tableaux identiques : keys %s %s, y_counts %s, n %s, ok %s"
      % (miel.keys.shape, miel.keys.dtype, miel.y_counts.shape, miel.n.shape, miel.ok.shape))

items = tv.probe_items()
mx, ncons = 0.0, 0
for src, _, _ in items:
    maj1, sk1 = miel.consult(src)
    maj2, sk2 = m2.consult(src)
    if maj1 is not None:
        ncons += 1
    mx = max(mx, abs(sk1 - sk2))
    assert maj1 == maj2, "maj divergent"
print("consult sur %d items probe : max |dsk| = %.2e  (consultees %d)" % (len(items), mx, ncons))
print("VERDICT :", "IDENTIQUE (aucun decalage train/eval)" if mx == 0.0 else "ECART -> A CORRIGER")
