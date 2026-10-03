# -*- coding: utf-8 -*-
"""fusion.py — FUSION DE FRAGMENTS du bebe, VERDICT MESURE. (v1.1)

Integre le retour de LYNX (23:30) :
  - memoire : fusion = CONSOLIDATION (meme voie que l'insertion), pas un dedup ad hoc
  - N>1 : SWEEPS PAR PAIRES ITERES (pas de grille exponentielle)
  - ENSEMBLE : temoin obligatoire, LIVRABLE INTERDIT (coute N forwards/interaction)
  - hist : convient le LOCAL seulement ; n_interactions = parent_n + somme

Usage : python fusion.py <frag1> <frag2> [...] --heldout heldout.npz [--out dossier]
"""
import argparse
import json
from pathlib import Path

import numpy as np
import torch

import banc
import etat


# ----------------------------------------------------------------- eval
def _probs(model, src, device="cpu"):
    ids = banc.to_ids(src).unsqueeze(0).to(device)
    with torch.no_grad():
        return torch.softmax(model(ids), 1)[0]


def evaluate(model, mem, items, device="cpu"):
    """Fidele au bras A de banc : conf = Pmax, boost kNN si score > 0.5."""
    model.eval()
    confs, oks = [], []
    for src, cible in items:
        p = _probs(model, src, device)
        conf, pred = float(p.max()), int(p.argmax())
        if mem is not None:
            maj, sk = mem.consult(src)
            if maj is not None and sk > 0.5:
                conf = min(0.99, max(conf, sk))
        confs.append(conf)
        oks.append(1.0 if pred == banc.VOCAB.get(cible, -1) else 0.0)
    confs, oks = np.array(confs), np.array(oks)
    return {"ece": banc.ece_score(confs, oks), "acc": float(oks.mean()),
            "conf": float(confs.mean()), "n": len(oks)}


def evaluate_ensemble(models, items, device="cpu"):
    """TEMOIN (plafond superieur). Jamais le livrable."""
    for m in models:
        m.eval()
    confs, oks = [], []
    for src, cible in items:
        p = torch.stack([_probs(m, src, device) for m in models]).mean(0)
        confs.append(float(p.max()))
        oks.append(1.0 if int(p.argmax()) == banc.VOCAB.get(cible, -1) else 0.0)
    confs, oks = np.array(confs), np.array(oks)
    return {"ece": banc.ece_score(confs, oks), "acc": float(oks.mean()), "n": len(oks)}


# ----------------------------------------------------------------- poids
def interpolate(sd_a, sd_b, alpha):
    return {k: (1.0 - alpha) * sd_a[k].float() + alpha * sd_b[k].float() for k in sd_a}


def sweep_alpha(sd_a, sd_b, arch, items, n=21, device="cpu"):
    curve = []
    for alpha in np.linspace(0.0, 1.0, n):
        m = etat.build_model(arch, device=device)
        m.load_state_dict(interpolate(sd_a, sd_b, float(alpha)))
        curve.append((float(alpha), evaluate(m, None, items, device)["ece"]))
    best_a, best_e = min(curve, key=lambda t: t[1])
    return curve, best_a, best_e


def fuse_multi(models, items, n_iter=3, device="cpu"):
    """Sweeps PAR PAIRES iteres jusqu'a convergence (LYNX). Retourne (sd, ece, trace)."""
    arch = etat.arch_of(models[0])
    fused = {k: v.clone() for k, v in models[0].state_dict().items()}
    m = etat.build_model(arch, device=device); m.load_state_dict(fused)
    e_cur = evaluate(m, None, items, device)["ece"]
    trace = [e_cur]
    for _ in range(n_iter):
        bouge = False
        for j in range(1, len(models)):
            _, a, e = sweep_alpha(fused, models[j].state_dict(), arch, items, n=11, device=device)
            if e < e_cur - 1e-6:
                fused = interpolate(fused, models[j].state_dict(), a)
                e_cur, bouge = e, True
        trace.append(e_cur)
        if not bouge:
            break
    return fused, e_cur, trace


# ----------------------------------------------------------------- memoire : consolidation
def merge_memoires(mems, cap=50000):
    """Union par cle + SOMME des compteurs (meme voie que add())."""
    keys, yc, ok_num, n, ls, ix = [], [], [], [], [], {}
    for mem in mems:
        for r in range(len(mem.keys)):
            kb = mem.keys[r].tobytes()
            j = ix.get(kb)
            if j is None:
                ix[kb] = len(keys)
                keys.append(mem.keys[r]); yc.append(mem.y_counts[r].astype(np.int32).copy())
                ok_num.append(float(mem.ok[r]) * int(mem.n[r])); n.append(int(mem.n[r]))
                ls.append(int(mem.last_seen[r]))
            else:
                yc[j] = yc[j] + mem.y_counts[r]
                ok_num[j] += float(mem.ok[r]) * int(mem.n[r]); n[j] += int(mem.n[r])
                ls[j] = max(ls[j], int(mem.last_seen[r]))
    out = etat.MemoireConsolidee(k=mems[0].k, cap=cap)
    out.keys = np.array(keys, np.float32); out.y_counts = np.array(yc, np.int32)
    out.n = np.array(n, np.int32)
    out.ok = np.array([ok_num[i] / n[i] if n[i] else 0.0 for i in range(len(n))], np.float32)
    out.last_seen = np.array(ls, np.int64)
    out._rebuild_index()
    return out


def concat_hist(hists):
    out = {}
    for k in set().union(*[h.keys() for h in hists]):
        parts = [np.asarray(h[k], np.float32) for h in hists if k in h]
        out[k] = np.concatenate(parts) if parts else np.zeros(0, np.float32)
    return out


# ----------------------------------------------------------------- orchestration
def fuse(paths, heldout_path, device="cpu"):
    heldout = etat.load_heldout(heldout_path)
    bundles = [etat.load_bundle(p, device) for p in paths]
    ok_inv, raisons = etat.check_invariants(bundles)
    if not ok_inv:
        return {"ok": False, "raisons": raisons}

    frag_ece = [evaluate(b["model"], None, heldout, device)["ece"] for b in bundles]
    best_frag, best_frag_ece = int(np.argmin(frag_ece)), float(np.min(frag_ece))
    parent_n = int(bundles[0]["meta"].get("parent_n", 0))   # partage : compte UNE fois
    n_inter = parent_n + sum(int(b["meta"].get("n_new", 0)) for b in bundles)

    res = {"ok": True, "raisons": raisons, "frag_ece": frag_ece,
           "best_frag_ece": best_frag_ece, "n_interactions": int(n_inter)}

    ens = evaluate_ensemble([b["model"] for b in bundles], heldout, device)
    res["ensemble_ece (témoin)"] = ens["ece"]

    if len(bundles) == 2:
        curve, a_best, e_best = sweep_alpha(bundles[0]["model"].state_dict(),
                                            bundles[1]["model"].state_dict(),
                                            etat.arch_of(bundles[0]["model"]),
                                            heldout, n=21, device=device)
        # raffinement +/-0.02 pas 0.005 (LYNX)
        for a2 in np.arange(max(0, a_best - 0.02), min(1, a_best + 0.02) + 1e-9, 0.005):
            m = etat.build_model(etat.arch_of(bundles[0]["model"]), device=device)
            m.load_state_dict(interpolate(bundles[0]["model"].state_dict(),
                                          bundles[1]["model"].state_dict(), float(a2)))
            e2 = evaluate(m, None, heldout, device)["ece"]
            if e2 < e_best:
                a_best, e_best = float(a2), e2
        res.update({"alpha_best": a_best, "fusion_poids_ece": e_best})
        e_gagnant = e_best
    else:
        sd, e_gagnant, trace = fuse_multi([b["model"] for b in bundles], heldout, device=device)
        res.update({"fusion_multi_ece": e_gagnant, "trace": trace})

    res.update({"gagnant": "fusion-poids", "ece_gagnant": e_gagnant,
                "verdict": "OK" if e_gagnant < best_frag_ece else "ECHEC"})

    if res["verdict"] == "OK":
        arch = etat.arch_of(bundles[0]["model"])
        m = etat.build_model(arch, device=device)
        if len(bundles) == 2:
            m.load_state_dict(interpolate(bundles[0]["model"].state_dict(),
                                          bundles[1]["model"].state_dict(), res["alpha_best"]))
        else:
            m.load_state_dict(res.pop("fused_state"))
        res["fused_model"] = m
        res["fused_mem"] = merge_memoires([b["mem"] for b in bundles])
        res["fused_hist"] = concat_hist([b["hist"] for b in bundles])
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("frags", nargs="+")
    ap.add_argument("--heldout", required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    r = fuse(a.frags, a.heldout)
    print(json.dumps({k: v for k, v in r.items()
                      if k not in ("fused_model", "fused_mem", "fused_hist", "alpha_curve")},
                     indent=2, ensure_ascii=False, default=str))
    if r.get("ok") and r.get("verdict") == "OK" and a.out:
        meta = {"fragment": "fusion", "parent": "|".join(a.frags), "cycle": -1,
                "parent_n": r["n_interactions"],
                "seeds": {"init": None, "data": -1, "eval": None},
                "heldout_sha256": etat.sha256_file(a.heldout), "code_sha": "n/a",
                "metrics": {"ece": r["ece_gagnant"]}}
        etat.save_bundle(a.out, r["fused_model"], r["fused_mem"], r["fused_hist"], meta)
        print("paquet fusionne ->", a.out)


if __name__ == "__main__":
    main()
