from bisect import insort

from collections import defaultdict

from job_shop_scheduler import get_label, Task


def readInstance(path: str) -> dict:
    job_dict = defaultdict(list)
    with open(path) as f:
        f.readline()
        for i, line in enumerate(f):
            lint = list(map(int, line.split()))
            job_dict[i+1] = [x for x in
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
            machine_dict[jobs[key][i][0]].append((value[i], jobs[key][i][1]))
    return machine_dict


# FIXME: zmien sposob ograniczania startów operacji w tych samych jobach
def find_time_window(jobs: dict, solution: dict, start: int, end: int):
    new_jobs = defaultdict(list)
    operations_indexes = defaultdict(list)
    disable_till = {}
    disabled_variables = []
    for job_name, start_times in solution.items():
        for i, start_time in enumerate(start_times):

            machine = jobs[job_name][i][0]
            end_time = start_time + jobs[job_name][i][1]

            if start_time >= start and end_time <= end:
                # an operation fits into the time window
                new_jobs[job_name].append(jobs[job_name][i])
                operations_indexes[job_name].append(i)

            # MAYBE we don't need to check this one, as it will
            # sort itself out later on

            # elif (start <= start_time < end and start_time + jobs[job_name][i][1] > end):
            #     # an operation reaches out of the time window from right side
            #     if i > 0:
            #         for x in range(start_time-jobs[job_name][i-1][1] + 1, end):
            #             disabled_variables.append(get_label(Task(job_name, i-1, jobs[job_name][i-1][0], jobs[job_name][i-1][1]), x - start))
            #     disabled_times[jobs[job_name][i][0]].append((start_time - start, end - start))

            elif (start_time < start and start < end_time <= end):
                # an operation reaches out of the time window from the left side
                if i < len(start_times) - 1:
                    for x in range(end_time - start):
                        disabled_variables.append(get_label(Task(
                            job_name, 0, jobs[job_name][i+1][0], jobs[job_name][i+1][1]), x))
                if machine in disable_till.keys():
                    disable_till[machine] = max(disable_till[machine], end_time - start)
                else:
                    disable_till[machine] = end_time - start

            # If an operation reaches out of the time window from both sides,
            # do nothing, it's not going to be a problem

    return new_jobs, operations_indexes, disable_till, disabled_variables


def solve_greedily(jobs: dict, max_time):
    free_space = {}
    solution = defaultdict(list)
    max_num_of_operations = 0
    for _, operations in jobs.items():
        if(len(operations) > max_num_of_operations):
            max_num_of_operations = len(operations)
        for machine, _ in operations:
            free_space[machine] = [(0, max_time)]

    for i in range(max_num_of_operations):
        for name, operations in jobs.items():
            if i >= len(operations):
                continue
            machine, length = jobs[name][i]
            for j, space in enumerate(free_space[machine]):
                if i == 0 and space[1] - space[0] >= length:
                    solution[name].append(space[0])
                    free_space[machine][j] = (space[0] + length, space[1])
                    break
                elif i > 0 and space[1] - max(space[0], solution[name][i-1] + jobs[name][i-1][1]) >= length:
                    startpoint = max(space[0], solution[name][i-1] + jobs[name][i-1][1])
                    solution[name].append(startpoint)
                    new_space_1 = (space[0], startpoint)
                    new_space_2 = (startpoint + length, space[1])
                    free_space[machine].pop(j)
                    free_space[machine].insert(j, new_space_2)
                    free_space[machine].insert(j, new_space_1)
                    break
    return solution


def checkValidity(jobs: dict, solution: dict) -> bool:
    # checking if every operation ends before next one starts
    for key, value in solution.items():
        for i, start_time in enumerate(value):
            if(i < len(value)-1 and start_time + jobs[key][i][1] > solution[key][i+1]):
                return False
    return True


def get_result(jobs, solution):
    max_time = 0
    for job in jobs:
        max_time = max(max_time, solution[job][-1] + job[-1][1])
    return max_time
