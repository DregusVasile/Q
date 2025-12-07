import random
import sys
from pathlib import Path

# Ensure parent folder (I/) is on sys.path so `import data.config` works
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.config import n, nr_matrici

# Functie care genereaza matricile random
def genereaza_matrice():
    matrice = []
    for i in range(n):
        rand = []
        for j in range(n):
            valoare = random.randint(1,4)
            rand.append(valoare)
        matrice.append(rand)
    return matrice

# Punem matricile generate in fisier
base_dir = Path(__file__).resolve().parent
tests_file = base_dir.parent / "tests" / "matrici_test.txt"

with open(tests_file, "w") as f:
    for i in range(nr_matrici):
        matrice = genereaza_matrice()
        for rand in matrice:
            rand_curent = ""
            for nr in rand:
                rand_curent += str(nr) + " "
            f.write(rand_curent + "\n")
        f.write("\n")