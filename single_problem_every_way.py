from instance import Instance
from stats import Statistics
from tqdm import tqdm
from collections import defaultdict
from random import randint, choice
from pathlib import Path
import sys

def main():
    filepath = choice(list(map(str, Path('./data').glob('*'))))
    print('instance:', filepath)
    instance = Instance(path=filepath)
    instance.max_time = instance.optimal + randint(0, 20)
    print("number of jobs:", instance.n_jobs)
    print("number of machines:", instance.n_machines)
    print("max time value:", instance.max_time)

    results = []
    instances = defaultdict(int)
    # for i in tqdm(range(100)):
    mode = choice(['csp', 'pyqubo', 'sim_pyqubo', 'discrete'])
    solution = instance.solve(mode=mode,
                              postprocessing=False,
                              statistics=True,
                              is_squashed=False,
                              heuristic=False,
                              num_reads=choice([100, 1000, 10000, 20000]))
    instance.recent_statistics.save_to_csv('single_problem.csv')
    # if solution.is_valid():
    #   results.append(solution.get_result())
    #   instances[solution.get_result()+'_'+str(solution)] += 1
    # else:
    #   results.append(-1)
    print('solution:\n', solution)
    print("solution is valid:", solution.is_valid())
    print("solution result:", solution.get_result())
    # print('num_feasible:',instance.recent_statistics.num_feasible)
    # instance.recent_statistics.results_histogram()
    # instance.recent_statistics.energies_histogram()
    # instance.recent_statistics.save_to_csv('JSP_data_2.csv')

    # solution.visualize(mode="plotly")
    # solution.visualize(mode="matplotlib")

if __name__ == '__main__':
    for _ in range(10000):
        main()
