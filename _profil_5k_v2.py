# _profil_5k_v2.py — profil de COMPARAISON apres port MemoireConsolidee (LYNX, 03/10)
# Meme banc que profile_5k.prof (run_bras 5000) mais SANS main() :
# main() ecrit sorties/ -> on ne touche jamais aux resultats existants.
import sys, cProfile, pstats
sys.path.insert(0, r"F:\becvide")
import banc

OUT = r"F:\becvide\profile_5k_v2.prof"

def go():
    banc.run_bras(5000, log_every=100)

cProfile.run("go()", OUT)
p = pstats.Stats(OUT)
print("=== TOP 15 TEMPS PROPRE (v2, memoire consolidee) ===")
p.sort_stats("tottime").print_stats(15)
print(f"profil ecrit: {OUT}")
