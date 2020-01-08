from instance_parser import readInstance, solve_worse, solve_greedily
from instance_parser import get_result, checkValidity, get_order, solve_with_order
from partial_brute_force import solve_with_pbruteforce
from utilities import draw_solution
from pprint import pprint
from collections import defaultdict
from copy import deepcopy
import sys

jobs2 = readInstance(sys.argv[1])
# jobs2 = readInstance("data/ft06.txt")
jobs = deepcopy(jobs2)
for operations in jobs.values():
    for j, operation in enumerate(operations):
        if operation[1] <= 3:
            operations[j] = (operation[0], 1)
        elif operation[1] <= 6:
            operations[j] = (operation[0], 2)
        else:
            operations[j] = (operation[0], 3)
# jobs = {1: [(2, 1), (0, 1), (1, 2), (3, 3), (5, 1), (4, 2)],
#         2: [(1, 3), (2, 2), (4, 3), (5, 3), (0, 3), (3, 2)],
#         3: [(2, 2), (3, 2), (5, 3), (0, 3), (1, 1), (4, 3)],
#         4: [(1, 2), (0, 2), (2, 2), (3, 1), (4, 3), (5, 3)],
#         5: [(2, 3), (1, 1), (4, 2), (5, 2), (0, 1), (3, 1)],
#         6: [(1, 1), (3, 1), (5, 3), (0, 3), (4, 2), (2, 1)]}

# jobs2 = {1: [(2, 1), (0, 3), (1, 6), (3, 7), (5, 3), (4, 6)],
#          2: [(1, 8), (2, 5), (4, 10), (5, 10), (0, 10), (3, 4)],
#          3: [(2, 5), (3, 4), (5, 8), (0, 9), (1, 1), (4, 7)],
#          4: [(1, 5), (0, 5), (2, 5), (3, 3), (4, 8), (5, 9)],
#          5: [(2, 9), (1, 3), (4, 5), (5, 4), (0, 3), (3, 1)],
#          6: [(1, 3), (3, 3), (5, 9), (0, 10), (4, 4), (2, 1)]}

for j in [5]:
    solution = solve_greedily(jobs2, 70)
    print("początkowy rezultat: " + str(get_result(jobs2, solution)))
    print("Zaczynamy dla window " + str(j))
    for i in range(11):
        print("Pętla nr " + str(i))
        try:
            solution, solutions = solve_with_pbruteforce(
                jobs,
                solution,
                get_result(
                    jobs, solution) + 1,
                qpu=False,
                window_size=j,
                num_reads=5000,
                chain_strength=2,
                times=5)
            s_origin_prev = solution
            for s in solutions:
                order_s = get_order(s)
                s_origin = solve_with_order(jobs2, order_s)
                if s_origin != s_origin_prev:
                    draw_solution(jobs2, s_origin, 'rysunki')
                    s_origin_prev = s_origin
                    print('Dodano rysunek')
        except:
            continue
        print("końcowy rezultat: " + str(get_result(jobs2, s_origin)))
