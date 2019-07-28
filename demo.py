from __future__ import print_function

from dwave.system.composites import EmbeddingComposite
from dwave.system.samplers import DWaveSampler

from job_shop_scheduler import get_jss_bqm

# Construct a BQM for the jobs
jobs = {"cupcakes": [("CPU1", 2), ("CPU1", 1)],
        "smoothie": [("CPU1", 1)],
        "lasagna": [("CPU1", 2)]}
max_time = 6	  # Upperbound on how long the schedule can be; 4 is arbitrary
num_of_machines = 2
bqm = get_jss_bqm(jobs, num_of_machines, max_time)

# Submit BQM
# Note: may need to tweak the chain strength and the number of reads
sampler = EmbeddingComposite(DWaveSampler(solver={'qpu':True}))
sampleset = sampler.sample(bqm, chain_strength=2, num_reads=1000)

# Grab solution
solution = sampleset.first.sample

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

print(solution)