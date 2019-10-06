from pprint import pprint
from random import randrange

from instance_parser import readInstance, transformToMachineDict

from copy import deepcopy

jobs = readInstance("/Users/mareksubocz/Downloads/ft06.txt")

pprint(jobs)

jobs_solution = deepcopy(jobs)

for key, value in jobs.items():
    for i in range(len(value)):
        jobs_solution[key][i] = randrange(0, 10)

pprint(jobs_solution)
pprint(jobs)
pprint(transformToMachineDict(jobs, jobs_solution))
