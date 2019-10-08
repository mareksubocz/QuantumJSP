from __future__ import print_function

import matplotlib.pyplot as plt
import time
import neal

from dwave.system.composites import EmbeddingComposite
from dwave.system.samplers import DWaveSampler
from dwavebinarycsp.exceptions import ImpossibleBQM

from job_shop_scheduler import get_jss_bqm

from instance_parser import readInstance, find_time_window, solve_greedily

from pprint import pprint

# {1: [(2, 1), (0, 3), (1, 6), (3, 7), (5, 3), (4, 6)],
#  2: [(1, 8), (2, 5), (4, 10), (5, 10), (0, 10), (3, 4)],
#  3: [(2, 5), (3, 4), (5, 8), (0, 9), (1, 1), (4, 7)],
#  4: [(1, 5), (0, 5), (2, 5), (3, 3), (4, 8), (5, 9)],
#  5: [(2, 9), (1, 3), (4, 5), (5, 4), (0, 3), (3, 1)],
#  6: [(1, 3), (3, 3), (5, 9), (0, 10), (4, 4), (2, 1)]}

# {1: [0, 1, 19, 25, 44, 47],
#  2: [0, 15, 20, 30, 40, 50],
#  3: [1, 6, 10, 18, 27, 53],
#  4: [8, 13, 20, 32, 35, 47],
#  5: [6, 16, 30, 40, 50, 54],
#  6: [13, 16, 19, 28, 43, 47]}

better_solution = {1: [0, 1, 19, 25, 40, 47],
                   2: [0, 15, 20, 30, 40, 50],
                   3: [1, 6, 10, 18, 27, 53],
                   4: [8, 13, 20, 32, 35, 47],
                   5: [6, 16, 30, 43, 50, 54],
                   6: [13, 16, 19, 28, 43, 47]}

jobs = readInstance("/Users/mareksubocz/Downloads/ft06.txt")

max_time = 61
window_size = 12
solution = solve_greedily(jobs, max_time)
solution = better_solution
sampler = neal.SimulatedAnnealingSampler()

pprint(jobs)
pprint(solution)

# pprint(find_time_window(jobs, solution, 24, 31))

for i in range(max_time - window_size):
    new_jobs, operations_indexes, disable_till, disabled_variables = find_time_window(jobs, solution, i, i + window_size)
    # print(" \/" * 50)
    # pprint(new_jobs)
    # pprint(disable_till)
    # pprint(disabled_variables)
    # print(" /\\" * 50)
    if not bool(new_jobs):  # if new_jobs dict is empty
        continue
    try:
        bqm = get_jss_bqm(new_jobs, window_size + 1, disable_till, disabled_variables, stitch_kwargs={'min_classical_gap': 2.0})
    except ImpossibleBQM:
        print('*' * 25 + " It's impossible to construct a BQM " + '*' * 25)
        continue
    sampleset = sampler.sample(bqm, num_reads=3000)
    solution1 = sampleset.first.sample
    selected_nodes = [k for k, v in solution1.items() if v ==
                      1 and not k.startswith('aux')]
    # Parse node information
    task_times = {k: [-1] * len(v) for k, v in new_jobs.items()}
    for node in selected_nodes:
        job_name, task_time = node.rsplit("_", 1)
        task_index, start_time = map(int, task_time.split(","))

        task_times[int(job_name)][task_index] = start_time

    pprint(task_times)
    pprint(disable_till)
    pprint(disabled_variables)

    print(i)

    # improving original solution
    for job, times in task_times.items():
        for j in range(len(times)):
            if solution[job][operations_indexes[job][j]] != task_times[job][j] + i:
                print('!' * 100)
            solution[job][operations_indexes[job][j]] = task_times[job][j] + i
    pprint(solution)
