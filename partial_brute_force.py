import tabu

from dwave.system.composites import EmbeddingComposite
from dwave.system.samplers import DWaveSampler
from dwavebinarycsp.exceptions import ImpossibleBQM

from job_shop_scheduler import get_jss_bqm

from instance_parser import *

from pprint import pprint

from copy import deepcopy

def solve_with_pbruteforce(jobs, solution, qpu=False, num_reads=2000,
                           max_time=None, window_size=5, chain_strength=2,
                           num_of_iterations=10, min_classical_gap=2,
                           lagrange_one_hot=1, lagrange_precedence=1,
                           lagrange_share=1):

    # default, safe value of max_time to give some room for improvement
    if max_time is None:
        max_time = get_result(jobs, solution) + 3

    # main loop, iterates over whole instance
    for iteration_number in range(num_of_iterations):
        print('-'*10, f"iteration {iteration_number+1}/{num_of_iterations}",'-'*10)
        try:
            if qpu:
                sampler = EmbeddingComposite(DWaveSampler())
            else:
                sampler = tabu.TabuSampler()

            # looping over parts of the instance, solving small sub-instances
            # of size window_size
            from random import sample
            for i in sample(range(max_time - window_size), len(range(max_time -
                                                                     window_size))):

                # cutting out the sub-instance
                info = find_time_window(jobs, solution, i, i + window_size)

                # new_jobs - tasks present in the sub-instance
                # indexes - old (full-instance) indexes of tasks in new_jobs
                # disable_till, disable_since and disabled_variables are all
                # explained in instance_parser.py
                new_jobs, indexes, disable_till, disable_since, disabled_variables = info

                if not bool(new_jobs):  # if sub-instance is empty
                    continue

                # constructing Binary Quadratic Model
                try:
                    bqm = get_jss_bqm(new_jobs, window_size + 1, disable_till, disable_since,
                                      disabled_variables, lagrange_one_hot,
                                      lagrange_precedence, lagrange_share)
                except ImpossibleBQM:
                    print('*' * 25 + " It's impossible to construct a BQM " + '*' * 25)
                    continue

                # reding num_reads responses from the sampler
                sampleset = sampler.sample(bqm, chain_strength=chain_strength,
                                           num_reads=num_reads)

                # using the best (lowest energy) sample 
                solution1 = sampleset.first.sample

                # variables that were selected by the sampler
                # (apart from the auxiliary variables)
                selected_nodes = [k for k, v in solution1.items() if v ==
                                  1 and not k.startswith('aux')]

                # parsing aquired information
                task_times = {k: [-1] * len(v) for k, v in new_jobs.items()}
                for node in selected_nodes:
                    job_name, task_time = node.rsplit("_", 1)
                    task_index, start_time = map(int, task_time.split(","))
                    task_times[int(job_name)][task_index] = start_time

                # constructing a new solution, improved by the aquired info
                # newly scheduled tasks are injected into a full instance
                sol_found = deepcopy(solution)
                for job, times in task_times.items():
                    for j in range(len(times)):
                        sol_found[job][indexes[job][j]] = task_times[job][j] + i

                # checking if the new, improved solution is valid
                if checkValidity(jobs, sol_found):
                    solution = deepcopy(sol_found)
                    # solution = sol_found
                    yield solution, i  # solution and current position of window

        except Exception as e:
            # uncomment this if you want to apply some behaviuor 
            # in demo.py when exception occurs:
            # yield 'ex', 'ex'
            print(e)
            continue
