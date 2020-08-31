from job_shop_scheduler import get_jss_bqm
from dwave.system.composites import EmbeddingComposite
from dwave.system.samplers import DWaveSampler
from charts import printResults
import csv
import matplotlib.pyplot as plt
import pandas as pd
from pprint import pprint

def get_instance(size):
    # instance = {'1': [(1,1), (2, 1)],
    #             '2': [(1,2), (2, 2)]}
    instance = { f'{i}': [((i+j)%size, 1) for j in range(size)] for i in range(size) }
    return instance

if __name__ == '__main__':

    num_reads = 1000
    with open("wyniki_rozmiar_instancji.csv", mode='a') as csvfile:
        filewriter = csv.writer(csvfile, delimiter=',',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for size in range(2, 5):
            for i in range(20):
                jobs = get_instance(size)
                try:
                    bqm = get_jss_bqm(jobs, size+2, stitch_kwargs={
                        'min_classical_gap': 2.0})
                    sampler = EmbeddingComposite(
                        DWaveSampler(solver={'qpu': True}))
                    sampleset = sampler.sample(
                        bqm, chain_strength=10, num_reads=num_reads)
                    sol_dict = printResults(sampleset, jobs)
                except Exception as e:
                    print(f"error: {size}")
                    print(e)
                    from time import sleep
                    sleep(60)
                    continue
                result_row = [size, sol_dict['error'], sol_dict['incorrect'],
                              num_reads, sol_dict[size]]
                filewriter.writerow(result_row)
                print('zapisane', size)

        # from time import sleep
        # sleep(30)
