from collections import defaultdict

from job_shop_scheduler import get_label, Task

from pprint import pprint

from random import shuffle

from math import inf


def readInstance(path: str) -> dict:
    job_dict = defaultdict(list)
    with open(path) as f:
        f.readline()
        for i, line in enumerate(f):
            lint = list(map(int, line.split()))
            job_dict[i + 1] = [x for x in
                               zip(lint[::2],  # machines
                                   lint[1::2]  # operation lengths
                                   )]
        return job_dict


def transformToMachineDict(jobs: dict, solution: dict) -> dict:
    """Given a solution to a problem from the first argument,
    produces a dictionary indicating the work timeline for each machine.

    Args:
        jobs (dict): description of an instance
        solution (dict): solution to an instance:
        {"job_1": [start_time_of_operation_1, start_time of operation_2],
         "job_2": [start_time_of_operation_1, start_time of operation_2]}

    Returns:
        dict: [description]
    """
    machine_dict = defaultdict(list)
    for key, value in solution.items():
        for i in range(len(value)):
            machine_dict[jobs[key][i][0]].append(
                (key, value[i], jobs[key][i][1]))
    return machine_dict


def find_time_window(jobs: dict, solution: dict, start: int, end: int):
    new_jobs = defaultdict(list)
    operations_indexes = defaultdict(list)
    disable_till = defaultdict(int)
    disable_since = defaultdict(lambda: inf)
    disabled_variables = []
    for job_name, start_times in solution.items():
        for i, start_time in enumerate(start_times):

            machine = jobs[job_name][i][0]
            end_time = start_time + jobs[job_name][i][1]

            if start_time >= start and end_time <= end:
                # an operation fits into the time window
                new_jobs[job_name].append(jobs[job_name][i])
                operations_indexes[job_name].append(i)

            elif (start <= start_time < end and end_time > end):
                # an operation reaches out of the time window from right side
                if i > 0:
                    for x in range(start_time - jobs[job_name][i - 1][1] + 1, end):
                        disabled_variables.append(get_label(Task(
                            job_name, i - 1, jobs[job_name][i - 1][0], jobs[job_name][i - 1][1]), x - start))
                disable_since[machine] = min(
                    disable_since[machine], start_time - start)

            elif start_time < start and start < end_time <= end:
                # an operation reaches out of the time window from the left side
                if i < len(start_times) - 1:
                    for x in range(end_time - start):
                        disabled_variables.append(get_label(Task(
                            job_name, 0, jobs[job_name][i + 1][0], jobs[job_name][i + 1][1]), x))
                disable_till[machine] = max(
                    disable_till[machine], end_time - start)

            # If an operation reaches out of the time window from both sides,
            # do nothing, it's not going to be a problem

    return new_jobs, operations_indexes, disable_till, disable_since, disabled_variables


def solve_greedily(jobs: dict, max_time):
    free_space = {}
    solution = defaultdict(list)
    max_num_of_operations = 0
    for _, operations in jobs.items():
        if len(operations) > max_num_of_operations:
            max_num_of_operations = len(operations)
        for machine, _ in operations:
            free_space[machine] = [(0, max_time)]

    jobs_shuffled = list(jobs.items())
    shuffle(jobs_shuffled)

    for i in range(max_num_of_operations):
        for name, operations in jobs_shuffled:
            if i >= len(operations):
                continue
            machine, length = jobs[name][i]
            for j, space in enumerate(free_space[machine]):
                if i == 0 and space[1] - space[0] >= length:
                    solution[name].append(space[0])
                    free_space[machine][j] = (space[0] + length, space[1])
                    break
                elif i > 0 and space[1] - max(space[0], solution[name][i - 1] + jobs[name][i - 1][1]) >= length:
                    startpoint = max(
                        space[0], solution[name][i - 1] + jobs[name][i - 1][1])
                    solution[name].append(startpoint)
                    new_space_1 = (space[0], startpoint)
                    new_space_2 = (startpoint + length, space[1])
                    free_space[machine].pop(j)
                    free_space[machine].insert(j, new_space_2)
                    free_space[machine].insert(j, new_space_1)
                    break
    return solution


def solve_worse(jobs: dict, max_time):
    free_space = {}
    solution = defaultdict(list)
    for operations in jobs.values():
        for machine, _ in operations:
            free_space[machine] = [(0, max_time)]

    jobs_shuffled = list(jobs.items())
    shuffle(jobs_shuffled)

    for name, operations in jobs_shuffled:
        for i, (machine, length) in enumerate(operations):
            for j, (start, end) in enumerate(free_space[machine]):
                if i == 0 and end - start >= length:
                    solution[name].append(start)
                    free_space[machine][j] = (start + length, end)
                    break
                elif i > 0 and end - max(start, solution[name][i - 1] + jobs[name][i - 1][1]) >= length:
                    startpoint = max(
                        start, solution[name][i - 1] + jobs[name][i - 1][1])
                    solution[name].append(startpoint)
                    new_space_1 = (start, startpoint)
                    new_space_2 = (startpoint + length, end)
                    free_space[machine].pop(j)
                    free_space[machine].insert(j, new_space_2)
                    free_space[machine].insert(j, new_space_1)
                    break
    return solution


def solve_with_order(jobs, order):
    last_in_job = defaultdict(int)  # default jest 0
    last_in_machine = defaultdict(int)
    solution = defaultdict(list)
    for key, index in order:
        machine = jobs[key][index][0]
        length = jobs[key][index][1]

        start = max(last_in_job[key], last_in_machine[machine])

        solution[key].append(start)
        last_in_job[key] = last_in_machine[machine] = start + length
    return solution


def checkValidity(jobs: dict, solution: dict) -> bool:
    order = get_order(solution)
    solution_from_order = solve_with_order(jobs, order)
    order2 = get_order(solution_from_order)

    if order != order2:
        pprint(order)
        print('*' * 40)
        pprint(order2)

    return order == order2


def get_result(jobs, solution):
    max_time = 0
    for job, operations in jobs.items():
        max_time = max(max_time, solution[job][-1] + operations[-1][1])
    return max_time


def get_order(solution):
    order_dict = {}
    order = []
    for job, start_times in solution.items():
        for i, start_time in enumerate(start_times):
            order.append((start_time, (job, i)))
        # order.extend([(value[x], (key, x)) for x in range(len(value))])
    order.sort()
    order = [x[1] for x in order]
    return order


def get_order_numbered(solution):
    order_dict = {}
    order = []
    for i, (key, value) in enumerate(solution.items()):
        # returning one number per operation
        order.extend([(value[x], x * len(solution) + i + 1)
                      for x in range(len(value))])

    order.sort()
    order = [x[1] for x in order]
    return order


if __name__ == "__main__":
    jobs = readInstance("data/ft06.txt")
    for i in range(10000):
        solution = solve_greedily(jobs, 100)
        result = get_result(jobs, solution)
        if result < 59:
            print(result)
