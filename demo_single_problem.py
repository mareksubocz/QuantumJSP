from instance import InstanceNew
from stats import Statistics
import sys

instance = InstanceNew(path=sys.argv[1])
print("number of jobs:", instance.n_jobs)
print("number of machines:", instance.n_machines)
print("max time value:", instance.max_time)

solution = instance.solve(mode="discrete",
                          postprocessing=False,
                          statistics=True,
                          is_squashed=False,
                          heuristic=False,
                          optimal=7,
                          num_reads=10000)
print('solution:\n', solution)
print("solution is valid:", solution.is_valid())
print("solution result:", solution.get_result())
print('num_feasible:',instance.recent_statistics.num_feasible)
# instance.recent_statistics.results_histogram()
# instance.recent_statistics.energies_histogram()
instance.recent_statistics.save_to_csv('JSP_data_2.csv')

# solution.visualize(mode="plotly")
# solution.visualize(mode="matplotlib")
