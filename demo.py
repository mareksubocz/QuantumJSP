from instance_parser import readInstance, solve_worse, solve_greedily, get_result
from partial_brute_force import solve_with_pbruteforce
from pprint import pprint


# jobs = {1: [(2, 1), (0, 3), (1, 6), (3, 7), (5, 3), (4, 6)],
#         2: [(1, 8), (2, 5), (4, 10), (5, 10), (0, 10), (3, 4)],
#         3: [(2, 5), (3, 4), (5, 8), (0, 9), (1, 1), (4, 7)],
#         4: [(1, 5), (0, 5), (2, 5), (3, 3), (4, 8), (5, 9)],
#         6: [(1, 3), (3, 3), (5, 9), (0, 10), (4, 4), (2, 1)]}
jobs = readInstance("data/ft06.txt")
solution = solve_greedily(jobs, 70)

solution = {1: [14, 16, 20, 26, 45, 55],
            2: [3, 16, 21, 31, 43, 53],
            3: [9, 15, 19, 34, 43, 48],
            4: [11, 19, 24, 33, 40, 48],
            5: [0, 17, 31, 41, 53, 57],
            6: [0, 4, 7, 24, 36, 40]}
pprint(solution)
solution = solve_with_pbruteforce(jobs,
                                  solution,
                                  get_result(jobs, solution) + 1,
                                  qpu=False,
                                  window_size=11,
                                  num_reads=5000,
                                  chain_strength=2,
                                  times=10)
pprint(solution)
