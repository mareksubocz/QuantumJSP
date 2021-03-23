import sys
from instance_parser import readInstance, squash_lengths, solve_greedily,\
get_order, get_result, solve_with_order
from utilities import draw_solution
from partial_brute_force import solve_with_pbruteforce
from warnings import filterwarnings

# if you see some excessive warnings from dwave
# filterwarnings("ignore")

jobs = readInstance(sys.argv[1])

first_solution = solve_greedily(jobs)
first_result = get_result(jobs, first_solution)
print(f"Result without squashing: {first_result}")

# job squashing
squashed_jobs = squash_lengths(jobs)

# uncomment to skip job squashing
# squashed_jobs = jobs

order = get_order(first_solution)
initial_solution = solve_with_order(squashed_jobs, order)

# uncomment if you want to leave space between operations at the start
initial_solution = first_solution

initial_result = get_result(squashed_jobs, initial_solution)
print(f"Initial (greedy) solution result: {initial_result}")
draw_solution(squashed_jobs, initial_solution, x_max=initial_result)

print("Performing the algorithm...")

# main loop
last_result = initial_result
current_solution = {}
for current_solution, _ in solve_with_pbruteforce(squashed_jobs,
                                                  initial_solution,
                                                  window_size=initial_result,
                                                  qpu=True,
                                                  lagrange_one_hot=1,
                                                  lagrange_precedence=2,
                                                  lagrange_share=2,
                                                  num_of_iterations=1):
    current_result = get_result(squashed_jobs, current_solution)

    if current_result < last_result:
        last_result = current_result
        draw_solution(squashed_jobs, current_solution, x_max=initial_result)

    print(f"Current_result: {get_result(squashed_jobs, current_solution)}")

# Using the order of new solution to solve the problem with full-time jobs
order = get_order(current_solution)
print("Streching jobs to full length...")
print("final result: ", get_result(jobs, solve_with_order(jobs, order)))
