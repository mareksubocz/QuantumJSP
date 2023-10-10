# from solution import Solution
from partial_brute_force import solve_with_pbruteforce_new
import sys
from instance import Instance
from utilities import draw_solution


def main(path, squashing=False):
    instance = Instance(path=path)
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

    draw_solution(instance, initial_solution, x_max=record)

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

    draw_solution(instance, proper_solution, x_max=proper_solution.get_result())

    print('proper result:', proper_solution.get_result())
    print('proper valid:', proper_solution.is_valid())
    # proper_solution.visualize()

if __name__ == '__main__':
    main(sys.argv[1])
