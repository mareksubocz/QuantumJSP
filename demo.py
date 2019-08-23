from __future__ import print_function

from dwave.system.composites import EmbeddingComposite
from dwave.system.samplers import DWaveSampler

from job_shop_scheduler import get_jss_bqm

import time
import operator

startTime = time.time()


# Construct a BQM for the jobs
jobs = {"1": [("a", 2), ("b", 1), ("c", 2)],
        "2": [("b", 1), ("c", 2), ("a", 1)],
        "3": [("c", 1), ("a", 1), ("b", 2)]}

# jobs = {"1": [("2", 1), ("0", 3), ("1", 6), ("3", 7), ("5", 3), ("4", 6)],
#         "2": [("1", 8), ("2", 5), ("4", 10), ("5", 10), ("0", 10), ("3", 4)],
#         "3": [("2", 5), ("3", 4), ("5", 8), ("0", 9), ("1", 1), ("4", 7)],
#         "4": [("1", 5), ("0", 5), ("2", 5), ("3", 3), ("4", 8), ("5", 9)],
#         "5": [("2", 9), ("1", 3), ("4", 5), ("5", 4), ("0", 3), ("3", 1)],
#         "6": [("1", 3), ("3", 3), ("5", 9), ("0", 10), ("4", 4), ("2", 1)]}

max_time = 7	  # Upperbound on how long the schedule can be; 4 is arbitrary
bqm = get_jss_bqm(jobs, max_time, stitch_kwargs={'min_classical_gap':0.5})

# Submit BQM
sampler = EmbeddingComposite(DWaveSampler(solver={'qpu':True}))
sampleset = sampler.sample(bqm, chain_strength=2, num_reads=1000)

# solution = sampleset.first.sample

# Visualize solution
# Note0: we are making the solution simpler to interpret by restructuring it
#  into the following format:
#   task_times = {"job": [start_time_for_task0, start_time_for_task1, ..],
#                 "other_job": [start_time_for_task0, ..]
#                 ..}
#
# Note1: each node in our BQM is labelled as "<job>_<task_index>,<time>".
#  For example, the node "cupcakes_1,2" refers to job 'cupcakes', its 1st task
#  (where we are using zero-indexing, so task '("oven", 1)'), starting at time
#  2.


endTime = time.time()

# # Print problem and restructured solution
#* print("Jobs and their machine-specific tasks:")
#* for job, task_list in jobs.items():
#*     print("{0:9}: {1}".format(job, task_list))

# min_energy = next(sampleset.data(["energy"]))[0]

solution_dict = {}
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

    selected_nodes = [k for k, v in sample.items() if v == 1]

    # Parse node information
    task_times = {k: [-1]*len(v) for k, v in jobs.items()}
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

    if(error_found == True):
        num_of_errors += occurrences
        continue

    if(result == best_result):
        num_of_best_results += occurrences
    elif(result < best_result):
        best_result = result
        num_of_best_results = occurrences
        best_solution = sample

# for key, val in sorted_solution_dict:
#         print(key, "\noccurrences: ", val)

selected_nodes = [k for k, v in best_solution.items() if v == 1]
# Parse node information
task_times = {k: [-1]*len(v) for k, v in jobs.items()}
for node in selected_nodes:
    job_name, task_time = node.rsplit("_", 1)
    task_index, start_time = map(int, task_time.split(","))

    task_times[job_name][task_index] = start_time

for job, times in task_times.items():
     print("{0:9}: {1}".format(job, times))

print("Number of jobs:", len(jobs))
print("Number of tasks in each job:", len(jobs["1"]))
print("Max time value:", max_time)
print("QPU time used:", sampleset.info['timing']['qpu_access_time'] / 1000, "milliseconds.")
print("Real time passed:", endTime - startTime, "seconds")
print("Total occurrences:", total)
print("Number of error solutions:", num_of_errors)
print("Number of non-optimal results:", total - num_of_best_results - num_of_errors)
print("Number of best results:", num_of_best_results)
print("Best result:", best_result)