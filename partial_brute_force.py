from solution import Solution
from instance import Instance
import tabu

from dwave.system.composites import EmbeddingComposite
from dwave.system import LeapHybridDQMSampler
from dwavebinarycsp.exceptions import ImpossibleBQM

from instance_parser import *

from pprint import pprint
from random import sample

from copy import deepcopy

def solve_with_pbruteforce_new(instance: Instance, solution: Solution,
                               num_of_iterations: int=2, window_size: int=5,
                               is_squashed=False, **kwargs):
    max_time = solution.get_result() + 2
    for i in range(num_of_iterations):
        print('-'*10, f"iteration {i+1}/{num_of_iterations}",'-'*10)
        for t in sample(range(max_time - window_size), len(range(max_time - window_size))):
            info = solution.cut_part_out(i, i+window_size)
            new_jobs, first_tasks, disable_till, disable_since, disabled_variables = info
            if not new_jobs: # if sub-instance is empty
                continue
            new_jobs = Instance(instance=new_jobs,
                                disable_till=disable_till,
                                disable_since=disable_since,
                                disabled_variables=disabled_variables)
            sub_solution = new_jobs.solve("discrete",
                                          statistics=True,
                                          heuristic=True,
                                          is_cut_out=True,
                                          window_size=window_size,
                                          window_start=t)
            new_jobs.recent_statistics.save_to_csv('JSP_data_3.csv')
            if 'random' in kwargs and kwargs['random']:
                worse_solution = new_jobs.solve("worse",
                               window_size=window_size,
                               window_start=t)
                with open('discreteVsrandom.csv', 'a') as file:
                    response = f"{sub_solution.get_result()},{sub_solution.is_valid()},{worse_solution.get_result()},{window_size}\n"
                    file.write(response)
                if not sub_solution.is_valid():
                    sub_solution.visualize()
                    worse_solution.visualize()
            if not sub_solution.is_valid():
                continue
            solution.put_part_in(sub_solution, first_tasks)
            yield solution



# def solve_with_pbruteforce(jobs, solution, qpu=True,
#                            max_time=None, window_size=5, time_limit=10,
#                            num_of_iterations=10,
#                            lagrange_one_hot=1, lagrange_precedence=1,
#                            lagrange_share=1):

#     # default, safe value of max_time to give some room for improvement
#     if max_time is None:
#         max_time = get_result(jobs, solution) + 3

#     # main loop, iterates over whole instance
#     for iteration_number in range(num_of_iterations):
#         print('-'*10, f"iteration {iteration_number+1}/{num_of_iterations}",'-'*10)
#         try:
#             if qpu:
#                 sampler = LeapHybridDQMSampler()
#             else:
#                 assert False, "can't do without the qpu"
#                 # sampler = tabu.TabuSampler()

#             # looping over parts of the instance, solving small sub-instances
#             # of size window_size
#             for i in sample(range(max_time - window_size), len(range(max_time -
#                                                                      window_size))):
#                 print('frame: ', i)

#                 # cutting out the sub-instance
#                 info = find_time_window(jobs, solution, i, i + window_size)

#                 # new_jobs - tasks present in the sub-instance
#                 # indexes - old (full-instance) indexes of tasks in new_jobs
#                 # disable_till, disable_since and disabled_variables are all
#                 # explained in instance_parser.py
#                 new_jobs, indexes, disable_till, disable_since, disabled_variables = info

#                 # FIXME: tak chyba nie może być
#                 disabled_variables = []

#                 if not bool(new_jobs):  # if sub-instance is empty
#                     continue

#                 # constructing Discrete Quadratic Model
#                 try:
#                     dqm = get_jss_dqm(new_jobs, window_size + 1, disable_till, disable_since,
#                                       disabled_variables, lagrange_one_hot,
#                                       lagrange_precedence, lagrange_share)
#                 except ImpossibleBQM:
#                     print('*' * 25 + " It's impossible to construct a DQM " + '*' * 25)
#                     continue

#                 # reding num_reads responses from the sampler
#                 # sampleset = sampler.sample_dqm(dqm, chain_strength=chain_strength,
#                 #                            num_reads=num_reads)
#                 sampleset = sampler.sample_dqm(dqm, time_limit=time_limit)

#                 # using the best (lowest energy) sample
#                 solution1 = sampleset.first.sample
#                 # print('solution: ', solution1)

#                 # variables that were selected by the sampler
#                 # (apart from the auxiliary variables)
#                 # selected_nodes = [k for k, v in solution1.items() if v ==
#                 #                   1 and not k.startswith('aux')]
#                 selected_nodes = [','.join((k, str(v))) for k, v in solution1.items()]

#                 # parsing aquired information
#                 task_times = {k: [-1] * len(v) for k, v in new_jobs.items()}
#                 for node in selected_nodes:
#                     job_name, task_time = node.rsplit("_", 1)
#                     task_index, start_time = map(int, task_time.split(","))
#                     task_times[int(job_name)][task_index] = start_time

#                 # constructing a new solution, improved by the aquired info
#                 # newly scheduled tasks are injected into a full instance
#                 sol_found = deepcopy(solution)
#                 for job, times in task_times.items():
#                     for j in range(len(times)):
#                         sol_found[job][indexes[job][j]] = task_times[job][j] + i

#                 # checking if the new, improved solution is valid
#                 if checkValidity(jobs, sol_found):
#                     print('git')
#                    # get_result(jobs, sol_found) <= max_time-3:
#                     solution = deepcopy(sol_found)
#                     # solution = sol_found
#                     yield solution, i  # solution and current position of window
#                 else:
#                     print('zepsute')

#         except Exception as e:
#             # uncomment this if you want to apply some behaviuor
#             # in demo.py when exception occurs:
#             # yield 'ex', 'ex'
#             print('error: ', e)
#             import traceback; print(traceback.print_exc())
#             continue
