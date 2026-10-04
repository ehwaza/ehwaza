# -*- coding: utf-8 -*-
"""fragment.py — UN FRAGMENT du bebe, executable localement OU sur un runner GitHub.

Chaine : restaure un parent (ou nait d'une seed_init) -> apprend en ligne (bras A)
-> sauvegarde un paquet d'etat conforme a etat.py. C'est le code que la CI lance.

Contraintes respectees :
  - budget de temps (--budget-seconds) : la session GitHub est plafonnee a 6h,
    on coupe AVANT et on sauvegarde un paquet propre.
  - seed_data PAR fragment (jamais partagee) ; seed_init = celle du parent.
  - memoire consolidee (etat.MemoireConsolidee) -> debit qui ne s'effondre pas.

Usage :
  python fragment.py --fragment local --init-seed 1234 --data-seed 1001 \
      --n 5000 --out sorties_frag/local [--parent <dossier_paquet>] [--budget-seconds 3600]
"""
import argparse
import json
import random
import time
from pathlib import Path

import numpy as np
import torch

import banc
import etat


def _gen_filtre(rng, regles):
    """Item de banc.gen_item RESTREINT a un sous-ensemble de regles (distribution)."""
    if not regles:
        return banc.gen_item(rng)
    while True:
        it = banc.gen_item(rng)
        if it[2] in regles:
            return it


def run_fragment(name, init_seed, data_seed, n_inter, out_dir,
                 parent_dir=None, pool_n=1200, eval_every=100,
                 budget_seconds=None, code_sha="local", heldout_path=None,
                 regles=None, central_spec=None, device="cpu"):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    # code_sha = hash de CONTENU du genome (identique local / Colab / GitHub) -> fusion possible
    # (aligne sur entrainer_local.py ; un commit git differe d'un depot a l'autre)
    code_sha = etat.sha256_file(Path(banc.__file__))[:12]
    if isinstance(regles, str):
        regles = set(r.strip() for r in regles.split(",") if r.strip()) or None
    parent_n = 0
    parent_id = "root"

    if parent_dir:
        b = etat.load_bundle(parent_dir, device)
        model, mem = b["model"], b["mem"]
        parent_n = int(b["meta"].get("parent_n", 0)) + int(b["meta"].get("n_new", 0))
        pm = b["meta"]
        # C4 : identite NON ambigue. Un enfant de la RACINE s'appelle "root" (convention
        # entrainer_local) pour que le local/Colab/GitHub partagent le meme id de famille.
        parent_id = ("root" if pm.get("fragment") == "root"
                     else f'{pm.get("fragment")}@{pm.get("code_sha")}#{pm.get("cycle")}')
    else:
        torch.manual_seed(int(init_seed))
        model = banc.Bebe().to(device)
        mem = etat.MemoireConsolidee(k=5)
        parent_id = "root"                                # geniteur : le bebe nait

    opt = torch.optim.SGD(model.parameters(), lr=3e-4)
    lossf = torch.nn.CrossEntropyLoss()
    if central_spec:
        # CENTRAL : pool = CONCAT des pools des shards (MEME multiset qu'eux -> seul le topo change)
        spec = json.loads(central_spec)
        pool = []
        for s in spec:
            rr = random.Random(int(s["data_seed"]))
            rg = set(x.strip() for x in s.get("regles", "").split(",") if x.strip()) or None
            pool += [_gen_filtre(rr, rg) for _ in range(int(s.get("pool", 300)))]
        print(f"[{name}] CENTRAL : concat de {len(spec)} shards -> pool={len(pool)} items", flush=True)
    else:
        rng = random.Random(int(data_seed))
        pool = [_gen_filtre(rng, regles) for _ in range(int(pool_n))]
        if regles:
            print(f"[{name}] distribution restreinte aux regles : {sorted(regles)} | pool={pool_n}", flush=True)

    hist = {"conf": [], "ok": [], "ece": []}
    confs, oks = [], []
    t0 = time.time()
    i = 0
    for i in range(int(n_inter)):
        if budget_seconds and (time.time() - t0) > budget_seconds:
            print(f"[budget] coupe a {i} interactions ({budget_seconds}s)", flush=True)
            break
        src, cible, _ = pool[i % len(pool)]     # indexation paresseuse : O(1) memoire
        ids = banc.to_ids(src).unsqueeze(0).to(device)
        y = banc.VOCAB[cible]
        model.train()
        logit = model(ids)
        p = torch.softmax(logit, 1)[0]
        conf, pred = float(p.max()), int(p.argmax())
        maj, sk = mem.consult(src)
        if maj is not None and sk > 0.5:
            conf = min(0.99, max(conf, sk))
        ok = 1.0 if pred == y else 0.0
        mem.add(src, pred, pred == y, step=i)
        confs.append(conf); oks.append(ok)
        opt.zero_grad(); lossf(logit, torch.tensor([y], device=device)).backward(); opt.step()
        if (i + 1) % eval_every == 0:
            hist["conf"].append(float(np.mean(confs[-eval_every:])))
            hist["ok"].append(float(np.mean(oks[-eval_every:])))
            hist["ece"].append(float(banc.ece_score(confs, oks)))
            dt = time.time() - t0
            print(f"[{name}] {i+1:6d}  ece={hist['ece'][-1]:.3f}  "
                  f"acc={np.mean(oks):.3f}  {dt:.0f}s  {1000*dt/(i+1):.1f} ms/it", flush=True)

    dt = time.time() - t0
    meta = {"fragment": name, "parent": parent_id, "parent_n": int(parent_n),
            "cycle": 0, "n_new": int(i + 1),
            "seeds": {"init": int(init_seed), "data": int(data_seed), "eval": None},
            "heldout_sha256": (etat.sha256_file(heldout_path) if heldout_path else None),
            "code_sha": code_sha, "source": "synthetique",
            "regles": (sorted(regles) if regles else None),
            "metrics": {"ece_final": hist["ece"][-1] if hist["ece"] else None,
                        "acc_final": float(np.mean(oks)) if oks else None,
                        "ms_per_iter": round(1000.0 * dt / max(i + 1, 1), 3),
                        "items_per_s": round((i + 1) / max(dt, 1e-9), 1)}}
    etat.save_bundle(out_dir, model, mem, hist, meta)
    print(f"[{name}] paquet -> {out_dir}  ({time.time()-t0:.0f}s, {i+1} interactions)")
    return out_dir


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fragment", required=True)
    ap.add_argument("--init-seed", type=int, required=True)
    ap.add_argument("--data-seed", type=int, required=True)
    ap.add_argument("--n", type=int, default=5000)
    ap.add_argument("--out", required=True)
    ap.add_argument("--parent", default=None)
    ap.add_argument("--pool", type=int, default=1200)
    ap.add_argument("--budget-seconds", type=int, default=None)
    ap.add_argument("--code-sha", default="local")
    ap.add_argument("--heldout", default=None)
    ap.add_argument("--regles", default=None,
                    help="regles de gen_item autorisees (ex: arith,rep). Vide = toutes")
    ap.add_argument("--central-spec", default=None,
                    help="JSON [{data_seed,regles,pool},...] -> pool = concat des shards (LE CONTROLE)")
    a = ap.parse_args()
    print("device :", "cuda" if torch.cuda.is_available() else "cpu")
    run_fragment(a.fragment, a.init_seed, a.data_seed, a.n, a.out,
                 parent_dir=a.parent, pool_n=a.pool,
                 budget_seconds=a.budget_seconds, code_sha=a.code_sha,
                 heldout_path=a.heldout, regles=a.regles, central_spec=a.central_spec)


if __name__ == "__main__":
    main()
