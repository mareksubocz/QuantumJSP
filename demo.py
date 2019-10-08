from __future__ import print_function

import matplotlib.pyplot as plt
import time
import neal

from dwave.system.composites import EmbeddingComposite
from dwave.system.samplers import DWaveSampler

from job_shop_scheduler import get_jss_bqm

from instance_parser import readInstance, transformToMachineDict, find_time_window, solve_greedily

from pprint import pprint

jobs = readInstance("/Users/mareksubocz/Downloads/ft06.txt")
# old_jobs = {"1": [(0, 4), (1, 2), (2, 3), (2, 1), (1, 2)],
#             "2": [(1, 5), (0, 1), (2, 2), (0, 2), (2, 3)],
#             "3": [(1, 3), (2, 2), (0, 2), (0, 1), (1, 3)]}
pprint(jobs)
pprint(solve_greedily(jobs, 70))

# jobs2 = {"a": [("0", 2), ("1", 2)],
#          "b": [("1", 1), ("0", 3)]}

# jobs = {"a": [("1", 2)],
#         "b": [("0", 1)]}

solution = {"1": [0, 8, 10, 15, 16],
            "2": [0, 5, 13, 15, 17],
            "3": [5, 8, 10, 17, 18]}
# trwa 21
# pprint(find_time_window(jobs, solution, 1, 6))

max_time = 5

tw_start = 10
tw_end = 17
jobs, disabled_times, disabled_variables = find_time_window(jobs, solution, tw_start, tw_end)
pprint(jobs)
pprint(disabled_times)
pprint(disabled_variables)
# bqm = get_jss_bqm(jobs, max_time, stitch_kwargs={'min_classical_gap': 2.0})

bqm = get_jss_bqm(jobs, tw_end - tw_start, disabled_times, disabled_variables, stitch_kwargs={'min_classical_gap': 2.0})

# Submit BQM
# sampler = EmbeddingComposite(DWaveSampler(solver={'qpu': True}))
# sampleset = sampler.sample(bqm, chain_strength=1, num_reads=1000)

# Test Locally
# sampler = neal.SimulatedAnnealingSampler()
# sampleset = sampler.sample(bqm, num_reads=1000)

# Node pattern:
# <job>_<task_index>,<time>


def printResults():
    solution_dict = {"error": 0}
    best_result = 99999
    num_of_best_results = 0
    num_of_errors = 0
    total = 0
    best_solution = {}

    for sample, energy, occurrences in sampleset.data(
        ["sample", "energy", "num_occurrences"]
    ):
        error_found = False
        total = total + occurrences
        selected_nodes = [k for k, v in sample.items() if v ==
                          1 and not k.startswith('aux')]

        # Parse node information
        task_times = {k: [-1] * len(v) for k, v in jobs.items()}
        for node in selected_nodes:
            job_name, task_time = node.rsplit("_", 1)
            task_index, start_time = map(int, task_time.split(","))
            task_times[job_name][task_index] = start_time

        result = 0
        for job, times in task_times.items():
            if -1 in times:
                error_found = True
                break
            result = max(result, times[-1] + jobs[job][-1][1])

        if(error_found):
            num_of_errors += occurrences
            solution_dict["error"] += 1
            continue
        if(result in solution_dict):
            solution_dict[result] += 1
        else:
            solution_dict[result] = 1

        if(result == best_result):
            num_of_best_results += occurrences
        elif(result < best_result):
            best_result = result
            num_of_best_results = occurrences
            best_solution = sample

    selected_nodes = [k for k, v in best_solution.items() if v ==
                      1 and not k.startswith('aux')]
    # Parse node information
    task_times = {k: [-1] * len(v) for k, v in jobs.items()}
    for node in selected_nodes:
        job_name, task_time = node.rsplit("_", 1)
        task_index, start_time = map(int, task_time.split(","))

        task_times[job_name][task_index] = start_time

    for job, times in task_times.items():
        print("{0:9}: {1}".format(job, times))

    print(solution_dict)
    return solution_dict


# ***************** Test Locally *******************
sampler = neal.SimulatedAnnealingSampler()
sampleset = sampler.sample(bqm, num_reads=1000)
solution1 = sampleset.first.sample
selected_nodes = [k for k, v in solution1.items() if v ==
                  1 and not k.startswith('aux')]
# Parse node information
task_times = {k: [-1] * len(v) for k, v in jobs.items()}
for node in selected_nodes:
    job_name, task_time = node.rsplit("_", 1)
    task_index, start_time = map(int, task_time.split(","))

    task_times[job_name][task_index] = start_time

for job, times in task_times.items():
    print("{0:9}: {1}".format(job, times))

# sdl = printResults()
# **************************************************
# plt.plot(list(sdl.keys()), list(sdl.values()), 'ro')
# plt.xticks(range(len(sdl)), list(sdl.keys()))

# # Submit BQM
# sampler = EmbeddingComposite(DWaveSampler(solver={'qpu': True}))
# sampleset = sampler.sample(bqm, chain_strength=3, num_reads=1000)
# sdq = printResults()
# plt.plot(list(sdq.keys()), list(sdq.values()), 'bo')
# # plt.xticks(range(len(sdq)), list(sdq.keys()))
# plt.legend(["Lokalnie", "Na QPU"])
# plt.title(f'Dla {len(jobs)} jobów po {len(jobs["1"])} zadania, maksymalny czas: {max_time}')
# plt.xlabel(f'Cmax\n\nWyniki lokalne:\n{str(sdl)}\nWyniki na QPU:\n{str(sdq)}')
# plt.ylabel('liczba wystąpień')
# plt.subplots_adjust(bottom=0.28)
# plt.show()

# print("Number of jobs:", len(jobs))
# print("Number of tasks in each job:", len(jobs["1"]))
# print("Max time value:", max_time)
# print("QPU time used:", sampleset.info['timing']
#   ['qpu_access_time'] / 1000, "milliseconds.")
# print("Real time passed:", endTime - startTime, "seconds")
# print("Total occurrences:", total)
# print("Number of error solutions:", num_of_errors)
# print("Number of non-optimal results:", total -
#       num_of_best_results - num_of_errors)
# print("Number of best results:", num_of_best_results)
# print("Best result:", best_result)
