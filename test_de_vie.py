# -*- coding: utf-8 -*-
"""test_de_vie.py — LE TEST DE VIE (remplace le heldout comme verdict).

Question falsifiable : une ABEILLE NEUVE (poids GELES, graine s) apprend-elle MIEUX
avec le miel que sans ?  2 bras APPARIES, identiques SAUF la memoire.

Deux modes d'usage du miel (le dur est un temoin ; le souple est le verdict primaire) :
  DUR    : si sk>0.5 -> pred=maj, conf=sk (l'override d'origine).
  SOUPLE : p = (1-beta)*p_modele + beta*p_knn, p_knn=one-hot(maj)*sk (beta=0.5 FIGE d'avance).

Passe PAR ITEM (une eval par (graine, bras) sur tout le probe) -> on agrege ensuite par
n'importe quelle strate. Strates : essence/transfert (niche du neuf) x vu/non-vu
(le contexte du probe a-t-il ete vu par les abeilles ?).

Probe scelle : probe_vie.npz, graine 20261004, sha 1c34d5ef... (verifie a chaque run).

Usage : python test_de_vie.py [--nectar nectar.jsonl] [--seeds 10] [--mode both] [--beta 0.5]
"""
import argparse
import json
import math
import random
import sys
from pathlib import Path

import numpy as np

_RACINE = Path(__file__).resolve().parent
sys.path.insert(0, str(_RACINE / "bebe"))
import nectar  # noqa: E402   (writer vendore, pin 6f645488)

import banc          # noqa: E402
import etat          # noqa: E402
import fusion        # noqa: E402
import charger_miel as cm  # noqa: E402

PROBE = _RACINE / "probe_vie.npz"
PROBE_SEED, PROBE_N = 20261004, 2000
PROBE_SHA = "1c34d5efa67638bef639a72204bf6033cb4863dbe36fef2512854616a9af228b"
ARCH = {"d": 128, "nl": 2, "heads": 4, "nv": banc.NV}
NICHES = {"n0": {"rep"}, "n1": {"arith", "miroir"}, "n2": {"saut", "rnd"}}
DELTA = 0.02
BETA_FIGE = 0.5


# ------------------------------------------------------------------ probe
def probe_items():
    """Rejoue la graine -> items + regles ; verifie l'egalite contre le probe SCELLE."""
    if etat.sha256_file(PROBE) != PROBE_SHA:
        raise SystemExit("PROBE modifie : le sha ne colle plus a l'engagement")
    rng = random.Random(PROBE_SEED)
    rejoue = [banc.gen_item(rng) for _ in range(PROBE_N)]
    scelle = etat.load_heldout(PROBE)
    assert len(rejoue) == len(scelle), "taille probe"
    for (s, c, _), (s2, c2) in zip(rejoue, scelle):
        assert s == s2 and c == c2, "replay != probe scelle (banc.py a bouge ?)"
    return rejoue


# ------------------------------------------------------------------ eval (par item)
def eval_rows(model, mem, items, mode="souple", beta=BETA_FIGE, device="cpu"):
    """Retourne (oks[np.bool_|float], stats). oks[i] = reponse juste sur items[i]."""
    model.eval()
    oks = np.zeros(len(items), np.float32)
    confs = np.zeros(len(items), np.float32)
    n_consult = n_chg = n_chg_ok = 0
    sks = []
    for i, (src, cible, *_) in enumerate(items):
        p = fusion._probs(model, src, device).detach().cpu().numpy().astype(np.float64)
        y = banc.VOCAB.get(cible, -1)
        pred, conf = int(np.argmax(p)), float(p.max())
        if mem is not None:
            maj, sk = mem.consult(src)
            if maj is not None and sk > 0.0:
                n_consult += 1; sks.append(sk)
                if mode == "dur":
                    if sk > 0.5:
                        if maj != pred:
                            n_chg += 1; n_chg_ok += (maj == y)
                        pred, conf = maj, sk
                else:
                    p2 = (1.0 - beta) * p
                    p2[maj] += beta * sk
                    pred2 = int(np.argmax(p2))
                    if pred2 != pred:
                        n_chg += 1; n_chg_ok += (pred2 == y)
                    pred, conf = pred2, float(p2.max())
        oks[i] = 1.0 if pred == y else 0.0
        confs[i] = conf
    stats = {"ece": banc.ece_score(confs, oks), "n": len(items),
             "taux_consult": n_consult / max(len(items), 1),
             "override_precision": (n_chg_ok / n_chg) if n_chg else float("nan"),
             "n_override": n_chg}
    if sks:
        a = np.array(sks)
        stats.update({"sk_moy": float(a.mean()), "sk_p50": float(np.percentile(a, 50)),
                      "sk_p90": float(np.percentile(a, 90)), "sk_p99": float(np.percentile(a, 99)),
                      "sk_max": float(a.max())})
    return oks, stats


# ------------------------------------------------------------------ stats
def ic95_bootstrap(diffs, n_boot=2000, seed=5):
    a = np.array(diffs, float)
    if len(a) < 2:
        m = float(a.mean()) if len(a) else 0.0
        return m, 0.0, (m, m)
    rng = np.random.default_rng(seed)
    means = a[rng.integers(0, len(a), size=(n_boot, len(a)))].mean(axis=1)
    return float(a.mean()), float(a.std(ddof=1)), \
        (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))


def n_requis(sigma_d, delta=DELTA):
    return 10 if sigma_d <= 0 else max(10, math.ceil(((1.96 + 0.84) * sigma_d / delta) ** 2))


# ------------------------------------------------------------------ coeur
def test_de_vie(honey, items, seeds, mode="souple", beta=BETA_FIGE):
    hkeys = {honey.keys[i].tobytes() for i in range(len(honey.keys))}
    # NB : les cles du miel sont float32 -> caster vec() en f32 avant tobytes, sinon 0% d'intersection
    vu = np.array([banc.MemoireKNN.vec(it[0]).astype(np.float32).tobytes() in hkeys for it in items])
    reg = np.array([it[2] for it in items])

    per_niche = {}
    for k, rv in NICHES.items():
        ess = np.array([r in rv for r in reg])
        masks = {"essence": ess, "transfert": ~ess,
                 "essence_vu": ess & vu, "essence_nonvu": ess & ~vu,
                 "transfert_vu": (~ess) & vu, "transfert_nonvu": (~ess) & ~vu}
        per_niche[k] = {"masks": masks, "size": {b: int(m.sum()) for b, m in masks.items()},
                        "acc_v": {b: [] for b in masks}, "acc_h": {b: [] for b in masks},
                        "stats": None}

    for s in seeds:
        m = etat.build_model(ARCH, seed_init=s)                 # poids GELES
        oe, _ = eval_rows(m, None, items, mode, beta)
        oh, sh = eval_rows(m, honey, items, mode, beta)
        for k in per_niche:
            d = per_niche[k]
            for b, mask in d["masks"].items():
                if mask.sum() == 0:
                    continue
                d["acc_v"][b].append(float(oe[mask].mean()))
                d["acc_h"][b].append(float(oh[mask].mean()))
            d["stats"] = sh
    return per_niche, {"vu_pct": float(vu.mean())}


def verdict(per_niche, meta, delta=DELTA):
    out = {}
    for k, d in per_niche.items():
        blocks = {}
        for b in d["masks"]:
            av, ah = d["acc_v"][b], d["acc_h"][b]
            if not av:
                continue
            diffs = [h - v for h, v in zip(ah, av)]
            m_, sd, (lo, hi) = ic95_bootstrap(diffs)
            blocks[b] = {"n": d["size"][b], "acc_vide": round(float(np.mean(av)), 4),
                         "acc_miel": round(float(np.mean(ah)), 4),
                         "diff": round(m_, 4), "sigma_d": round(sd, 4),
                         "ic95": [round(lo, 4), round(hi, 4)], "n_requis": n_requis(sd, delta)}
        prim = ((blocks["essence"]["ic95"][0] > 0) or (blocks["transfert"]["ic95"][0] > 0)) and \
               (min(blocks["essence"]["diff"], blocks["transfert"]["diff"]) > -delta)
        out[k] = {"primaire": "MIEL UTILE" if prim else "DECORATION", "blocs": blocks,
                  "stats": d["stats"]}
    out["_vu_pct"] = meta["vu_pct"]
    return out


# ------------------------------------------------------------------ fallback
def _lignes_synthetiques():
    def abeille(rules, seed, n):
        rng = random.Random(seed)
        mem = banc.MemoireConsolidee(k=5, cap=banc.CAP_MEMOIRE)
        for i in range(n):
            src, cible, reg = banc.gen_item(rng)
            while reg not in rules:
                src, cible, reg = banc.gen_item(rng)
            mem.add(src, banc.VOCAB.get(cible, 0), correct=(rng.random() < 0.7), step=i)
        return mem
    GEN = {"heldout_sha256": "03ff6fbc03286bc15ff615d46d8ad3b878686e75070af3b52d53e9f345bc1abb",
           "code_sha": "1ac15d6fc88c", "arch": ARCH}
    out = []
    for j, (rules, seed) in enumerate([({"rep"}, 7), ({"arith", "miroir"}, 8), ({"saut", "rnd"}, 9)]):
        mem = abeille(rules, seed, 400)
        out.append(nectar.ligne_nectar(abeille=f"{j:016x}", niche=f"regles={','.join(sorted(rules))}; data_seed={seed}",
                                       meta=GEN, seen={"n_items": int(mem.n.sum()), "cycles": 1},
                                       mem=mem, m_total=len(mem.keys)))
    return out


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nectar", default=None)
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--mode", default="both", choices=["dur", "souple", "both"])
    ap.add_argument("--beta", type=float, default=BETA_FIGE)
    ap.add_argument("--json", default=None, help="ecrit le rapport complet")
    a = ap.parse_args()

    items = probe_items()
    lignes = nectar.lire_jsonl(a.nectar) if a.nectar else _lignes_synthetiques()
    honey, rap = cm.charger_miel(lignes)
    print("miel : cles=%d sum_n=%d | gardees=%d refusees=%d | N_cap=%s"
          % (len(honey.keys), int(honey.n.sum()), rap["gardees"], len(rap["refusees"]), rap["N_cap"]))
    print("probe : %s (%d items) | sha OK | graine %d" % (PROBE.name, len(items), PROBE_SEED))

    seeds = list(range(1, a.seeds + 1))
    modes = ["souple", "dur"] if a.mode == "both" else [a.mode]
    rapport = {}
    for mode in modes:
        per_niche, meta = test_de_vie(honey, items, seeds, mode=mode, beta=a.beta)
        v = verdict(per_niche, meta)
        rapport[mode] = v
        print("\n=== MODE %s (beta=%.2f) | %d graines | chevauchement contexte %.3f ==="
              % (mode.upper(), a.beta, len(seeds), meta["vu_pct"]))
        print("  verdicts : %s" % json.dumps({k: v[k]["primaire"] for k in NICHES}, ensure_ascii=False))
        for k in NICHES:
            st = v[k]["stats"]
            print("  %s : %s" % (k, v[k]["primaire"]))
            for b, bl in v[k]["blocs"].items():
                print("     %-14s n=%-4d vide=%.3f miel=%.3f diff=%+.4f IC[%+.4f,%+.4f]"
                      % (b, bl["n"], bl["acc_vide"], bl["acc_miel"], bl["diff"],
                         bl["ic95"][0], bl["ic95"][1]))
            print("     ov_prec=%s n_ov=%d | sk moy=%.3f p50=%.3f p90=%.3f p99=%.3f max=%.3f"
                  % (st.get("override_precision"), st.get("n_override", 0), st.get("sk_moy") or 0,
                     st.get("sk_p50") or 0, st.get("sk_p90") or 0, st.get("sk_p99") or 0, st.get("sk_max") or 0))
    if a.json:
        Path(a.json).write_text(json.dumps(rapport, indent=2, ensure_ascii=False), encoding="utf-8")
        print("\nrapport ->", a.json)


if __name__ == "__main__":
    main()
