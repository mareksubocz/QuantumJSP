# from solution import Solution
from partial_brute_force import solve_with_pbruteforce_new
import sys
from instance import Instance


squashing = False
instance = Instance(path=sys.argv[1])
squashed_instance = instance.squash()
print("number of jobs:", instance.n_jobs)
print("number of machines:", instance.n_machines)
print("max time value:", instance.max_time)
if squashing:
    initial_solution = squashed_instance.solve("greedy")
else:
    initial_solution = instance.solve("greedy")
# initial_solution.visualize()
best_solution = initial_solution.copy()
record = initial_solution.get_result()

print('Initial result:', record)

for solution in solve_with_pbruteforce_new(instance,
                                           initial_solution,
                                           window_size=20,
                                           is_squashed=squashing,
                                           random=True):
    print('Current result:',solution.get_result())
    if solution.get_result() < record:
        # solution.visualize()
        best_solution = solution.copy()
        record = solution.get_result()

# Solution(squashed_instance, solution=best_solution).visualize()
proper_solution = instance.solve_with_order(best_solution)
print('proper result:', proper_solution.get_result())
print('proper valid:', proper_solution.is_valid())
# proper_solution.visualize()
