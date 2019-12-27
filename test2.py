from __future__ import print_function

import matplotlib.pyplot as plt
import time
import neal

from dwave.system.composites import EmbeddingComposite
from dwave.system.samplers import DWaveSampler

from job_shop_scheduler import get_jss_bqm

from instance_parser import readInstance, transformToMachineDict, find_time_window, solve_greedily

from collections import defaultdict

from pprint import pprint

from utilities import draw_solution

jobs = {1: [(2, 1), (0, 1), (1, 2), (3, 3), (5, 1), (4, 2)],
        2: [(1, 3), (2, 2), (4, 3), (5, 3), (0, 3), (3, 2)],
        3: [(2, 2), (3, 2), (5, 3), (0, 3), (1, 1), (4, 3)],
        4: [(1, 2), (0, 2), (2, 2), (3, 1), (4, 3), (5, 3)],
        5: [(2, 3), (1, 1), (4, 2), (5, 2), (0, 1), (3, 1)],
        6: [(1, 1), (3, 1), (5, 3), (0, 3), (4, 2), (2, 1)]}

solutions = []

for solution in solutions:
    draw_solution(jobs, solution)
