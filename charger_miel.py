# -*- coding: utf-8 -*-
"""charger_miel.py — L'AGREGATEUR (cote mesure). Fold de lignes de nectar -> MemoireConsolidee (LE MIEL).

Frontiere : ce module NE produit NI NE valide de ligne (ca, c'est le writer de LYNX,
bebe/nectar.py, vendore ici). Il CONSOMME des lignes et en fait UNE memoire.

Anti-empoisonnement (contract v0, arbitre mailbox 04/10) :
  (i)   attribution       : groupe par 'abeille'
  (ii)  poids PLAFONNE    : w_b = min(1, N_cap / sum_n_b), N_cap = 5 x median(sum n_b)
                            de la COHORTE, recalcule a chaque fold (scale-free)
  (iii) niche dupliquee   : alarme (verifiee, non fatale en v0)
  (iv)  genome gate       : {heldout_sha256, code_sha, arch} identiques AVANT tout

Usage :
  python charger_miel.py <nectar.jsonl>            # fold + rapport
"""
import argparse
import json
import statistics
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent / "bebe"))
import nectar  # noqa: E402  (writer vendore, byte-identique, sha 87349392...)

import banc       # noqa: E402
import etat       # noqa: E402
import fusion     # noqa: E402


def _genome_key(li):
    g = li.get("genome") or {}
    return (g.get("heldout_sha256"), g.get("code_sha"),
            json.dumps(g.get("arch"), sort_keys=True))


def _mem_de_tableaux(k, keys, yc, n, ok_num, ls):
    """Construit une MemoireConsolidee depuis les 5 tableaux du nectar (ok = ok_num/n)."""
    m = etat.MemoireConsolidee(k=int(k))
    m.keys = np.asarray(keys, np.float32)
    m.y_counts = np.asarray(yc, np.int32)
    m.n = np.asarray(n, np.int32)
    m.last_seen = np.asarray(ls, np.int64)
    m.ok = np.array([ok_num[i] / n[i] if n[i] else 0.0 for i in range(len(n))], np.float32)
    m._rebuild_index()
    return m


def _scaler(mem, w):
    """Applique le plafond par abeille : n et y_counts x w ; ok INVARIANT (ok=ok_num/n)."""
    if w >= 1.0:
        return
    mem.n = np.round(mem.n.astype(np.float64) * w).astype(np.int32)
    mem.y_counts = np.round(mem.y_counts.astype(np.float64) * w).astype(np.int32)
    # ok inchange : (ok_num*w)/(n*w) = ok_num/n  -> les ratios de votes et la fiabilite tiennent


def charger_miel(lignes, cap_rule=True, genome_ref=None):
    """lignes: list[dict] -> (MemoireConsolidee | None, rapport)."""
    rap = {"recues": len(lignes), "gardees": 0, "refusees": [], "niches": {},
           "abeilles": {}, "N_cap": None, "w_b": {}}

    # ---- (iv) validation + genome gate
    bonnes = []
    for i, li in enumerate(lignes):
        ok, raisons = nectar.valider(li)
        if not ok:
            rap["refusees"].append({"i": i, "raisons": raisons}); continue
        gk = _genome_key(li)
        if genome_ref is None:
            genome_ref = gk
        if gk != genome_ref:
            rap["refusees"].append({"i": i, "raisons": ["genome divergent du miel"]}); continue
        bonnes.append(li)
    rap["gardees"] = len(bonnes)
    if not bonnes:
        return None, rap

    # ---- (iii) niche dupliquee = alarme (une niche, une abeille)
    par_niche = {}
    for li in bonnes:
        par_niche.setdefault(li["niche"], set()).add(li["abeille"])
    for niche, abs_ in par_niche.items():
        if len(abs_) > 1:
            rap["niches"][niche] = {"alarme": "niche partagee par plusieurs abeilles",
                                    "abeilles": sorted(abs_)}

    # ---- fold INTRA-abeille (une abeille peut ecrire plusieurs lignes/cycles)
    par_abeille = {}
    for li in bonnes:
        par_abeille.setdefault(li["abeille"], []).append(li)

    bee_mems = {}
    for ab, lis in par_abeille.items():
        parts = []
        for li in lis:
            keys, yc, n, ok_num, ls = nectar.lire_nectar(li)
            if int(np.asarray(n).sum()) == 0:
                rap["refusees"].append({"abeille": ab, "raisons": ["Sigma n = 0"]}); continue
            k = int(li["nectar"]["k"])
            parts.append(_mem_de_tableaux(k, keys, yc, n, ok_num, ls))
        if parts:
            bee_mems[ab] = parts[0] if len(parts) == 1 else fusion.merge_memoires(parts)
    if not bee_mems:
        return None, rap

    # ---- (ii) plafond par abeille : N_cap scale-free de la COHORTE
    sommes = {ab: int(m.n.sum()) for ab, m in bee_mems.items()}
    if cap_rule and sommes:
        N_cap = 5 * statistics.median(sommes.values())
        rap["N_cap"] = N_cap
        for ab, m in bee_mems.items():
            s = sommes[ab]
            w = 1.0 if s <= N_cap or s == 0 else N_cap / s
            rap["w_b"][ab] = round(w, 4)
            _scaler(m, w)
    rap["abeilles"] = {ab: int(m.n.sum()) for ab, m in bee_mems.items()}

    # ---- fold GLOBAL (le miel)
    miel = fusion.merge_memoires(list(bee_mems.values()),
                                 cap=int(getattr(banc, "CAP_MEMOIRE", 50000)))
    return miel, rap


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jsonl")
    ap.add_argument("--no-cap", action="store_true")
    a = ap.parse_args()
    lignes = nectar.lire_jsonl(a.jsonl)
    miel, rap = charger_miel(lignes, cap_rule=not a.no_cap)
    print(json.dumps(rap, indent=2, ensure_ascii=False))
    if miel is not None:
        print(json.dumps({"miel": {"cles": len(miel.keys), "sum_n": int(miel.n.sum()),
                                   "k": miel.k}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
