import argparse
import random
import time
import sys
from pathlib import Path
from copy import deepcopy
from multiprocessing import Pool, cpu_count

# Ensure parent folder (I/) is on sys.path so `import data.config` works
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.config import n, target

# Force this script to always run 100 games unless you explicitly change this constant
ALWAYS_NUM_GAMES = 100


def in_bounds(i, j):
    return 0 <= i < n and 0 <= j < n


def check_positions_equal(matrice, positions, val, marcate):
    for x, y in positions:
        if not in_bounds(x, y) or matrice[x][y] != val or marcate[x][y] != 0:
            return False
    return True


def genereaza_matrice():
    matrice = []
    for i in range(n):
        rand = []
        for j in range(n):
            rand.append(random.randint(1, 4))
        matrice.append(rand)
    return matrice


def afiseaza_matrice(matrice):
    for i in range(n):
        for j in range(n):
            print(matrice[i][j], end=" ")
        print()
    print()


def gaseste_formatiuni(matrice):
    marcate = [[0 for _ in range(n)] for _ in range(n)]
    formatiuni = {}
    id_forma = 1

    def add_formation(pos_list, points):
        nonlocal id_forma
        for x, y in pos_list:
            marcate[x][y] = points
        formatiuni[id_forma] = {"pozitii": pos_list, "puncte": points}
        id_forma += 1

    # Precompute horizontal run lengths to the right and vertical run lengths downward
    run_right = [[1] * n for _ in range(n)]
    run_down = [[1] * n for _ in range(n)]
    for i in range(n):
        for j in range(n - 2, -1, -1):
            if matrice[i][j] != 0 and matrice[i][j] == matrice[i][j + 1]:
                run_right[i][j] = run_right[i][j + 1] + 1
            else:
                run_right[i][j] = 1
    for j in range(n):
        for i in range(n - 2, -1, -1):
            if matrice[i][j] != 0 and matrice[i][j] == matrice[i + 1][j]:
                run_down[i][j] = run_down[i + 1][j] + 1
            else:
                run_down[i][j] = 1

    # Detect straight runs (prioritize longer ones)
    for length, points in ((5, 50), (4, 10), (3, 5)):
        # horizontal
        for i in range(n):
            for j in range(n - length + 1):
                val = matrice[i][j]
                if val == 0:
                    continue
                if run_right[i][j] >= length:
                    # check marcate free
                    conflict = False
                    for k in range(length):
                        if marcate[i][j + k] != 0:
                            conflict = True
                            break
                    if not conflict:
                        pos = [(i, j + k) for k in range(length)]
                        add_formation(pos, points)
        # vertical
        for j in range(n):
            for i in range(n - length + 1):
                val = matrice[i][j]
                if val == 0:
                    continue
                if run_down[i][j] >= length:
                    conflict = False
                    for k in range(length):
                        if marcate[i + k][j] != 0:
                            conflict = True
                            break
                    if not conflict:
                        pos = [(i + k, j) for k in range(length)]
                        add_formation(pos, points)

        # Precompute horizontal run lengths to the left and vertical run lengths upward
        run_left = [[1] * n for _ in range(n)]
        run_up = [[1] * n for _ in range(n)]
        for i in range(n):
            for j in range(1, n):
                if matrice[i][j] != 0 and matrice[i][j] == matrice[i][j - 1]:
                    run_left[i][j] = run_left[i][j - 1] + 1
                else:
                    run_left[i][j] = 1
        for j in range(n):
            for i in range(1, n):
                if matrice[i][j] != 0 and matrice[i][j] == matrice[i - 1][j]:
                    run_up[i][j] = run_up[i - 1][j] + 1
                else:
                    run_up[i][j] = 1

        # L shapes (5 cells): check only candidate corner cells where two orthogonal legs of length>=3 meet
        for i in range(n):
            for j in range(n):
                val = matrice[i][j]
                if val == 0:
                    continue
                # up + right
                if run_up[i][j] >= 3 and run_right[i][j] >= 3:
                    pos = [(i - 2, j), (i - 1, j), (i, j), (i, j + 1), (i, j + 2)]
                    if check_positions_equal(matrice, pos, val, marcate):
                        add_formation(pos, 20)
                # up + left
                if run_up[i][j] >= 3 and run_left[i][j] >= 3:
                    pos = [(i - 2, j), (i - 1, j), (i, j), (i, j - 1), (i, j - 2)]
                    if check_positions_equal(matrice, pos, val, marcate):
                        add_formation(pos, 20)
                # down + right
                if run_down[i][j] >= 3 and run_right[i][j] >= 3:
                    pos = [(i, j), (i + 1, j), (i + 2, j), (i, j + 1), (i, j + 2)]
                    if check_positions_equal(matrice, pos, val, marcate):
                        add_formation(pos, 20)
                # down + left
                if run_down[i][j] >= 3 and run_left[i][j] >= 3:
                    pos = [(i, j), (i + 1, j), (i + 2, j), (i, j - 1), (i, j - 2)]
                    if check_positions_equal(matrice, pos, val, marcate):
                        add_formation(pos, 20)

        # T / plus shapes (5 cells): check only candidate center cells that have all four orthogonal neighbors
        for i in range(n):
            for j in range(n):
                val = matrice[i][j]
                if val == 0:
                    continue
                if run_left[i][j] >= 2 and run_right[i][j] >= 2 and run_up[i][j] >= 2 and run_down[i][j] >= 2:
                    pos = [(i, j), (i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)]
                    if check_positions_equal(matrice, pos, val, marcate):
                        add_formation(pos, 30)

    return formatiuni, marcate


def elimina_formatiuni(matrice, marcate, formatiuni):
    scor = 0
    for id_formatiune, info in formatiuni.items():
        puncte = info['puncte']
        pozitii = info['pozitii']
        scor += puncte
        for x, y in pozitii:
            matrice[x][y] = 0
            marcate[x][y] = 0
    return scor


def aplica_gravitatie(matrice):
    for j in range(n):
        write_idx = n - 1
        for i in range(n - 1, -1, -1):
            if matrice[i][j] != 0:
                matrice[write_idx][j] = matrice[i][j]
                if write_idx != i:
                    matrice[i][j] = 0
                write_idx -= 1
        for k in range(write_idx, -1, -1):
            matrice[k][j] = 0


def reumple_matrice(matrice):
    for i in range(n):
        for j in range(n):
            if matrice[i][j] == 0:
                matrice[i][j] = random.randint(1, 4)


def gaseste_swap(matrice):
    # Localized formation finder: only checks a small bounding box around swapped positions
    def gaseste_formatiuni_local(matrice, anchors):
        # anchors: iterable of (i,j) positions to build a small region around
        min_i = max(0, min(a[0] for a in anchors) - 2)
        max_i = min(n - 1, max(a[0] for a in anchors) + 2)
        min_j = max(0, min(a[1] for a in anchors) - 2)
        max_j = min(n - 1, max(a[1] for a in anchors) + 2)

        marcate = [[0 for _ in range(n)] for _ in range(n)]
        formatiuni = {}
        id_forma = 1

        def add_formation(pos_list, points):
            nonlocal id_forma
            for x, y in pos_list:
                marcate[x][y] = points
            formatiuni[id_forma] = {"pozitii": pos_list, "puncte": points}
            id_forma += 1

        # Straight runs (horizontal/vertical) within the small region
        for length, points in ((5, 50), (4, 10), (3, 5)):
            for i in range(min_i, max_i + 1):
                for j in range(max(min_j, 0), max_j - length + 2):
                    val = matrice[i][j]
                    if val == 0:
                        continue
                    ok = True
                    for k in range(length):
                        x, y = i, j + k
                        if y < min_j or y > max_j or matrice[x][y] != val or marcate[x][y] != 0:
                            ok = False
                            break
                    if ok:
                        pos = [(i, j + k) for k in range(length)]
                        add_formation(pos, points)
            for j in range(min_j, max_j + 1):
                for i in range(max(min_i, 0), max_i - length + 2):
                    val = matrice[i][j]
                    if val == 0:
                        continue
                    ok = True
                    for k in range(length):
                        x, y = i + k, j
                        if x < min_i or x > max_i or matrice[x][y] != val or marcate[x][y] != 0:
                            ok = False
                            break
                    if ok:
                        pos = [(i + k, j) for k in range(length)]
                        add_formation(pos, points)

        # L shapes and T shapes inside region (brute-force over region but small)
        L_patterns = [
            [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)],
            [(0, 0), (1, 0), (2, 0), (2, -1), (2, -2)],
            [(0, 0), (0, -1), (0, -2), (1, -2), (2, -2)],
            [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2)],
        ]
        for i in range(min_i, max_i + 1):
            for j in range(min_j, max_j + 1):
                val = matrice[i][j]
                if val == 0:
                    continue
                for pat in L_patterns:
                    valid = True
                    pos = []
                    for dx, dy in pat:
                        x, y = i + dx, j + dy
                        if x < min_i or x > max_i or y < min_j or y > max_j or matrice[x][y] != val or marcate[x][y] != 0:
                            valid = False
                            break
                        pos.append((x, y))
                    if valid:
                        add_formation(pos, 20)

        T_patterns = [
            [(0, 0), (0, -1), (0, 1), (-1, 0), (1, 0)],
            [(0, 0), (0, -1), (0, 1), (1, 0), (-1, 0)],
            [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)],
            [(0, 0), (-1, 0), (1, 0), (0, 1), (0, -1)],
        ]
        for i in range(min_i, max_i + 1):
            for j in range(min_j, max_j + 1):
                val = matrice[i][j]
                if val == 0:
                    continue
                for pat in T_patterns:
                    valid = True
                    pos = []
                    for dx, dy in pat:
                        x, y = i + dx, j + dy
                        if x < min_i or x > max_i or y < min_j or y > max_j or matrice[x][y] != val or marcate[x][y] != 0:
                            valid = False
                            break
                        pos.append((x, y))
                    if valid:
                        add_formation(pos, 30)

        return formatiuni, marcate

    directions = [(1, 0), (0, 1)]
    for i in range(n):
        for j in range(n):
            for dx, dy in directions:
                ni, nj = i + dx, j + dy
                if not in_bounds(ni, nj):
                    continue
                matrice[i][j], matrice[ni][nj] = matrice[ni][nj], matrice[i][j]
                # local check around the swapped cells
                formatiuni, marcate = gaseste_formatiuni_local(matrice, [(i, j), (ni, nj)])
                matrice[i][j], matrice[ni][nj] = matrice[ni][nj], matrice[i][j]
                if formatiuni:
                    return (i, j), (ni, nj), formatiuni
    return None


def proceseaza_matrice(matrice):
    matrice = deepcopy(matrice)
    scor_total = 0
    contor_swap = 0
    reached_target = False
    motiv_oprire = ""
    start_timp = time.time()

    while scor_total < target:
        formatiuni, marcate = gaseste_formatiuni(matrice)
        if not formatiuni:
            swap = gaseste_swap(matrice)
            if swap is None:
                break
            (i1, j1), (i2, j2), formatiuni = swap
            matrice[i1][j1], matrice[i2][j2] = matrice[i2][j2], matrice[i1][j1]
            contor_swap += 1

        # cascade until stable
        while formatiuni:
            scor = elimina_formatiuni(matrice, marcate, formatiuni)
            scor_total += scor
            aplica_gravitatie(matrice)
            reumple_matrice(matrice)
            formatiuni, marcate = gaseste_formatiuni(matrice)

    stop_time = time.time()
    durata = stop_time - start_timp

    if scor_total >= target:
        reached_target = True
        motiv_oprire = "REACHED_TARGET"

    return scor_total, contor_swap, durata, reached_target, motiv_oprire


def process_single(matrice):
    return proceseaza_matrice(matrice)


def load_matrices_from_file(path):
    matrices = []
    with open(path, 'r') as f:
        matr = []
        for linie in f:
            linie = linie.strip()
            if linie:
                matr.append([int(x) for x in linie.split()])
            else:
                if matr:
                    matrices.append(matr)
                    matr = []
        if matr:
            matrices.append(matr)
    return matrices


def write_results(results_file, rezultate):
    with open(results_file, 'w') as f:
        for linie in rezultate:
            f.write(linie + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--use-tests', action='store_true', help='Load matrices from tests file')
    parser.add_argument('--workers', type=int, default=0, help='Number of parallel workers (0=auto, default: auto)')
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    tests_file = base_dir.parent / 'tests' / 'matrici_test.txt'
    results_file = base_dir.parent / 'results' / 'rezultate.csv'

    # Enforce ALWAYS_NUM_GAMES regardless of config or args
    desired = ALWAYS_NUM_GAMES

    if args.use_tests and tests_file.exists():
        matrices = load_matrices_from_file(tests_file)
        # If tests file has fewer or more matrices than desired, trim or pad with randoms
        if len(matrices) < desired:
            matrices += [genereaza_matrice() for _ in range(desired - len(matrices))]
        elif len(matrices) > desired:
            matrices = matrices[:desired]
    else:
        matrices = [genereaza_matrice() for _ in range(desired)]

    nr_matrice = len(matrices)

    start = time.time()
    rezultate = []
    avg_swap = 0
    avg_puncte = 0
    timp_total = 0

    # Determine workers: 0 means auto -> use cpu_count()-1 to leave one core free
    if args.workers <= 0:
        workers = max(1, cpu_count() - 1)
    else:
        workers = args.workers

    if workers > 1 and nr_matrice > 1:
        # Use imap_unordered with a chunksize tuned to number of workers for better throughput
        chunksize = max(1, nr_matrice // (workers * 4))
        with Pool(processes=workers) as p:
            results = list(p.imap_unordered(process_single, matrices, chunksize))
    else:
        results = [process_single(m) for m in matrices]

    for idx, (scor_total, cnt_swap, durata, reached_target, motiv) in enumerate(results, start=1):
        rezultate.append(f"Jocul {idx}: Scor total = {scor_total}, Swap-uri = {cnt_swap}, Motiv oprire = {motiv}, Timp = {durata:.2f} secunde")
        avg_swap += cnt_swap
        avg_puncte += scor_total
        timp_total += durata

    avg_swap /= nr_matrice
    avg_timp = timp_total / nr_matrice
    avg_puncte /= nr_matrice

    rezultate.append("\nMedie rezultate:\n")
    rezultate.append(f"1.Medie swap-uri: {avg_swap}")
    rezultate.append(f"2.Medie timp: {avg_timp:.2f}")
    rezultate.append(f"3.Timp total: {timp_total:.2f}")
    rezultate.append(f"4.Medie puncte: {avg_puncte}")

    write_results(results_file, rezultate)
    stop = time.time()
    print(f"Finished {nr_matrice} games in {stop - start:.2f}s. Results written to {results_file}")


if __name__ == '__main__':
    main()
