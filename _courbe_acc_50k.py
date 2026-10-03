# -*- coding: utf-8 -*-
"""Courbe d'accuracy du run 50k RECONSTRUITE depuis le log du job.

Le banc ne trace pas (encore) l'accuracy par 100 interactions ; le log,
lui, contient accA et accB a chaque pas de 100. C n'est pas dans le log :
c'est un predicteur aleatoire, accuracy theorique constante 1/39 = 0.026
(ligne de reference en pointilles).

Usage : python _courbe_acc_50k.py   (rejouable a tout moment, le log grandit)
"""
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

LOG = Path(r"C:\Users\Mathieu\Documents\Replicant_V7_Desktop"
           r"\.replicant\jobs\20261003-213656-b398.log")
OUT = Path(r"F:\becvide\sorties\courbe_accuracy_50k.png")

pat = re.compile(r"\[\s*(\d+)/50000\].*accA=([\d.]+)\s+accB=([\d.]+)")
xs, acc_a, acc_b = [], [], []
for ligne in LOG.read_text(encoding="utf-8", errors="replace").splitlines():
    m = pat.search(ligne)
    if m:
        xs.append(int(m.group(1)))
        acc_a.append(float(m.group(2)))
        acc_b.append(float(m.group(3)))

if not xs:
    sys.exit("aucune donnee d'accuracy dans le log (run pas encore en boucle ?)")

plt.figure(figsize=(9, 5))
plt.plot(xs, acc_a, color="tab:blue", label="A bebe (en-ligne, sans supervision)")
plt.plot(xs, acc_b, color="tab:red", label="B supervise (temperature)")
plt.axhline(1 / 39, color="gray", linestyle="--",
            label="C baseline (1/39 = 0.026, hasard)")
plt.xlabel("interactions")
plt.ylabel("accuracy")
plt.title(f"ACCURACY vs interactions — run 50k ({xs[-1]}/50000)")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
OUT.parent.mkdir(exist_ok=True)
plt.savefig(OUT, dpi=120)
print(f"OK {len(xs)} points, dernier = {xs[-1]}/50000 -> {OUT}")
