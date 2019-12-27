from instance_parser import readInstance, solve_worse, solve_greedily
from instance_parser import get_result, checkValidity, get_order, solve_with_order
from partial_brute_force import solve_with_pbruteforce
from utilities import draw_solution
from pprint import pprint
from collections import defaultdict

# jobs = readInstance("data/ft06.txt")
jobs = {1: [(2, 1), (0, 1), (1, 2), (3, 3), (5, 1), (4, 2)],
        2: [(1, 3), (2, 2), (4, 3), (5, 3), (0, 3), (3, 2)],
        3: [(2, 2), (3, 2), (5, 3), (0, 3), (1, 1), (4, 3)],
        4: [(1, 2), (0, 2), (2, 2), (3, 1), (4, 3), (5, 3)],
        5: [(2, 3), (1, 1), (4, 2), (5, 2), (0, 1), (3, 1)],
        6: [(1, 1), (3, 1), (5, 3), (0, 3), (4, 2), (2, 1)]}

jobs2 = {1: [(2, 1), (0, 3), (1, 6), (3, 7), (5, 3), (4, 6)],
         2: [(1, 8), (2, 5), (4, 10), (5, 10), (0, 10), (3, 4)],
         3: [(2, 5), (3, 4), (5, 8), (0, 9), (1, 1), (4, 7)],
         4: [(1, 5), (0, 5), (2, 5), (3, 3), (4, 8), (5, 9)],
         5: [(2, 9), (1, 3), (4, 5), (5, 4), (0, 3), (3, 1)],
         6: [(1, 3), (3, 3), (5, 9), (0, 10), (4, 4), (2, 1)]}
for j in [5]:
    solution = {1: [14, 16, 20, 26, 45, 55],
                2: [3, 16, 21, 31, 43, 53],
                3: [9, 15, 19, 34, 43, 48],
                4: [11, 19, 24, 33, 40, 48],
                5: [0, 17, 31, 41, 53, 57],
                6: [0, 4, 7, 24, 36, 40]}
    while get_result(jobs2, solution) >= 60:
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
                    draw_solution(jobs2, s_origin, 'solrandom')
                    s_origin_prev = s_origin
                    print('hejka')
        except:
            continue
        print("końcowy rezultat: " + str(get_result(jobs2, s_origin)))
