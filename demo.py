import sys
from instance_parser import *
from partial_brute_force import solve_with_pbruteforce

jobs = readInstance(sys.argv[1])
initial_solution = solve_greedily(jobs)

for current_result, _ in solve_with_pbruteforce(jobs, initial_solution, lagrange_one_hot=1, lagrange_precedence=2, lagrange_share=2, times=1):
    print(f"Current_result: {get_result(jobs, current_result)}")
