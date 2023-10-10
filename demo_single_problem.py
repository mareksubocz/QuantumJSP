from instance import Instance
from stats import Statistics
from tqdm import tqdm
from collections import defaultdict
import sys

def main(filepath, mode='discrete'):
    instance = Instance(path=filepath, max_time=60)
    print("number of jobs:", instance.n_jobs)
    print("number of machines:", instance.n_machines)
    print("max time value:", instance.max_time)

    results = []
    instances = defaultdict(int)
    # for i in tqdm(range(100)):
    solution = instance.solve(mode=mode,
                              postprocessing=False,
                              statistics=True,
                              is_squashed=False,
                              heuristic=False,
                              num_reads=1000)
    instance.recent_statistics.save_to_csv('proba.csv')
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

    solution.visualize(mode="plotly")
    solution.visualize(mode="matplotlib")

if __name__ == '__main__':
    main(sys.argv[1])
