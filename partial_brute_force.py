from __future__ import print_function

import time
import neal

from dwave.system.composites import EmbeddingComposite
from dwave.system.samplers import DWaveSampler
from dwavebinarycsp.exceptions import ImpossibleBQM

from job_shop_scheduler import get_jss_bqm

from instance_parser import find_time_window, solve_greedily

from pprint import pprint


def solve_with_pbruteforce(jobs, window_size, max_time):
    solution = solve_greedily(jobs, max_time)
    sampler = neal.SimulatedAnnealingSampler()
    for i in range(max_time - window_size):
        new_jobs, operations_indexes, disable_till, disabled_variables = find_time_window(jobs, solution, i, i + window_size)
        if not bool(new_jobs):  # if new_jobs dict is empty
            continue
        try:
            bqm = get_jss_bqm(new_jobs, window_size + 1, disable_till, disabled_variables, stitch_kwargs={'min_classical_gap': 2.0})
        except ImpossibleBQM:
            # print('*' * 25 + " It's impossible to construct a BQM " + '*' * 25)
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

        # pprint(task_times)
        # pprint(disable_till)
        # pprint(disabled_variables)

        print(i)

        # improving original solution
        for job, times in task_times.items():
            for j in range(len(times)):
                if solution[job][operations_indexes[job][j]] != task_times[job][j] + i:
                    print('!' * 100)
                solution[job][operations_indexes[job][j]] = task_times[job][j] + i
        # pprint(solution)
    return solution
