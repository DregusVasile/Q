import cProfile
import pstats
import io
import random
import sys
from pathlib import Path

# Ensure local src is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

from candycrush import gaseste_formatiuni, gaseste_swap, genereaza_matrice

random.seed(0)

def profile_gaseste_formatiuni(iters=200):
    mats = [genereaza_matrice() for _ in range(iters)]
    pr = cProfile.Profile()
    pr.enable()
    for m in mats:
        gaseste_formatiuni(m)
    pr.disable()
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumtime')
    ps.print_stats(30)
    print("---- gaseste_formatiuni profile ----")
    print(s.getvalue())


def profile_gaseste_swap(iters=100):
    mats = [genereaza_matrice() for _ in range(iters)]
    pr = cProfile.Profile()
    pr.enable()
    for m in mats:
        gaseste_swap(m)
    pr.disable()
    s = io.StringIO()
    pstats.Stats(pr, stream=s).sort_stats('cumtime').print_stats(30)
    print("---- gaseste_swap profile ----")
    print(s.getvalue())


if __name__ == '__main__':
    print('Profiling gaseste_formatiuni (200 iters)...')
    profile_gaseste_formatiuni(200)
    print('\nProfiling gaseste_swap (100 iters)...')
    profile_gaseste_swap(100)
