import sys
from instance_parser import *
from partial_brute_force import solve_with_pbruteforce
from warnings import filterwarnings

filterwarnings("ignore")

jobs = readInstance(sys.argv[1])
initial_solution = solve_greedily(jobs)

for current_result, _ in solve_with_pbruteforce(jobs, initial_solution):
    print(f"Current_result: {current_result}")
