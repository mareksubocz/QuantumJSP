from copy import deepcopy
import dimod
from stats import Statistics
from dimod.vartypes import ExtendedVartype, Vartype
from dwave.system.composites.embedding import EmbeddingComposite
from dwave.system.samplers.dwave_sampler import DWaveSampler
from dwave.system.samplers.leap_hybrid_sampler import LeapHybridDQMSampler
from greedy.composite import SteepestDescentComposite
from solution import Solution
from dqm_scheduler import get_jss_dqm
from pyqubo_scheduler import get_jss_bqm
from csp_scheduler import get_jss_csp
from tabu import TabuSampler
from collections import defaultdict
from instance_parser import (
    solve_worse,
    solve_greedily,
)

class InstanceNew(dict):
    def __init__(
        self,
        path=None,
        instance=None,
        **kwargs
    ):
        """
        A class to encapsulate a JSP instance, provides solve function.

        **kwargs:
            disable_since=None,
            disable_till=None,
            disabled_variables=None
        """
        assert (
            path or instance
        ), "Provide path to instance file or an already constructed instance."

        if path:
            instance = self.__read_file(path)
        super().__init__(instance)

    def __read_file(self, path: str) -> dict:
        job_dict = defaultdict(list)
        with open(path) as f:
            self.n_jobs, self.n_machines = list(map(int, f.readline().split()))
            for i, line in enumerate(f):
                lint = list(map(int, line.split()))
                job_dict[i + 1] = [
                    x for x in zip(
                        lint[::2],   # machines
                        lint[1::2])  # operation lengths
                ]
            return job_dict

    def squash(self, steps=(4,7)):
        """Returns an instance with the same operations, but with
        squashed lengths to [1,2,3,..., len(steps)+1]

        Args:
            instance (dict): instance to be squashed
            steps (list, optional): lengths at which operations
            are qualified to a longer length. Defaults to [4, 7].
        """
        steps = list(steps)
        steps.sort()
        steps.append(float('inf'))

        result = deepcopy(self)

        for operations in result.values():
            for j, operation in enumerate(operations):
                for i, step in enumerate(steps, start=1):
                    if operation[1] < step:
                        operations[j] = (operation[0], i)
                        break
        return InstanceNew(instance=result)


class Instance(dict):
    def __init__(
        self,
        path="",
        instance={},
        max_time=None,
        disable_since=None,
        disable_till=None,
        disabled_variables=None,
    ):
        """
        A class to encapsulate a JSP instance, provides solve function.
        """
        assert (
            path or instance
        ), "Provide path to instance or an already constructed instance."

        if path:
            instance = self.read_file(path)
        super().__init__(instance)

        # TODO: use better approximation
        # sum of times of all tasks
        # max_time = sum([sum([t for m,t in job]) for job in self.values()])
        if max_time is None:
            self.max_time = max(
                Solution(self, solution=solve_greedily(self)).get_result(),
                Solution(self, solution=solve_worse(self)).get_result(),
            )
        else:
            self.max_time = max_time

        self.path = path
        self.disable_since = disable_since
        self.disable_till = disable_till
        self.disabled_variables = disabled_variables

    def read_file(self, path: str) -> dict:
        job_dict = defaultdict(list)
        with open(path) as f:
            self.n_jobs, self.n_machines = list(map(int, f.readline().split()))
            for i, line in enumerate(f):
                lint = list(line.split())
                job_dict[str(i + 1)] = [
                    x for x in zip(
                        lint[::2],   # machines
                        map(int, lint[1::2]))  # operation lengths
                ]
            return job_dict

    def __extract_solution_from_sample(self, sample, type):
        if type == Vartype.BINARY:
            selected_nodes = [k for k, v in sample.items() if v == 1]

            # Parse node information
            task_times = {k: [-1] * len(v) for k, v in self.items()}
            for node in selected_nodes:
                if 'aux' in str(node):
                    continue
                job_name, task_time = node.rsplit("_", 1)
                task_index, start_time = map(int, task_time.split(","))

                task_times[job_name][task_index] = start_time
            return Solution(self, solution=task_times)
        elif type == ExtendedVartype.DISCRETE:
            selected_nodes = [','.join((k, str(v))) for k, v in sample.items()]

            task_times = {k: [-1] * len(v) for k, v in self.items()}
            for node in selected_nodes:
                if 'aux' in str(node):
                    continue
                job_name, task_time = node.rsplit("_", 1)
                task_index, start_time = map(int, task_time.split(","))
                task_times[job_name][task_index] = start_time
            return Solution(self, solution=task_times)
        else:
            raise NotImplementedError('This vartype is not supported.')

    def squash(self, steps=None):
        """Returns an instance with the same operations, but with
        squashed lengths to [1,2,3,..., len(steps)+1]

        Args:
            instance (dict): instance to be squashed
            steps (list, optional): lengths at which operations
            are qualified to a longer length. Defaults to [4, 7].
        """

        if steps is None:
            steps = [4,7]
        steps.sort()
        steps.append(float('inf'))

        result = deepcopy(self)

        for operations in result.values():
            for j, operation in enumerate(operations):
                for i, step in enumerate(steps, start=1):
                    if operation[1] < step:
                        operations[j] = (operation[0], i)
                        break
        return Instance(instance=result)

    def __get_order(self, solution):
        order = []
        for job, start_times in solution.items():
            for i, start_time in enumerate(start_times):
                order.append((start_time, (job, i)))
            # order.extend([(value[x], (key, x)) for x in range(len(value))])
        order.sort()
        res = [x[1] for x in order]
        return res

    def solve_with_order(self, solution):
        order = self.__get_order(solution)
        last_in_job = defaultdict(int)  # default is 0
        last_in_machine = defaultdict(int)
        solution = defaultdict(list)
        for key, index in order:
            machine = self[key][index][0]
            length = self[key][index][1]

            start = max(last_in_job[key], last_in_machine[machine])

            solution[key].append(start)
            last_in_job[key] = start + length
            last_in_machine[machine] = start + length
        return Solution(self, solution=solution)

    def solve(self,
              mode="greedy",
              num_reads=1000,
              postprocessing=False,
              statistics=False,
              optimal=0,
              heuristic=False,
              is_squashed=None,
              is_cut_out=None,
              window_size=None,
              window_start=None
              ):
        """
        Available modes are:
            - greedy: simple greedy solver
              WARNING: not usable for partial brute-force

            - worse: greedy solver giving worse results (more room for improvement).
              Involves element of randomness.
              WARNING: not usable for partial brute-force

            - csp: construct bqm using ConstraintSatisfactionProblem and solve
            by quantum annealing

            - pyqubo: construct bqm using pyqubo and solve by quantum annealing

            - sim_pyqubo: construct bqm using pyqubo and solve by simmulated annealing

            - discrete: solve problem using DiscreteQuadraticModel and solve by
            hybrid annealing
        """
        available_modes = [
            "greedy",
            "worse",
            "csp",
            "pyqubo",
            "sim_pyqubo",
            "discrete",
        ]
        assert mode in available_modes, f"Choose one of: {available_modes}"

        # -------- classic methods --------
        if mode == 'greedy':
            self.last_sampleset = None
            return Solution(self, solution=solve_greedily(self))

        elif mode == "worse":
            self.last_sampleset = None
            return Solution(self, solution=solve_worse(self))



        # -------- BQM methods --------
        sampler = DWaveSampler()

        if mode == "csp":
            bqm = get_jss_csp(self, self.max_time,
                              disable_since=self.disable_since,
                              disable_till=self.disable_till,
                              disabled_variables=self.disabled_variables)
            sampler = EmbeddingComposite(sampler)

        elif mode == "pyqubo":
            bqm = get_jss_bqm(self, self.max_time,
                              disable_since=self.disable_since,
                              disable_till=self.disable_till,
                              disabled_variables=self.disabled_variables)
            sampler = EmbeddingComposite(sampler)

        elif mode == "sim_pyqubo":
            bqm = get_jss_bqm(self, self.max_time,
                              disable_since=self.disable_since,
                              disable_till=self.disable_till,
                              disabled_variables=self.disabled_variables)
            sampler = TabuSampler()

        if postprocessing:
            sampler = SteepestDescentComposite(sampler)

        # -------- DQM method --------
        if mode == 'discrete':
            if postprocessing:
                print('Additional postprocessing is not available in discrete mode.')

            #FIXME: give more adequate name than bqm for what is really dqm
            bqm = get_jss_dqm(self, self.max_time,
                              disable_since=self.disable_since,
                              disable_till=self.disable_till,
                              disabled_variables=self.disabled_variables)
            # pegasus - Advantage, chimera - 2000Q
            sampler = LeapHybridDQMSampler()
            sampleset = sampler.sample_dqm(bqm)

        else:
            sampleset = sampler.sample(bqm, num_reads=num_reads,
                                       return_embedding=True)
        solution = self.__extract_solution_from_sample(
            sampleset.first.sample, sampleset.vartype
        )

        if statistics:
            feasibles = []
            results = []
            for sample in sampleset.samples():
                sample_solution = self.__extract_solution_from_sample(
                    sample, sampleset.vartype
                )
                feasibles.append(sample_solution.is_valid())
                results.append(sample_solution.get_result())

            sampleset = dimod.append_data_vectors(
                sampleset, feasible=feasibles, result=results
            )

            tasks_times = []
            for tasks in self.values():
                tasks_times.extend([t for _, t in tasks])
            self.recent_statistics = Statistics(sampleset, self.path,
                                                self.max_time,
                                                postprocessing,
                                                mode,
                                                optimal=optimal,
                                                number_of_jobs=len(self),
                                                number_of_tasks=sum([len(x) for x in self.values()]),
                                                tasks_times=tasks_times,
                                                is_squashed=is_squashed,
                                                heuristic=heuristic,
                                                is_cut_out=is_cut_out,
                                                window_size=window_size,
                                                window_start=window_start
                                                )
        return solution
