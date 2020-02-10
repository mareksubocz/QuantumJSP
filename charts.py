from __future__ import print_function

import matplotlib.pyplot as plt
import time
import neal
import numpy as np

from dwave.system.composites import EmbeddingComposite
from dwave.system.samplers import DWaveSampler

from job_shop_scheduler import get_jss_bqm

from instance_parser import *
from utilities import *
from partial_brute_force import solve_with_pbruteforce

from copy import deepcopy, copy
from collections import defaultdict
from pprint import pprint
from statistics import median
from warnings import filterwarnings


def printResults(sampleset, jobs):
    solution_dict = defaultdict(int)

    for sample, occurrences in sampleset.data(
        ["sample", "num_occurrences"]
    ):
        selected_nodes = [k for k, v in sample.items() if v ==
                          1 and not k.startswith('aux')]

        # Parse node information
        task_times = {k: [-1] * len(v) for k, v in jobs.items()}
        for node in selected_nodes:
            job_name, task_time = node.rsplit("_", 1)
            task_index, start_time = map(int, task_time.split(","))
            task_times[job_name][task_index] = start_time

        result = 0
        for job, times in task_times.items():
            if -1 in times:
                solution_dict["error"] += occurrences
                break
            result = max(result, times[-1] + jobs[job][-1][1])
        else:
            solution_dict[result] += occurrences

    best_solution = sampleset.first.sample
    selected_nodes = [k for k, v in best_solution.items() if v ==
                      1 and not k.startswith('aux')]

    # Parse node information
    task_times = {k: [-1] * len(v) for k, v in jobs.items()}
    for node in selected_nodes:
        job_name, task_time = node.rsplit("_", 1)
        task_index, start_time = map(int, task_time.split(","))

        task_times[job_name][task_index] = start_time
        # for job, times in task_times.items():
        #     print("{0:9}: {1}".format(job, times))

    return solution_dict


def num_of_errors_in_times(qpu=False):
    jobs = {"1": [(0, 2), (1, 1), (0, 1)],
            "2": [(1, 1), (0, 1), (2, 2)],
            "3": [(2, 1), (2, 1), (1, 1)]}

    times = range(4, 12)
    errors = defaultdict(list)
    for time in times:
        for i in range(12):
            try:
                bqm = get_jss_bqm(jobs, time, stitch_kwargs={
                    'min_classical_gap': 2.0})
                if qpu:
                    sampler = EmbeddingComposite(
                        DWaveSampler(solver={'qpu': True}))
                    sampleset = sampler.sample(
                        bqm, chain_strength=2, num_reads=1000)
                else:
                    sampler = neal.SimulatedAnnealingSampler()
                    sampleset = sampler.sample(bqm, num_reads=1000)
                sol_dict = printResults(sampleset, jobs)
                errors[time].append(sol_dict['error'])
            except:
                print(f"error: {time}")
                continue
    medians = []
    margins = []
    for key, values in errors.items():
        values.sort()
        values = values[1:-1]
        medians.append(median(values))
        margins.append([abs(values[0] - median(values)),
                        abs(values[-1] - median(values))])
    plt.errorbar(errors.keys(), medians, yerr=np.array(
        margins).T, fmt='o', color='blue')
    plt.xlabel('max_time value')
    plt.ylabel('number of error solutions provided (out of 1000)')
    # plt.show()
    plt.savefig('times.png')
    print(errors)


def num_of_errors_in_chain_strengths(qpu=False):
    jobs = {"1": [(0, 2), (1, 1), (2, 1)],
            "2": [(1, 1), (0, 1), (3, 2)],
            "3": [(2, 1), (3, 1), (1, 1)]}

    strengths = (0.5, 1, 1.5, 1.8, 2.0, 2.1, 2.3, 2.5, 3.0, 3.5, 4.0)
    errors = defaultdict(list)
    for strength in strengths:
        for i in range(12):
            print("tick " + str(strength) + " " + str(i))
            try:
                bqm = get_jss_bqm(jobs, 8, stitch_kwargs={
                    'min_classical_gap': 2.0})
                if qpu:
                    sampler = EmbeddingComposite(
                        DWaveSampler(solver={'qpu': True}))
                    sampleset = sampler.sample(
                        bqm, chain_strength=strength, num_reads=1000)
                else:
                    sampler = neal.SimulatedAnnealingSampler()
                    sampleset = sampler.sample(bqm, num_reads=1000)
                sol_dict = printResults(sampleset, jobs)
                errors[strength].append(sol_dict['error'])
            except Exception as e:
                print(f"error: {strength}")
                print(e)
                continue
    medians = []
    margins = []
    for key, values in errors.items():
        values.sort()
        values = values[1:-1]
        medians.append(median(values))
        margins.append([abs(values[0] - median(values)),
                        abs(values[-1] - median(values))])
    plt.errorbar(errors.keys(), medians, yerr=np.array(
        margins).T, fmt='o-', color='blue')
    plt.xlabel('chain strength')
    plt.ylabel('number of error solutions provided (out of 1000)')
    # plt.show()
    plt.savefig('chain_strength.png')
    print(errors)


def num_of_errors_in_length(qpu=True):
    jobs3 = {"1": [(0, 2), (1, 1), (0, 1)],
             "2": [(1, 1), (0, 1), (2, 2)],
             "3": [(2, 1), (2, 1), (1, 1)]}
    jobs4 = {"1": [(0, 2), (1, 1), (0, 1)],
             "2": [(1, 1), (0, 1), (2, 2)],
             "3": [(2, 1), (2, 1), (1, 1)]}
    jobs5 = {"1": [(0, 2), (1, 1), (0, 1)],
             "2": [(1, 1), (0, 1), (2, 2)],
             "3": [(2, 1), (2, 1), (1, 1)]}
    jobs6 = {"1": [(0, 2), (1, 1), (0, 1)],
             "2": [(1, 1), (0, 1), (2, 2)],
             "3": [(2, 1), (2, 1), (1, 1)]}
    jobs7 = {"1": [(0, 2), (1, 1), (0, 1)],
             "2": [(1, 1), (0, 1), (2, 2)],
             "3": [(2, 1), (2, 1), (1, 1)]}


def frequencies():
    jobs = readInstance("data/ft06.txt")
    results = defaultdict(int)
    ilosc = 10000
    for i in range(ilosc):
        results[get_result(jobs, solve_greedily(jobs))] += 1
    pprint(results)
    plt.bar(list(results.keys()), list(results.values()), align='center')
    plt.ylabel(f'Number of occurrences (out of {ilosc})')
    plt.xlabel('Makespan')
    plt.show()


def partial_bruteforce_visualisation(folder_name, jobs_full_len=None, max_time=70, num_of_times=10, qpu=False):
    if jobs_full_len is None:
        jobs_full_len = readInstance("data/ft06.txt")

    jobs_squashed_len = squash_lengths(jobs_full_len)
    for j in [5]:
        solution = solve_greedily(jobs_full_len)
        print(
            f"Wynik po rozw. zachłannym: {get_result(jobs_full_len, solution)}")
        print(f"Zaczynamy dla okna o szerokości {j}.")
        next_result_checkpoint = solution
        for result_checkpoint, line_tick in solve_with_pbruteforce(
                jobs_squashed_len,
                solution,
                max_time=get_result(jobs_squashed_len, solution) + 1,
                qpu=qpu,
                window_size=j,
                num_reads=5000,
                chain_strength=2,
                times=num_of_times):
            draw_solution(jobs_squashed_len, next_result_checkpoint,
                          folder_name, [line_tick, line_tick + j])
            draw_solution(jobs_squashed_len, result_checkpoint,
                          folder_name, [line_tick, line_tick + j])

            order_full = get_order(result_checkpoint)
            full_result_checkpoint = solve_with_order(
                jobs_full_len, order_full)
            draw_solution(jobs_full_len, full_result_checkpoint,
                          folder_name, [], full=True)

            next_result_checkpoint = deepcopy(result_checkpoint)
        final_result = result_checkpoint
        print(f"końcowy rezultat: {get_result(jobs_full_len, final_result)}")


if __name__ == "__main__":
    # num_of_errors_in_times(qpu=True)
    partial_bruteforce_visualisation("kolorowe_krotkie_poprawione3")
    # num_of_errors_in_chain_strengths(qpu=True)
    # frequencies()
