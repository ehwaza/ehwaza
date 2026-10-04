# -*- coding: utf-8 -*-
"""test_de_vie_phase2.py — Harnais des 4 CELLULES (Phase 2), code seulement.

Question : le miel ajoute-t-il un gain MARGINAL sur une abeille neuve COMPETENTE ?

4 cellules (appariement strict : meme graine, seul le miel-cible differe) :
                   eval SANS miel     eval AVEC miel (souple beta=0.5)
  T_nu  (cible nu)  E0 (reference)     E1
  T_miel(cible §3)  E2                E3
Contrasts : (B) primaire = E1-E0 ; (A) primaire = E2-E0 ; secondaires E3-E0, E3-E1.

Le harnais CONSOMME des paquets deja entraines (entrainer_local de LYNX) : par graine, deux
paquets T_nu et T_miel. Aucun entrainement ici. Le miel = miel_phase1.npz (fold Phase 1),
charge par un loader IDENTIQUE a entrainer_local._charger_miel (k=5).

Usage : python test_de_vie_phase2.py --runs runs.json
  runs.json = {"1": {"nu": "<dir>", "miel": "<dir>"}, "2": {...}}   (cles = graines)
  ou --selftest (paquets factices, verifie que le mobilier tourne).
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

_RACINE = Path(__file__).resolve().parent
sys.path.insert(0, str(_RACINE / "bebe"))
import banc          # noqa: E402
import etat          # noqa: E402
import test_de_vie as tv   # noqa: E402   (eval_rows, ic95_bootstrap, n_requis, NICHES, ARCH)

PROBE2 = _RACINE / "probe_phase2.npz"
PROBE2_SEED, PROBE2_N = 20261005, 2000
PROBE2_SHA = "29444f0e451bacb0a878252ebd5d9b90911ab0e0f5f02b2941dd1ad853b14c78"
MIEL_DEFAUT = _RACINE / "miel_phase1.npz"


# ------------------------------------------------------------------ probe 2
def probe_phase2_items():
    if etat.sha256_file(PROBE2) != PROBE2_SHA:
        raise SystemExit("probe_phase2 modifie : le sha ne colle plus a l'engagement")
    rng = __import__("random").Random(PROBE2_SEED)
    rejoue = [banc.gen_item(rng) for _ in range(PROBE2_N)]
    scelle = etat.load_heldout(PROBE2)
    for (s, c, _), (s2, c2) in zip(rejoue, scelle):
        assert s == s2 and c == c2, "replay != probe_phase2 scelle"
    return rejoue


# ------------------------------------------------------------------ loader miel (contrat LYNX)
def charger_miel_npz(path):
    z = np.load(path)
    m = banc.MemoireConsolidee(k=5, cap=None)
    m.keys = np.asarray(z["keys"], np.float32)
    m.y_counts = np.asarray(z["y_counts"], np.int32)
    m.n = np.asarray(z["n"], np.int32)
    m.ok = np.asarray(z["ok"], np.float32)
    return m


# ------------------------------------------------------------------ cellules
def cellules(nu_dir, miel_dir, honey, items, beta=0.5, device="cpu"):
    """Retourne les accs des 4 cellules + stats (sur le probe entier)."""
    b_nu = etat.load_bundle(nu_dir, device)
    b_miel = etat.load_bundle(miel_dir, device)
    out = {}
    for nom, b in (("E0", (b_nu, None)), ("E1", (b_nu, honey)),
                   ("E2", (b_miel, None)), ("E3", (b_miel, honey))):
        oks, st = tv.eval_rows(b[0]["model"], b[1], items, mode="souple", beta=beta, device=device)
        out[nom] = {"acc": float(oks.mean()), "stats": st, "oks": oks}
    return out


def _seats(items):
    reg = np.array([it[2] for it in items])
    return {k: np.array([r in v for r in reg]) for k, v in tv.NICHES.items()}


def comparer(runs, honey, items, beta=0.5):
    """runs = {graine: {'nu': dir, 'miel': dir}}. Contrasts apparies par graine."""
    seats = _seats(items)
    per_niche = {k: {} for k in tv.NICHES}
    for seed, dirs in runs.items():
        cells = cellules(dirs["nu"], dirs["miel"], honey, items, beta=beta)
        for k in tv.NICHES:
            m_ess = seats[k]
            for bloc, mask in (("essence", m_ess), ("transfert", ~m_ess)):
                accs = {n: float(cells[n]["oks"][mask].mean()) for n in ("E0", "E1", "E2", "E3")}
                d = per_niche[k].setdefault(bloc, {"B": [], "A": [], "S_E3E0": [], "S_E3E1": []})
                d["B"].append(accs["E1"] - accs["E0"])
                d["A"].append(accs["E2"] - accs["E0"])
                d["S_E3E0"].append(accs["E3"] - accs["E0"])
                d["S_E3E1"].append(accs["E3"] - accs["E1"])
    return per_niche


def comparer_plein(runs_niche, honey, items, beta=0.5):
    """runs_niche = {niche: {graine: {'nu':dir,'miel':dir}}}.
    Chaque abeille est lue sur SA niche : le split essence/transfert depend de la niche d'entrainement."""
    seats = _seats(items)
    per_niche = {}
    for k, runs in runs_niche.items():
        m_ess = seats[k]
        blocs = {"essence": {"B": [], "A": [], "S_E3E0": [], "S_E3E1": []},
                 "transfert": {"B": [], "A": [], "S_E3E0": [], "S_E3E1": []}}
        for seed, dirs in runs.items():
            cells = cellules(dirs["nu"], dirs["miel"], honey, items, beta=beta)
            for bloc, mask in (("essence", m_ess), ("transfert", ~m_ess)):
                accs = {n: float(cells[n]["oks"][mask].mean()) for n in ("E0", "E1", "E2", "E3")}
                d = blocs[bloc]
                d["B"].append(accs["E1"] - accs["E0"])
                d["A"].append(accs["E2"] - accs["E0"])
                d["S_E3E0"].append(accs["E3"] - accs["E0"])
                d["S_E3E1"].append(accs["E3"] - accs["E1"])
        per_niche[k] = blocs
    return per_niche


def _est_plein(runs):
    """True si le schema est niche -> graine -> {nu,miel} (3 niveaux),
    False si graine -> {nu,miel} (2 niveaux)."""
    first = next(iter(runs.values()))
    if not isinstance(first, dict):
        return False
    any_val = next(iter(first.values()))
    return isinstance(any_val, dict) and ("nu" in any_val or "miel" in any_val)


def verdict_phase2(per_niche):
    out = {}
    for k, blocs in per_niche.items():
        out[k] = {}
        for bloc, dd in blocs.items():
            row = {}
            for nom, key in (("B=E1-E0", "B"), ("A=E2-E0", "A"),
                             ("E3-E0", "S_E3E0"), ("E3-E1", "S_E3E1")):
                m_, sd, ic = tv.ic95_bootstrap(dd[key])
                row[nom] = {"diff": round(m_, 6), "sigma_d": round(sd, 6),
                            "ic95": [round(ic[0], 6), round(ic[1], 6)],
                            "n_requis": tv.n_requis(sd)}
            out[k][bloc] = row
    return out


# ------------------------------------------------------------------ selftest (paquets factices)
def _selftest():
    import torch
    d = _RACINE / "_p2_mock"
    import shutil; shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True, exist_ok=True)
    items = probe_phase2_items()[:300]
    miel = charger_miel_npz(MIEL_DEFAUT)
    runs = {}
    for seed in (1, 2):
        for tag, sd in (("nu", 100 + seed), ("miel", 200 + seed)):
            bdir = d / f"{tag}{seed}"
            torch.manual_seed(sd)
            model = banc.Bebe(d=128, nl=2, heads=4)
            mem = etat.MemoireConsolidee(k=5)
            etat.save_bundle(bdir, model, mem, {"conf": [0.5]}, {
                "fragment": tag, "parent": "root", "cycle": 0, "parent_n": 0,
                "seeds": {"init": sd, "data": seed, "eval": 0},
                "heldout_sha256": "X", "code_sha": "Y", "arch": tv.ARCH})
            runs.setdefault(str(seed), {})[tag] = str(bdir)
    res = comparer(runs, miel, items)
    v = verdict_phase2(res)
    print("SELFTEST 4 cellules OK :", json.dumps({k: list(v[k].keys()) for k in v}, ensure_ascii=False))
    print("  exemple n0/essence:", json.dumps(v["n0"]["essence"], ensure_ascii=False))
    shutil.rmtree(d, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default=None, help="json {graine:{nu,miel}}")
    ap.add_argument("--miel", default=str(MIEL_DEFAUT))
    ap.add_argument("--beta", type=float, default=0.5)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        _selftest(); return
    if not a.runs:
        print(__doc__); return
    runs = json.loads(Path(a.runs).read_text(encoding="utf-8"))
    honey = charger_miel_npz(a.miel)
    items = probe_phase2_items()
    if _est_plein(runs):
        res = comparer_plein(runs, honey, items, beta=a.beta)
    else:
        res = comparer(runs, honey, items, beta=a.beta)
    print(json.dumps(verdict_phase2(res), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
