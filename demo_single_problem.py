# Copyright 2019 D-Wave Systems Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
from utilities import draw_solution
from instance_parser import checkValidity, get_result, readInstance

from dwave.system.composites import EmbeddingComposite
from dwave.system.samplers import DWaveSampler
from dwave.system import LeapHybridDQMSampler
from greedy import SteepestDescentSolver
from time import time

from job_shop_scheduler import get_jss_dqm
import tabu

import pandas as pd
from itertools import product

# Construct a BQM for the jobs
# jobs = {"cupcakes": [("mixer", 2), ("oven", 1)],
#         "smoothie": [("mixer", 1), ("oven", 1)],
#         "lasagna": [("oven", 2), ("mixer", 1)]}
full = 1
max_time=680
time_limit=1
results = []
reads = []
for max_time, time_limit in product([680], [60]):
    print(f'-------Max time: {max_time}, time limit: {time_limit}-------')
    for ifull in range(full):
        start = time()
        jobs = readInstance(sys.argv[1])
        dqm = get_jss_dqm(jobs, max_time=max_time)

        qpu = True
        # if not qpu:
            # sampler = tabu.TabuSampler()
        # else:
        sampler = LeapHybridDQMSampler()
        sampleset = sampler.sample_dqm(dqm, time_limit=time_limit,
                                       label=f'JSP tl:{time_limit}, max:{max_time} {ifull}.')
        # post processing
        pp_solver = SteepestDescentSolver()
        sampleset = pp_solver.sample(dqm, initial_states=sampleset)

        # Grab solution
        solution = sampleset.first.sample

        # # Parse node information
        result = {i: [-1]*len(jobs[i]) for i in jobs.keys()}

        for name, value in solution.items():
            job_name, task_index = name.rsplit("_", 1)
            result[int(job_name)][int(task_index)] = value
        if get_result(jobs, result) == 55 and checkValidity(jobs, result):
            if result not in results:
                results.append(result.items())
                draw_solution(jobs, result)
                print(f'!{len(results)}!', end='')

        end = time()
        reads.append([
            'Advantage',
            max_time,
            time_limit,
            get_result(jobs, result),
            checkValidity(jobs, result)
        ])
        reads_df = pd.DataFrame(reads, columns=['machine', 'max_time', 'time_limit',
                                                'result', 'valid'])
        reads_df.to_csv('reads_long2.csv', index=False)
        # print('max_time:', min_time)
        # print('time:', end-start)
        print(f'{ifull}/{full}:', get_result(jobs, result), end=', ')
        # draw_solution(jobs, result)
        print('valid:', checkValidity(jobs, result))

print('number of results:', len(results))
print(results)

# # Print problem and restructured solution
# print("Jobs and their machine-specific tasks:")
# for job, task_list in jobs.items():
#     print("{0:9}: {1}".format(job, task_list))

# print("\nJobs and the start times of each task:")
# for job, times in task_times.items():
#     print("{0:9}: {1}".format(job, times))
# print("Solution's energy:", sampleset.first.energy)
