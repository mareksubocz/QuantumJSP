from __future__ import print_function

import tabu

from dwave.system.composites import EmbeddingComposite
from dwave.system.samplers import DWaveSampler
from dwavebinarycsp.exceptions import ImpossibleBQM

from job_shop_scheduler import get_jss_bqm

from instance_parser import *

from pprint import pprint

from copy import deepcopy


def solve_with_pbruteforce(jobs, solution, qpu=False, num_reads=2000, max_time=None, window_size=5, chain_strength=2, times=10, lagrange_one_hot=1, lagrange_precedence=1, lagrange_share=1):
    if max_time is None:
        max_time = get_result(jobs, solution) + 3
    for iteration_number in range(times):
        print(iteration_number)
        try:
            if qpu:
                sampler = EmbeddingComposite(
                    DWaveSampler(solver={'qpu': True}))
            else:
                sampler = tabu.TabuSampler()

            bqm = get_jss_bqm(jobs, window_size + 1, lagrange_one_hot=lagrange_one_hot, lagrange_precedence=lagrange_precedence, lagrange_share=lagrange_share)
            
            # Check elements in the BQM
            for q in bqm.linear:
                if bqm.linear[q] != -1:
                    print(q)
            for q in bqm.quadratic:
                if bqm.quadratic[q] != 2:
                    print(q, bqm.quadratic[q])

            # Run BQM and get the solution and the energy
            sampleset = sampler.sample(bqm)
            solution1 = sampleset.first.sample
            energy1 = sampleset.first.energy

            # Determine which nodes are involved
            selected_nodes = [k for k, v in solution1.items() if v == 1 and not k.startswith('aux')]
            print(selected_nodes, ' Energy ', energy1)

            # Compute the task times
            task_times = {k: [-1] * len(v) for k, v in jobs.items()}
            for node in selected_nodes:
                job_name, task_time = node.rsplit("_", 1)
                task_index, start_time = map(int, task_time.split(","))
                task_times[int(job_name)][task_index] = start_time
            print(' Task times ',task_times)
 
            i = 0
            sol_found = deepcopy(solution)
            # TODO: make the "improving original solution" loop work
            # Original solution is "greedy," and then we provide the
            # found solution. When I try this loop, the indexes list
            # seems too short.
            info = find_time_window(jobs, solution, i, i + window_size)
            new_jobs, indexes, disable_till, disable_since, disabled_variables = info
            #print(' New jobs ',new_jobs)
            #print(' Indexes ',indexes)
            #for job, times in task_times.items():
            #    for j in range(len(times)):
            #        print(' Job ',job, ' Times ',times, ' j ',j)
            #         sol_found[job][indexes[job][j]
            #                       ] = task_times[job][j] + i
            #print(sol_found)

            # TODO: learn how to check the solution. Not sure what the
            # input needs to look like
            #if checkValidity(jobs, sol_found):

            #return the solution
            # yield solution, i

            for job, times in task_times.items():
                for j in range(len(indexes[job])):
                    print('^' * 50)
                    print(task_times)
                    print(sol_found)
                    print(indexes)
                    print('v' * 50)
                    sol_found[job][indexes[job][j]] = task_times[job][j] + i

            if checkValidity(jobs, sol_found):
                solution = sol_found
                yield solution, i

            #for i in range(max_time - window_size):
            #    info = find_time_window(jobs, solution, i, i + window_size)
            #    new_jobs, indexes, disable_till, disable_since, disabled_variables = info

            #    if not bool(new_jobs):  # if new_jobs dict is empty
            #        continue

            #    try:
            #        bqm = get_jss_bqm(new_jobs, window_size + 1, disable_till, disable_since,
            #                          disabled_variables, stitch_kwargs={'min_classical_gap': 2})
            #    except ImpossibleBQM:
            #        print('*' * 25 + " It's impossible to construct a BQM " + '*' * 25)
            #        continue

            #    if qpu:
            #        sampleset = sampler.sample(
            #            bqm, chain_strength=chain_strength, num_reads=num_reads)
            #    else:
            #        sampleset = sampler.sample(bqm, num_reads=num_reads)

            #    solution1 = sampleset.first.sample
            #    selected_nodes = [k for k, v in solution1.items() if v ==
            #                      1 and not k.startswith('aux')]
            #    # Parse node information
            #    task_times = {k: [-1] * len(v) for k, v in new_jobs.items()}
            #    for node in selected_nodes:
            #        job_name, task_time = node.rsplit("_", 1)
            #        task_index, start_time = map(int, task_time.split(","))

            #        task_times[int(job_name)][task_index] = start_time

            #    # improving original solution
            #    sol_found = deepcopy(solution)
            #    for job, times in task_times.items():
            #        for j in range(len(times)):
            #            sol_found[job][indexes[job][j]
            #                           ] = task_times[job][j] + i
            #    if checkValidity(jobs, sol_found):
            #        solution = sol_found
            #        yield solution, i  # solution and place in frame
        except Exception as e:
            # uncomment this if you want to apply some behaviuor when exception occurs
            # yield 'ex', 'ex'
            print(e)
            continue
