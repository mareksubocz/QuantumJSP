from __future__ import print_function

import matplotlib.pyplot as plt
import time
import neal

from dwave.system.composites import EmbeddingComposite
from dwave.system.samplers import DWaveSampler

from job_shop_scheduler import get_jss_bqm

from instance_parser import readInstance, find_time_window, solve_greedily

from pprint import pprint


jobs = readInstance("/Users/mareksubocz/Downloads/ft06.txt")


max_time = 70
window_size = 7
solution = solve_greedily(jobs, max_time)
sampler = neal.SimulatedAnnealingSampler()

pprint(jobs)
pprint(solution)

for i in range(max_time - window_size):
    new_jobs, disabled_times, disabled_variables = find_time_window(jobs, solution, i, i + window_size)
    pprint(new_jobs)
    if not bool(new_jobs):  # if new_jobs dict is empty
        continue
    bqm = get_jss_bqm(new_jobs, window_size + 1, disabled_times, disabled_variables, stitch_kwargs={'min_classical_gap': 2.0})
    sampleset = sampler.sample(bqm, num_reads=1000)
    solution1 = sampleset.first.sample
    selected_nodes = [k for k, v in solution1.items() if v ==
                      1 and not k.startswith('aux')]
    # Parse node information
    task_times = {k: [-1] * len(v) for k, v in new_jobs.items()}
    for node in selected_nodes:
        job_name, task_time = node.rsplit("_", 1)
        task_index, start_time = map(int, task_time.split(","))

        task_times[int(job_name)][task_index] = start_time

    for job, times in task_times.items():
        print("{0:9}: {1}".format(job, times))
