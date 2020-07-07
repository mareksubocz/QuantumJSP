# from __future__ import print_function
from instance_parser import *
from copy import deepcopy


def brute_force_greedy(jobs, solution, qpu=False, num_reads=2000, max_time=None, window_size=5, chain_strength=2, times=20):
    if max_time is None:
        max_time = get_result(jobs, solution) + 3
    for iteration_number in range(times):
        print(iteration_number)
        for i in range(max_time - window_size):
            info = find_time_window(jobs, solution, i, i + window_size)
            new_jobs, indexes, disable_till, disable_since, disabled_variables = info

            if not bool(new_jobs):  # if new_jobs dict is empty
                continue

            task_times = solve_greedily(new_jobs)
            for i in range(10):
                new_task_times = solve_greedily(new_jobs)
                if get_result(new_jobs, new_task_times) < get_result(new_jobs, task_times):
                    task_times = deepcopy(new_task_times)

            # improving original solution
            sol_found = deepcopy(solution)
            for job, times in task_times.items():
                for j in range(len(times)):
                    if sol_found[job][indexes[job][j]] != task_times[job][j] + i:
                        sol_found[job][indexes[job][j]
                                       ] = task_times[job][j] + i
            if checkValidity(jobs, sol_found):
                solution = sol_found
                yield solution, i  # solution and which timepoint the frame starts on
