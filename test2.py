from instance_parser import readInstance, solve_worse, solve_greedily
from instance_parser import get_result, checkValidity, get_order, solve_with_order, squash_lengths
from partial_brute_force import solve_with_pbruteforce
from utilities import draw_solution
from pprint import pprint
from collections import defaultdict
from copy import deepcopy
import sys
from warnings import filterwarnings
from charts import partial_bruteforce_visualisation

filterwarnings("ignore")

# jobs_full_len = readInstance("data/ft06.txt")
jobs_full_len = readInstance(sys.argv[1])
partial_bruteforce_visualisation("ramki_poprawione", jobs_full_len)
