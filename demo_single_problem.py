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

from __future__ import print_function

from dwave.system.composites import EmbeddingComposite
from dwave.system.samplers import DWaveSampler
from dwave.system import LeapHybridDQMSampler

from job_shop_scheduler import get_jss_dqm
import tabu

# Construct a BQM for the jobs
jobs = {"cupcakes": [("mixer", 2), ("oven", 1)],
        "smoothie": [("mixer", 1)],
        "lasagna": [("oven", 2)]}
max_time = 4	  # Upperbound on how long the schedule can be; 4 is arbitrary
dqm = get_jss_dqm(jobs, max_time)
print(dqm)

qpu = True
# Submit BQM
# Note: may need to tweak the chain strength and the number of reads
if not qpu:
    sampler = tabu.TabuSampler()
else:
    sampler = LeapHybridDQMSampler()
sampleset = sampler.sample_dqm(dqm)

# Grab solution
solution = sampleset.first.sample
print(solution)

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
#
#  Hence, we are grabbing the nodes selected by our solver (i.e. nodes flagged
#  with 1s) that will make a good schedule.
#  (see next line of code, 'selected_nodes')
#
# Note2: if a start_time_for_task == -1, it means that the solution is invalid

# Grab selected nodes
selected_nodes = [k for k, v in solution.items() if v == 1]

# Parse node information
task_times = {k: [-1]*len(v) for k, v in jobs.items()}
for node in selected_nodes:
    job_name, task_time = node.rsplit("_", 1)
    task_index, start_time = map(int, task_time.split(","))

    task_times[job_name][task_index] = start_time

# Print problem and restructured solution
print("Jobs and their machine-specific tasks:")
for job, task_list in jobs.items():
    print("{0:9}: {1}".format(job, task_list))

print("\nJobs and the start times of each task:")
for job, times in task_times.items():
    print("{0:9}: {1}".format(job, times))
print("Solution's energy:", sampleset.first.energy)
