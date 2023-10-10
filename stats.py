import dimod
from typing import List
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from statistics import mean, median, stdev
from instance_best import RECORDS
from pathlib import Path

class Statistics:
    def __init__(
        self,
        sampleset: dimod.SampleSet,
        instance_name: str,
        max_time: int,
        postprocessing: bool,
        mode: str,
        number_of_jobs: int,
        number_of_tasks: int,
        tasks_times: List[int],
        is_squashed: bool,
        heuristic: bool,
        optimal: int|None = None,
        is_cut_out: bool|None = None,
        window_size: int|None = None,
        window_start: int|None = None,

    ):
        self.sampleset = sampleset
        self.df_sampleset = self.sampleset.to_pandas_dataframe()
        self.instance_name = instance_name
        self.max_time = max_time
        self.postprocessing = postprocessing
        self.mode = mode
        if optimal is None and self.instance_name in RECORDS:
            self.optimal = RECORDS[self.instance_name]
        else:
            self.optimal = optimal
        self.number_of_jobs = number_of_jobs
        self.number_of_tasks = number_of_tasks
        self.tasks_times = tasks_times
        self.is_squashed = is_squashed
        self.heuristic = heuristic
        self.max_task_time = max(tasks_times)
        self.mean_task_time = mean(tasks_times)
        if self.heuristic:
            self.is_cut_out = is_cut_out
            if self.is_cut_out:
                self.window_size = window_size
                self.window_start = window_start
        self.num_reads = self.df_sampleset["num_occurrences"].sum()
        if "embedding_context" in self.sampleset.info.keys():
            self.chain_strength = self.sampleset.info["embedding_context"][
                "chain_strength"
            ]
            self.chain_break_method = self.sampleset.info["embedding_context"][
                "chain_break_method"
            ]
        if "timing" in self.sampleset.info.keys():
            # FIXME: check if timing is dict for sure
            self.timing = sampleset.info['timing']
        self.energy_best = min(self.sampleset.record.energy)
        self.num_feasible = sum(self.sampleset.record.feasible)

        feasible_results = []
        self.num_optimal = 0
        for feasible, result in zip(self.sampleset.record.feasible,
                                    self.sampleset.record.result):
            if feasible:
                feasible_results.append(result)
                if result == self.optimal:
                    self.num_optimal += 1

        self.result_best = min(feasible_results) if feasible_results else None

        # TDOO: number of error vs unfeasible?
        # TODO: zmienić unfeasible na infeasible

    def save_to_csv(self, filename):
        # if new_file:
        #     df = pd.DataFrame()
        # else:
        #     df = pd.read_csv(filename, index_col=0)
        info = {
            'instance': self.instance_name,
            'max_time': self.max_time,
            'postprocessing': self.postprocessing,
            'version': self.mode,
            'num_reads': self.num_reads,
            'num_feasible': self.num_feasible,
            'num_optimal': self.num_optimal,
            'number_of_jobs': self.number_of_jobs,
            'number_of_tasks': self.number_of_tasks,
            'is_squashed': self.is_squashed,
            'max_task_time': self.max_task_time,
            'mean_task_time': self.mean_task_time,
            'heuristic': self.heuristic,
            'optimal': self.optimal,
            'energy_best': self.energy_best,
            'result_best': self.result_best,
        }
        if hasattr(self, 'chain_strength'):
            info['chain_strength'] = self.chain_strength
        if hasattr(self, 'chain_break_method'):
            info['chain_break_method'] = self.chain_break_method
        if hasattr(self, 'timing'):
            info.update(self.timing)
        if hasattr(self, 'is_cut_out'):
            info['is_cut_out'] = self.is_cut_out
        if hasattr(self, 'window_size'):
            info['window_size'] = self.window_size
        if hasattr(self, 'window_start'):
            info['window_start'] = self.window_start

        file = Path(filename)
        info = pd.DataFrame(info, index=[0])
        if not file.exists():
            print("file doesn't exist")
            df = info
        else:
            # dataframe anly needed for linter
            df = pd.DataFrame(pd.read_csv(filename, index_col=0))
            # df = df.append(info, ignore_index=True)
            df = pd.concat([df, info])
        df.to_csv(filename)
