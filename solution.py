from dqm_scheduler import get_label, Task, get_jss_dqm
from csp_scheduler import get_jss_csp as get_jss_bqm
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


class Solution(dict):
    def __init__(self, instance, solution = defaultdict(list)):
        super().__init__(solution)
        self.instance = instance

    def is_valid(self):
        # checking if there is no -1
        for operations in self.values():
            for time in operations:
                if time < 0:
                    return False

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

    def get_starting_point(self) -> int:
        """
        The point of beginning of the first task

        NOTE: 0 is considered maximum starting point.
        """
        min_time = 0
        for job, operations in self.instance.items():
            min_time = min(min_time, self[job][0])
        return int(min_time)

    def get_order(self) -> list:
        order = []
        for job, start_times in self.items():
            for i, start_time in enumerate(start_times):
                order.append((start_time, (job, i)))
            # order.extend([(value[x], (key, x)) for x in range(len(value))])
        order.sort()
        res = [x[1] for x in order]
        return res

    def cut_part_out(self, start: int, end: int):
        new_jobs = defaultdict(list)
        first_task_per_job = {}

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
                    if job_name not in first_task_per_job:
                        first_task_per_job[job_name] = i

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

        return new_jobs, first_task_per_job, disable_till, disable_since, disabled_variables

    def put_part_in(self, solution_part, first_tasks: dict):
        """
        Works in-place!
        """
        for job in solution_part.keys():
            for i, task_start in enumerate(solution_part[job]):
                proper_index = i + first_tasks[job]
                self[job][proper_index] = task_start

    def visualize(self, mode='plotly', x_max=None):
        """
        Available modes are:
            - plotly: visualize using plotly (modern and interactive)
            - matplotlib: visualize using matplotlib (simple, paper-friendly)
        """
        available_modes = ['plotly', 'matplotlib']
        assert mode in available_modes, f'Choose one of: {available_modes}'

        if mode == 'plotly':
            def convert_to_datetime(x):
                return datetime.fromtimestamp(31536000+x*24*3600).strftime("%Y-%m-%d")

            # df = [dict(Job=str(i)) for i in range(1, len(self.keys())+1)]
            df = [dict(Job=str(k)) for k in self.keys()]
            if x_max is None:
                x_max = self.get_result()
            for job, tasks in self.items():
                for i, start in enumerate(tasks):
                    machine, length = self.instance[job][i]
                    df.append(dict(Machine=machine,
                                   Start=convert_to_datetime(start),
                                   Finish=convert_to_datetime(start+length),
                                   Job=str(job)))

            df.sort(key=lambda x: x['Machine'] if 'Machine' in x else '')

            num_tick_labels = list(range(x_max+1))
            date_ticks = [convert_to_datetime(x) for x in num_tick_labels]

            fig = px.timeline(df, y="Machine", x_start="Start", x_end="Finish", color="Job")
            fig.update_traces(marker=dict(line=dict(width=3, color='black')), opacity=0.5)
            fig.layout.xaxis.update({
                'tickvals' : date_ticks,
                'ticktext' : num_tick_labels,
                'range' : [convert_to_datetime(0),
                           convert_to_datetime(self.instance.max_time)]
            })
            # fig.layout.yaxis.update({
            #     'tickvals' : list(range(len(self.keys()))),
            #     'ticktext' : list(range(1, len(self.keys())+1))
            # })
            fig.layout.legend.update({
                'traceorder': 'normal'
            })
            fig.show()

        if mode == 'matplotlib':
            pass
            colors = ['blue', 'red', 'green', 'violet', 'orange', 'azure']
            colorsHEX = ['#80B3FF', '#FF3333', '#79D279', '#C299FF', '#FFDAB3', '#93E0F5']
            import matplotlib.pyplot as plt
            import matplotlib.patches as mpatch
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.set_aspect(aspect=1.5)
            rectangles = []
            machine_dict = self.__transformToMachineDict()
            for machine, operations in machine_dict.items():
                for operation in operations:
                    # plt.gca().add_patch(plt.Rectangle(
                        # (operation[1], machine), operation[2] - 0.1, 0.9, name="cos"))
                    rectangles.append( (str(operation[0]),
                        mpatch.Rectangle(
                            (operation[1]+0.01, float(machine) + 1.5),
                            operation[2] - 0.02,
                            0.9,
                            facecolor=colorsHEX[int(operation[0])-1],
                            edgecolor='black',
                            linewidth=1
                        ),
                    ))

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
            ax.set_xticks(range(0, self.get_result() + 1))
            ax.set_yticks(range(1, len(self.instance) + 2))
            ax.set_yticklabels(['', *map(str, range(len(self.instance)))])
            ax.tick_params(left=False, rotation=270)
            ax.set_ylabel('Machine')
            ax.set_xlabel('Time Units')
            ax.grid(axis='x')
            ax.set_axisbelow(True)
            ax.set_ylim(1.4, len(self.instance)+1.5)
            ax.set_xlim(self.get_starting_point()-0.1, self.instance.max_time+0.1)
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
