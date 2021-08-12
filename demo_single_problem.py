from dwave.system.composites import EmbeddingComposite
from dwave.system.samplers import DWaveSampler
from dwave.system import LeapHybridDQMSampler
from greedy import SteepestDescentSolver
from instance_parser import readInstance
import pandas as pd
import matplotlib.pyplot as plt
import sys
from utilities import draw_solution

from job_shop_scheduler import get_jss_bqm
import tabu

# Construct a BQM for the jobs
# jobs = {"cupcakes": [("mixer", 2), ("oven", 1)],
#         "smoothie": [("mixer", 1), ("oven", 1)],
#         "lasagna": [("oven", 2), ("mixer", 1)]
jobs = readInstance(sys.argv[1])
max_time = 12	  # Upperbound on how long the schedule can be; 4 is arbitrary
bqm = get_jss_bqm(jobs, max_time)
# print(bqm)

qpu = True
# Submit BQM
# Note: may need to tweak the chain strength and the number of reads
if not qpu:
    sampler = tabu.TabuSampler()
else:
    sampler = EmbeddingComposite(DWaveSampler())
sampleset = sampler.sample(bqm, num_reads=1000)
print(sampleset)
# post processing
solver_greedy = SteepestDescentSolver()
sampleset_pp = solver_greedy.sample_qubo(bqm.to_qubo()[0], initial_states=sampleset)

plt.plot(list(range(len(sampleset))), sampleset.record.energy, 'b.-',
                           sampleset_pp.record.energy, 'r^-')
plt.legend(['QPU samples', 'Postprocessed Samples'])
plt.xlabel("Sample")
plt.ylabel("Energy")
plt.show()
# Grab solution
# solution = sampleset_pp.first.sample
# print(solution)
# for sol in sampleset.samples():
#     print(sol.num_occurences)

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
solution = sampleset.first.sample
selected_nodes = [k for k, v in solution.items() if v == 1]

# Parse node information
task_times = {k: [-1]*len(v) for k, v in jobs.items()}
for node in selected_nodes:
    job_name, task_time = node.rsplit("_", 1)
    task_index, start_time = map(int, task_time.split(","))

    task_times[int(job_name)][task_index] = start_time

# Print problem and restructured solution
print("Jobs and their machine-specific tasks:")
for job, task_list in jobs.items():
    print("{0:9}: {1}".format(job, task_list))

print("\nJobs and the start times of each task:")
for job, times in task_times.items():
    print("{0:9}: {1}".format(job, times))
print("Solution's energy:", sampleset.first.energy)


draw_solution(jobs, task_times)

solution = sampleset_pp.first.sample
selected_nodes = [k for k, v in solution.items() if v == 1]

# Parse node information
task_times = {k: [-1]*len(v) for k, v in jobs.items()}
for node in selected_nodes:
    job_name, task_time = node.rsplit("_", 1)
    task_index, start_time = map(int, task_time.split(","))

    task_times[int(job_name)][task_index] = start_time

# Print problem and restructured solution
print("Jobs and their machine-specific tasks:")
for job, task_list in jobs.items():
    print("{0:9}: {1}".format(job, task_list))

print("\nJobs and the start times of each task:")
for job, times in task_times.items():
    print("{0:9}: {1}".format(job, times))
print("Solution's energy:", sampleset_pp.first.energy)


draw_solution(jobs, task_times)
