# -*- coding: utf-8 -*-
"""_test_charger_miel.py — roundtrip : 3 abeilles (niches disjointes) -> nectar -> fold -> miel."""
import random
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent / "bebe"))
import banc
import nectar
import charger_miel as cm

ARCH = {"d": 128, "nl": 2, "heads": 4, "nv": banc.NV}
# genome REEL (LYNX, 04/10) : les cles restent synthetiques jusqu'aux vraies abeilles
GENOME = {"heldout_sha256": "03ff6fbc03286bc15ff615d46d8ad3b878686e75070af3b52d53e9f345bc1abb",
          "code_sha": "1ac15d6fc88c", "arch": ARCH}


def _abeille(niche, seed, n_items):
    rng = random.Random(seed)
    mem = banc.MemoireConsolidee(k=5, cap=banc.CAP_MEMOIRE)
    for i in range(n_items):
        src, cible, _ = banc.gen_item(rng)
        mem.add(src, banc.VOCAB.get(cible, 0), correct=(rng.random() < 0.7), step=i)
    return mem


def _ligne(ab, niche, seed, mem):
    return nectar.ligne_nectar(abeille=ab, niche=f"regles={niche}; data_seed={seed}",
                               meta=GENOME, seen={"n_items": int(mem.n.sum()), "cycles": 1},
                               mem=mem, m_total=len(mem.keys))


def main():
    abeilles = [
        ("a" * 16, "rep", 7, _abeille("rep", 7, 60)),
        ("b" * 16, "arith|miroir", 8, _abeille("arith|miroir", 8, 60)),
        ("c" * 16, "saut|rnd", 9, _abeille("saut|rnd", 9, 60)),
    ]
    lignes = [_ligne(ab, ni, sd, m) for ab, ni, sd, m in abeilles]

    # roundtrip d'une ligne : valider + decoder
    ok, raisons = nectar.valider(lignes[0])
    k0, yc0, n0, okn0, ls0 = nectar.lire_nectar(lignes[0])
    m0 = abeilles[0][3]
    assert ok, raisons
    assert k0.shape == m0.keys.shape, (k0.shape, m0.keys.shape)
    assert np.allclose(k0, m0.keys) and np.array_equal(n0, m0.n), "roundtrip tableaux KO"
    assert np.allclose(okn0, m0.ok.astype(np.float64) * m0.n), "ok_num != ok*n"
    print("[1] roundtrip ligne OK : m=%d k=%d sum_n=%d" % (len(k0), k0.shape[1], int(n0.sum())))

    # fold
    miel, rap = cm.charger_miel(lignes)
    assert miel is not None, rap
    sum_attendu = sum(int(mm.n.sum()) for _, _, _, mm in abeilles)
    cles_union = len(set().union(*[set(mm.keys.tobytes() for mm in [m]) for _, _, _, m in abeilles]))
    print("[2] fold OK : cles=%d sum_n=%d (attendu %d) N_cap=%s"
          % (len(miel.keys), int(miel.n.sum()), sum_attendu, rap["N_cap"]))
    assert int(miel.n.sum()) == sum_attendu, "somme des compteurs != somme des abeilles (sans cap)"
    assert rap["gardees"] == 3 and not rap["refusees"]
    print("[3] attribution/niches OK : gardees=%d, niches=%s" % (rap["gardees"], rap["w_b"] or "(pas de cap)"))

    # cap : une abeille GONFLEE ne doit plus avaler le miel
    gros = _abeille("rep", 7, 60)
    gros.n = (gros.n * 100).astype(np.int32)          # byzantin en volume (n x100)
    lignes2 = [_ligne("a" * 16, "rep", 7, gros)] + lignes[1:]
    miel2, rap2 = cm.charger_miel(lignes2)
    na, nb, nc = (int(m.n.sum()) for _, _, _, m in abeilles)
    print("[4] cap : N_cap=%s w_b=%s | sum_n miel=%d (sans cap aurait ete %d)"
          % (rap2["N_cap"], rap2["w_b"], int(miel2.n.sum()), na * 100 + nb + nc))
    assert rap2["w_b"]["a" * 16] < 1.0, "l'abeille gonflee devrait etre plafonnee"

    # genome divergent -> ligne refusee
    bad = dict(lignes[1]); bad["genome"] = dict(bad["genome"], code_sha="AUTRE")
    bad["h"] = nectar._h(bad)
    _, rap3 = cm.charger_miel([lignes[0], bad, lignes[2]])
    print("[5] genome gate : refusees=%s" % [r.get("raisons") for r in rap3["refusees"]])
    assert rap3["gardees"] == 2 and rap3["refusees"], "une ligne au genome divergent doit etre refusee"

    print("\nTOUS VERTS")


if __name__ == "__main__":
    main()
