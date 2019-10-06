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


def find_time_window(jobs: dict, solution: dict, start: int, end: int):
    new_jobs = defaultdict(list)
    disabled_times = defaultdict(list)
    disabled_variables = []
    for job_name, start_times in solution.items():
        for i, start_time in enumerate(start_times):
            if(start_time >= start and start_time + jobs[job_name][i][1] <= end):
                # an operation fits into the time window
                new_jobs[job_name].append(jobs[job_name][i])

            elif (start <= start_time < end and start_time + jobs[job_name][i][1] > end):
                # an operation reaches out of the time window from right side
                if i > 0:
                    for x in range(start_time-jobs[job_name][i-1][1] + 1, end):
                        disabled_variables.append(get_label(Task(job_name, i-1, jobs[job_name][i-1][0], jobs[job_name][i-1][1]), x))
                disabled_times[job_name].append((start_time, end))

            elif (start_time < start and start <= start_time + jobs[job_name][i][1] <= end):
                # an operation reaches out of the time window from left side
                if i < len(jobs[job_name]) - 1:
                    for x in range(start, start_time + jobs[job_name][i][1]):
                        disabled_variables.append(get_label(Task(job_name, i+1, jobs[job_name][i+1][0], jobs[job_name][i+1][1]), x))
                disabled_times[job_name].append((start, start_time + jobs[job_name][i][1]))

            # If an operation reaches out of the time window from both sides,
            # do nothing, it's not going to be a problem

    return new_jobs, disabled_times, disabled_variables


def checkValidity(jobs: dict, solution: dict) -> bool:
    # checking if every operation ends before next one starts
    for key, value in solution.items():
        for i, start_time in enumerate(value):
            if(i < len(value)-1 and start_time + jobs[key][i][1] > solution[key][i+1]):
                return False
    return True
