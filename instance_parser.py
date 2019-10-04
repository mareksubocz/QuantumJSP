from bisect import insort
from collections import defaultdict


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
    machine_dict = defaultdict(list)
    for key, value in solution.items():
        for i in len(value):
            machine_dict[jobs[key][i][0]].insort((value[i], jobs[key][i][1]))


def checkValidity(jobs: dict, solution: dict) -> bool:
    # checking if every operation ends before next one starts
    for key, value in solution.items():
        for i, start_time in enumerate(value):
            if(i < len(value)-1 and start_time + jobs[key][i][1] > solution[key][i+1]):
                return False
    return True
