import sys
from instance_parser import readInstance, solve_greedily
from partial_brute_force import solve_with_pbruteforce
from charts import num_of_errors_in_chain_strengths, num_of_errors_in_min_gap

jobs = readInstance(sys.argv[1])
initial_solution = solve_greedily(jobs)

for current_result, _ in solve_with_pbruteforce(jobs, initial_solution, lagrange_one_hot=1, lagrange_precedence=2, lagrange_share=2, times=1):
    print(f"Current_result: {get_result(jobs, current_result)}")
# import sys
# num_of_errors_in_min_gap(qpu=True, start = float(sys.argv[1]))
