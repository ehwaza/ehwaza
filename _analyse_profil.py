# _analyse_profil.py — goulots de profile_5k.prof (LYNX, 03/10)
# Affiche le top cumulatif + le top par temps propre, filtre sur becvide.
import pstats, sys
p = pstats.Stats(r"F:\becvide\profile_5k.prof")
print("=== TOP 25 CUMULATIF ===")
p.sort_stats("cumulative").print_stats(25)
print("=== TOP 25 TEMPS PROPRE ===")
p.sort_stats("tottime").print_stats(25)
