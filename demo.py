import sys
from instance_parser import readInstance, squash_lengths, solve_greedily,\
get_order, get_result, solve_with_order
from partial_brute_force import solve_with_pbruteforce
from warnings import filterwarnings

filterwarnings("ignore")

jobs = readInstance(sys.argv[1])
initial_solution = solve_greedily(jobs)
print(f"Initial (greedy) solution result: {get_result(jobs, initial_solution)}")
print("Squashing jobs' length to 3 categories...")
squashed_jobs = squash_lengths(jobs)

print("Performing the algorithm...")

for current_result, _ in solve_with_pbruteforce(squashed_jobs,
                                                initial_solution,
                                                window_size=5,
                                                qpu=False):
    print(f"Current_result: {get_result(squashed_jobs, current_result)}")

order = get_order(current_result)
# Using the order of new solution to solve the problem with full-time jobs

print("Streching jobs to full length...")
print("final result: ", get_result(jobs, solve_with_order(jobs, order)))
