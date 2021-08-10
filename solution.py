from dqm_scheduler import get_label, Task, get_jss_dqm
from csp_scheduler import get_jss_bqm as get_jss_csp
from pyqubo_scheduler import get_jss_bqm
from collections import defaultdict
from datetime import datetime
import plotly.express as px
from tabu import TabuSampler
import math

#TODO: użyj tego opisu jobs
"""Function checking if given solution fulfills all JSP constraints.

Args:
    jobs (dict): description of an instance
    {"job_1": [ (m1, l1), (m2, l2), (m3, l3), (m3, l3), ... ],
     "job_2": [ (m1, l1), (m2, l2), (m3, l3), (m3, l3), ... ],
     ...}
     where:
     - mx == machine of task x
     - lx == length of task x

    solution (dict): solution for an instance:
    {"job_1": [s1, s2, s3, ...],
     "job_2": [s1, s2, s3, ...],
     ...}
     where:
    - sx == start time of task x

Returns:
    bool: true - solution is valid
"""

class Instance(dict):
    def __init__(self,
                 path = '',
                 instance = {},
                 disable_since = None,
                 disable_till = None,
                 disabled_variables = None):

        assert path or instance, \
            'Provide path to instance or an already constructed instance.'

        if path:
            instance = self.read_file(path)
        super().__init__(instance)

        self.disable_since = disable_since
        self.disable_till = disable_till
        self.disabled_variables = disabled_variables

    def read_file(self, path: str) -> dict:
        job_dict = defaultdict(list)
        with open(path) as f:
            self.n_jobs, self.n_machines = list(map(int, f.readline().split()))
            for i, line in enumerate(f):
                lint = list(map(int, line.split()))
                job_dict[i + 1] = [x for x in
                                   zip(lint[::2],  # machines
                                       lint[1::2]  # operation lengths
                                       )]
            return job_dict

    def solve(self, max_time, mode='greedy'):
        available_modes = [
            'greedy',
            'worse',
            'csp',
            'discrete',
            'pyqubo',
            'sim_pyqubo',
        ]
        assert mode in available_modes, f'Choose one of: {available_modes}'

        #TODO: kontynuuj tutaj
        if mode == 'sim_pyqubo':
            bqm = get_jss_bqm(self, max_time)
            sampler = TabuSampler()
            sampleset = sampler.sample()
            solution = sampleset.first.sample

            selected_nodes = [k for k, v in solution.items() if v == 1]

            # Parse node information
            task_times = {k: [-1]*len(v) for k, v in self.items()}
            for node in selected_nodes:
                job_name, task_time = node.rsplit("_", 1)
                task_index, start_time = map(int, task_time.split(","))

                task_times[job_name][task_index] = start_time
            return Solution(self, solution=task_times)
        pass


class Solution(dict):
    def __init__(self, instance: Instance, solution = defaultdict(list)):
        super().__init__(solution)
        self.instance = instance

    def is_valid(self):
        # checking if order of operations in jobs is preserved
        for job, operations in self.instance.items():
            for i, (operation1, operation2) in enumerate(list(zip(operations[:-1], operations[1:]))):
                if self[job][i] + operation1[1] > self[job][i+1]:
                    return False

        machineDict = self.__transformToMachineDict()

        # checking if no operations using the same machine intersect
        for _, operations in machineDict.items():
            for i, operation1 in enumerate(operations):
                for j, operation2 in enumerate(operations):
                    if i == j:
                        continue
                    if not (operation1[1] + operation1[2] <= operation2[1] or # ends before
                            operation2[1] + operation2[2] <= operation1[1]):  # starts after
                        return False
        return True

    def __transformToMachineDict(self) -> dict:
        """Given a solution to a problem from the first argument,
        produces a dictionary indicating the work timeline for each machine.

        Args:
            jobs (dict): description of an instance

            solution (dict): solution to an instance:
            {"job_1": [start_time_of_operation_1, start_time_of_operation_2],
             "job_2": [start_time_of_operation_1, start_time_of_operation_2]}

        Returns:

            machineDict(dict):
            {"machine_1": [(job, time_of_operation_start, length), (..., ..., ...), ...],
             "machine_2:: [(..., ..., ...), ...], ...}
        """
        machine_dict = defaultdict(list)
        for key, value in self.items():
            for i in range(len(value)):
                machine_dict[self.instance[key][i][0]].append(
                    (key, value[i], self.instance[key][i][1]))
        return machine_dict

    def get_result(self) -> int:
        max_time = 0
        for job, operations in self.instance.items():
            max_time = max(max_time, self[job][-1] + int(operations[-1][1]))
        return max_time


    def get_order(self) -> list:
        order = []
        for job, start_times in self.items():
            for i, start_time in enumerate(start_times):
                order.append((start_time, (job, i)))
            # order.extend([(value[x], (key, x)) for x in range(len(value))])
        order.sort()
        res = [x[1] for x in order]
        return res

    def cut_part_out(self, start, end):
        pass

    def find_time_window(self, start: int, end: int):
        new_jobs = defaultdict(list)
        operations_indexes = defaultdict(list)

        # Those dictionaries indicate since or till when each machine should be unused,
        # because it is already taken by an operation that is happening during start
        # or end of time window. Therefore, you can't find them in jobs: dict
        # (instance dictionary), because they are removed from it.
        disable_till = defaultdict(int)
        disable_since = defaultdict(lambda: math.inf)

        # When an operation is scheduled during start or end of time window,
        # it's previous and subsequent operations are restricted to not last
        # after or before it (respectively).
        disabled_variables = []

        for job_name, start_times in self.items():
            for i, start_time in enumerate(start_times):

                machine = self.instance[job_name][i][0]
                end_time = start_time + self.instance[job_name][i][1]

                if start_time >= start and end_time <= end:
                    # an operation fits into the time window
                    new_jobs[job_name].append(self.instance[job_name][i])
                    operations_indexes[job_name].append(i)

                elif (start <= start_time < end and end_time > end):
                    # an operation reaches out of the time window from right side
                    if i > 0:
                        for x in range(start_time - self.instance[job_name][i - 1][1] + 1, end):
                            disabled_variables.append((get_label(Task(
                                job_name, i - 1, self.instance[job_name][i - 1][0],
                                self.instance[job_name][i - 1][1])), x - start))
                    disable_since[machine] = min(
                        disable_since[machine], start_time - start)

                elif start_time < start and start < end_time <= end:
                    # an operation reaches out of the time window from the left side
                    if i < len(start_times) - 1:
                        for x in range(end_time - start):
                            disabled_variables.append((get_label(Task(
                                job_name, 0, self.instance[job_name][i + 1][0],
                                self.instance[job_name][i + 1][1])), x))
                    disable_till[machine] = max(
                        disable_till[machine], end_time - start)

                # If an operation reaches out of the time window from both sides,
                # do nothing, it's not going to be a problem

        return new_jobs, operations_indexes, disable_till, disable_since, disabled_variables

    def visualize(self, mode='plotly', x_max=None):
        available_modes = ['plotly', 'matplotlib']
        assert mode in available_modes, f'Choose one of: {available_modes}'

        if mode == 'plotly':
            def convert_to_datetime(x):
                return datetime.fromtimestamp(31536000+x*24*3600).strftime("%Y-%m-%d")

            df = []
            if x_max is None:
                x_max = self.get_result()
            for job, tasks in self.items():
                for i, start in enumerate(tasks):
                    machine, length = self.instance[job][i]
                    df.append(dict(Machine=machine,
                                   Start=convert_to_datetime(start),
                                   Finish=convert_to_datetime(start+length),
                                   Job=str(job)))

            num_tick_labels = list(range(x_max+1))
            date_ticks = [convert_to_datetime(x) for x in num_tick_labels]

            fig = px.timeline(df, y="Machine", x_start="Start", x_end="Finish", color="Job")
            fig.update_traces(marker=dict(line=dict(width=3, color='black')), opacity=0.5)
            fig.layout.xaxis.update({
                'tickvals' : date_ticks,
                'ticktext' : num_tick_labels,
                'range' : [convert_to_datetime(0), convert_to_datetime(x_max)]
            })
            fig.update_yaxes(autorange="reversed") # otherwise tasks are listed from the bottom up
            fig.show()

        if mode == 'matplotlib':
            pass
            colors = ['red', 'green', 'yellow', 'blue', 'violet', 'orange']
            colorsHEX = ['#FF3333', '#79D279', '#FFFF66', '#80B3FF', '#C299FF', '#FFDAB3']
            from pathlib import Path
            import matplotlib.pyplot as plt
            import matplotlib.patches as mpatch
            import glob
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.set_aspect(aspect=1.5)
            rectangles = []
            machine_dict = self.__transformToMachineDict()
            for machine, operations in machine_dict.items():
                for operation in operations:
                    # plt.gca().add_patch(plt.Rectangle(
                        # (operation[1], machine), operation[2] - 0.1, 0.9, name="cos"))
                    rectangles.append((str(operation[0]), mpatch.Rectangle(
                        (operation[1], machine + 1.5), operation[2] - 0.2, 0.9, color=colorsHEX[machine]), ))

            for r in rectangles:
                ax.add_artist(r[1])
                rx, ry = r[1].get_xy()
                cx = rx + r[1].get_width() / 2.0
                cy = ry + r[1].get_height() / 2.0

                ax.annotate(r[0], (cx, cy), color='black', weight='bold',
                            fontsize=8, ha='center', va='center')

            # drawing the frame's barriers
            # for line in lines:
            #     plt.axvline(x=line, color='red', linewidth=1, linestyle='--')

            # ax.set_xlim((0, get_result(jobs, solution) + 1))
            ax.set_xlim(0, 65)
            ax.set_ylim((1, len(self.instance) + 2))
            ax.set_xticks(range(0, self.get_result() + 1, 2))
            ax.set_yticks(range(1, len(self.instance) + 2))
            ax.set_yticklabels(['', *map(str, range(1, len(self.instance) + 1))])
            ax.tick_params(left=False)
            ax.set_ylabel('Machine')
            ax.set_xlabel('Time Units')
            plt.show()
            # else:
            #     folder_path = './img/gantt/' + folder
            #     Path(folder_path).mkdir(parents=True, exist_ok=True)
            #     number = len(glob.glob(folder_path + '/*'))
            #     plt.savefig(folder_path + '/' + '0' * (4 - len(str(number))) + str(number)
            #                 + '_' + str(get_result(jobs, solution)))
            plt.close()

        if mode == 'ascii':
            #TODO: check if ascii mode is possible
            pass


i = Instance()
a = Solution(i)
print(a)
