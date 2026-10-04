# -*- coding: utf-8 -*-
"""Enrichit rapport_reel.json : bloc ENGAGEMENT + drapeaux par bloc (ajours LYNX a,b,c,e)."""
import json
from pathlib import Path

p = Path(r"F:\becvide\rapport_reel.json")
rap = json.loads(p.read_text(encoding="utf-8"))

raf = rap.get("_prioritaire") or {}
rap["engagement"] = {
    "probe_fichier": "probe_vie.npz",
    "probe_sha256": "1c34d5efa67638bef639a72204bf6033cb4863dbe36fef2512854616a9af228b",
    "probe_graine": 20261004, "probe_n": 2000,
    "probe_determinisme": "verifie : 2 generations -> meme sha",
    "nectar_depot": "ehwaza/bebe-ia", "nectar_commit": "b871661",
    "nectar_fichier": "resultats/nectar_lignes.jsonl",
    "nectar_blob_sha256_LF": "cfebe88d112820d2ccefc1cf2705bd69bcce4be9ab79e57c121beabc4b80e0a4",
    "nectar_blob_taille_LF": 844164,
    "nectar_local_sha256_CRLF": "293e7734d1875b94e0ab21b4097c30ed60c4460382529f168ed730df2edf4615",
    "nectar_local_taille_CRLF": 844167,
    "nectar_ecart": "3 octets = 3 fins de ligne (core.autocrlf)",
    "lignes_h16": ["caf9ea4280a3fa73", "ed28088771caafad", "dcbc2b08701b687e"],
    "chevauchement_contexte": 0.591,
    "chevauchement_note": "UPPER BOUND (vecteur = histogramme de caracteres ; 2 src distincts peuvent partager le meme octet). Calcule par LYNX ET recalcule par Claude (convergent).",
    "bootstrap": {"n_reechantillons": 2000, "graine": 5},
    "beta": 0.5, "beta_note": "FIGE AVANT tout resultat reel ; pas de sweep",
    "n_graines": 10, "chance_1sur39": 0.02564102564102564,
    "gel": "poids init graine s, AUCUN entrainement, miel au consult seulement",
}

# drapeaux par bloc : IC croise 0 (b) et sigma=0 (c)
croise0, sigma0, nreq_gt10 = [], [], []
for mode in ("souple", "dur"):
    for niche in ("n0", "n1", "n2"):
        for b, bl in rap[mode][niche]["blocs"].items():
            tag = f"{mode}/{niche}/{b}"
            lo, hi = bl["ic95"]
            bl["ic_croise_zero"] = (lo <= 0 <= hi)
            bl["sigma_zero"] = (bl["sigma_d"] == 0.0)
            if bl["ic_croise_zero"]:
                croise0.append(tag)
            if bl["sigma_zero"]:
                sigma0.append(tag)
            if bl["n_requis"] > 10:
                nreq_gt10.append((tag, bl["n_requis"]))

rap["_drapeaux"] = {
    "ic_croise_zero": croise0,
    "sigma_zero": sigma0,
    "n_requis_gt10": sorted(nreq_gt10, key=lambda t: -t[1]),
    "n_requis_max": max((n for _, n in nreq_gt10), default=10),
}
p.write_text(json.dumps(rap, indent=2, ensure_ascii=False), encoding="utf-8")
print("croise0:", croise0)
print("sigma0 :", sigma0)
print("n_requis>10 (", len(nreq_gt10), " blocs ) max:", rap["_drapeaux"]["n_requis_max"])
print("->", p)
