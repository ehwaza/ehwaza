# _smoke_memoire.py — fumigation du port MemoireConsolidee -> banc.py (LYNX, 03/10)
# 1) imports (banc + client_reseau)  2) consolidation  3) parite d'interface
# 4) run_bras(300) bout-en-bout (n'ecrit aucun fichier : seul main() ecrit)
import sys, time
sys.path.insert(0, r"F:\becvide")

import banc
from banc import MemoireKNN, MemoireConsolidee, CAP_MEMOIRE, run_bras

# --- 1) imports
import client_reseau
assert client_reseau.MemoireConsolidee is MemoireConsolidee, "import client_reseau casse"
print("1. imports OK (banc + client_reseau, MemoireConsolidee partage)")

# --- 2) consolidation : 500 adds sur 250 contextes distincts
import random
rng = random.Random(7)
AL = banc.ALPHABET
ctx = ["".join(rng.choice(AL[:26]) for _ in range(8)) for _ in range(250)]
mem = MemoireConsolidee(k=5, cap=CAP_MEMOIRE)
t0 = time.time()
for i in range(500):
    s = ctx[i % 250]
    mem.add(s, rng.randrange(banc.NV), rng.random() < 0.6, step=i)
M = len(mem.keys)
assert M <= 255, f"consolidation casse : {M} cles pour 500 adds / 250 contextes"
assert int(mem.n.sum()) == 500, f"compteur perdu : n.sum={int(mem.n.sum())}"
print(f"2. consolidation OK : {M} cles pour 500 adds (250 contextes), "
      f"n.sum=500, {time.time()-t0:.2f}s")

# --- 3) parite d'interface avec MemoireKNN
maj, sc = mem.consult(ctx[0])
assert maj is None or 0 <= maj < banc.NV
assert 0.0 <= sc <= 1.0
m2 = MemoireKNN(k=5)
m2.add("abc", 1, True)
assert MemoireKNN.vec("abc").shape == MemoireConsolidee.vec("abc").shape
print(f"3. interface OK : consult -> (lab={maj}, score={sc:.3f}), vec commune")

# --- 4) run_bras(300) bout-en-bout
t0 = time.time()
hist = run_bras(300, log_every=100)
assert "A" in hist and len(hist["A"]["ece"]) >= 3
print(f"4. run_bras(300) OK en {time.time()-t0:.1f}s — "
      f"ECE A final = {hist['A']['ece'][-1]:.3f}")
print("SMOKE MEMOIRE : TOUT VERT")
