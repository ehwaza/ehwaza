# -*- coding: utf-8 -*-
"""Test d'integration v1.1 : memoire consolidee + fusion + refus des doublons/code_sha."""
import random
from pathlib import Path

import torch

import banc
import etat
import fusion

ROOT = Path(__file__).resolve().parent / "sorties_test"
ROOT.mkdir(exist_ok=True)
HD = ROOT / "holdout.npz"


def train_fragment(name, seed_init, seed_data, code_sha="genome-A", n=500, pool_n=250):
    torch.manual_seed(seed_init)
    m = banc.Bebe()
    opt = torch.optim.SGD(m.parameters(), lr=3e-4)
    lossf = torch.nn.CrossEntropyLoss()
    rng = random.Random(seed_data)
    pool = [banc.gen_item(rng) for _ in range(pool_n)]
    items = [pool[i % pool_n] for i in range(n)]
    mem = etat.MemoireConsolidee(k=5)
    hist = {"conf": [], "ok": []}
    m.train()
    for i, (src, cible, _) in enumerate(items):
        ids = banc.to_ids(src).unsqueeze(0)
        logit = m(ids)
        p = torch.softmax(logit, 1)[0]
        conf, pred = float(p.max()), int(p.argmax())
        y = banc.VOCAB[cible]
        mem.add(src, pred, pred == y, step=i)
        hist["conf"].append(conf); hist["ok"].append(1.0 if pred == y else 0.0)
        opt.zero_grad(); lossf(logit, torch.tensor([y])).backward(); opt.step()
    meta = {"fragment": name, "parent": "root-test", "cycle": 0, "parent_n": 0,
            "seeds": {"init": seed_init, "data": seed_data, "eval": 999},
            "heldout_sha256": etat.sha256_file(HD), "code_sha": code_sha, "metrics": {}}
    d = ROOT / name
    etat.save_bundle(d, m, mem, hist, meta)
    return d


if __name__ == "__main__":
    etat.save_heldout(HD, seed_eval=999, n=400)

    d1 = train_fragment("frag1", seed_init=1234, seed_data=1001)
    d2 = train_fragment("frag2", seed_init=1234, seed_data=2002)
    b = etat.load_bundle(d1)
    print(f"memoire consolidee : {len(b['mem'].keys)} cles pour 500 interactions en ligne")

    print("\n--- FUSION (data differente) ---")
    r = fusion.fuse([d1, d2], HD)
    for k in ("raisons", "frag_ece", "best_frag_ece", "alpha_best", "fusion_poids_ece",
              "ensemble_ece (témoin)", "n_interactions", "gagnant", "ece_gagnant", "verdict"):
        print(f"  {k}: {r.get(k)}")

    print("\n--- REFUS 1 : MEME seed_data ---")
    d3 = train_fragment("frag3_dup", seed_init=1234, seed_data=1001)
    r3 = fusion.fuse([d1, d3], HD)
    print("  ok:", r3.get("ok"), "|", r3.get("raisons"))

    print("\n--- REFUS 2 : code_sha divergent ---")
    d4 = train_fragment("frag4_autre", seed_init=1234, seed_data=3003, code_sha="genome-B")
    r4 = fusion.fuse([d1, d4], HD)
    print("  ok:", r4.get("ok"), "|", r4.get("raisons"))
