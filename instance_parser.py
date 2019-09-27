from collections import defaultdict


def readInstance(path: str) -> dict:
    job_dict = defaultdict(list)
    with open(path) as f:
        f.readline()
        for i, line in enumerate(f):
            lint = list(map(int, line.split()))
            job_dict[i+1] = [x for x in
                             zip(lint[::2],  # machines
                                 lint[1::2]  # operation lengths
                                 )]
        return job_dict
