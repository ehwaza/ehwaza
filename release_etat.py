# -*- coding: utf-8 -*-
"""release_etat.py — paquet d'etat -> RELEASE GitHub 'etat-courant' (assets).

SPEC_ECHANGE.md §7 : le paquet circule par ASSETS de release, JAMAIS par commit.
Ce script :
  (a) fabrique le paquet RACINE (le bebe nait : poids aleatoires, memoire vide) ;
  (b) VERIFIE qu'un paquet est conforme C1-C5 avant de le publier ;
  (c) publie le paquet + heldout.npz comme release 'etat-courant'.

Usage :
  python release_etat.py init <seed_init> <out_dir>        # paquet racine
  python release_etat.py check <bundle_dir>                # verif C1-C5, sans publier
  python release_etat.py push  <bundle_dir> [--tag etat-courant]
"""
import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np
import torch

import banc
import etat

CHAMPS_NPZ = {"keys", "y_counts", "ok", "n", "last_seen", "k"}


def init(seed_init, out_dir):
    torch.manual_seed(int(seed_init))
    model = banc.Bebe()
    mem = etat.MemoireConsolidee(k=5)
    hist = {"conf": np.zeros(0, np.float32), "ok": np.zeros(0, np.float32),
            "ece": np.zeros(0, np.float32)}
    meta = {"fragment": "root", "parent": "root", "cycle": -1, "parent_n": 0,
            "n_new": 0, "seeds": {"init": int(seed_init), "data": -1, "eval": 999},
            "heldout_sha256": (etat.sha256_file("heldout.npz") if Path("heldout.npz").exists() else None),
            "code_sha": "root", "metrics": {}}
    etat.save_bundle(out_dir, model, mem, hist, meta)
    print("paquet racine ->", out_dir, "| arch", etat.arch_of(model))


def check(bundle_dir, heldout="heldout.npz"):
    b = etat.load_bundle(bundle_dir)
    m = b["meta"]
    errs = []
    if m.get("format") != etat.FORMAT:
        errs.append(f"format != {etat.FORMAT}")
    for k in ("fragment", "parent", "cycle", "parent_n", "n_new", "arch",
              "seeds", "heldout_sha256", "code_sha", "metrics"):
        if k not in m:
            errs.append("meta manque " + k)
    if "arch" in m and set(m["arch"]) != {"d", "nl", "heads", "nv"}:
        errs.append("arch != d/nl/heads/nv (C1)")
    z = np.load(Path(bundle_dir) / "memoire.npz")
    if set(z.files) != CHAMPS_NPZ:
        errs.append(f"champs npz {sorted(z.files)} != {sorted(CHAMPS_NPZ)} (C5)")
    else:
        if z["keys"].dtype != np.float32:
            errs.append("keys != float32")
        if z["y_counts"].dtype != np.int32:
            errs.append("y_counts != int32 (C3)")
    if Path(heldout).exists() and m.get("heldout_sha256"):
        if m["heldout_sha256"] != etat.sha256_file(heldout):
            errs.append("heldout_sha256 != heldout.npz local")
    return errs


def push(bundle_dir, tag="etat-courant", heldout="heldout.npz"):
    errs = check(bundle_dir, heldout)
    if errs:
        print("PAQUET NON CONFORME :", errs)
        sys.exit(1)
    files = [str(Path(bundle_dir) / f) for f in ("model.pt", "memoire.npz", "hist.npz", "meta.json")]
    if Path(heldout).exists():
        files.append(str(heldout))
    subprocess.run(["gh", "release", "delete", tag, "--yes", "--cleanup-tag"], check=False)
    subprocess.run(["gh", "release", "create", tag, *files,
                    "--title", tag, "--notes",
                    "paquet d'etat (format bebe-etat/1) + heldout.npz"], check=True)
    print("release", tag, "<-", [Path(f).name for f in files])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["init", "check", "push"])
    ap.add_argument("a", help="seed_init (init) ou dossier paquet (check/push)")
    ap.add_argument("b", nargs="?", help="out_dir (init)")
    ap.add_argument("--tag", default="etat-courant")
    ap.add_argument("--heldout", default="heldout.npz")
    x = ap.parse_args()
    if x.cmd == "init":
        init(int(x.a), x.b or "etat_racine")
    elif x.cmd == "check":
        e = check(x.a, x.heldout)
        print("CONFORME" if not e else "NON CONFORME : " + str(e))
        sys.exit(1 if e else 0)
    else:
        push(x.a, x.tag, x.heldout)
