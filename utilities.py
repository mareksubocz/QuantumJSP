import plotly.express as px
from instance_parser import get_result
from datetime import datetime

import plotly.figure_factory as ff


def convert_to_datetime(x):
  return datetime.fromtimestamp(31536000+x*24*3600).strftime("%Y-%m-%d")

def draw_solution(jobs: dict, solution: dict, x_max=None, lines=[]):
    df = []
    if x_max is None:
        x_max = get_result(jobs, solution)
    for job, tasks in solution.items():
        for i, start in enumerate(tasks):
            machine, length = jobs[job][i]
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


if __name__ == "__main__":

    jobs = {1: [(2, 1), (0, 1), (1, 2), (3, 3), (5, 1), (4, 2)],
            2: [(1, 3), (2, 2), (4, 3), (5, 3), (0, 3), (3, 2)],
            3: [(2, 2), (3, 2), (5, 3), (0, 3), (1, 1), (4, 3)],
            4: [(1, 2), (0, 2), (2, 2), (3, 1), (4, 3), (5, 3)],
            5: [(2, 3), (1, 1), (4, 2), (5, 2), (0, 1), (3, 1)],
            6: [(1, 1), (3, 1), (5, 3), (0, 3), (4, 2), (2, 1)]}
    solution = {1: [0, 1, 6, 8, 11, 19],
                2: [3, 6, 12, 15, 18, 21],
                3: [1, 3, 5, 8, 15, 21],
                4: [1, 3, 8, 11, 16, 19],
                5: [3, 9, 10, 12, 16, 17],
                6: [0, 1, 2, 5, 8, 10]}

    draw_solution(jobs, solution, lines=[10, 15])
