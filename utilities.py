from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatch
from instance_parser import transformToMachineDict, get_result
import glob

colors = ['red', 'green', 'yellow', 'blue', 'violet', 'orange']
# colorsHEX = ['#FF3333', '#79D279', '#FFFF66', '#80B3FF', '#C299FF', '#FFDAB3']
colorsHEX = ['blue', 'blue', 'blue', 'blue', 'blue', 'blue']


def draw_solution(jobs, solution, folder=None, lines=[0, 0]):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.set_aspect(aspect=1.5)
    rectangles = []
    machine_dict = transformToMachineDict(jobs, solution)
    for machine, operations in machine_dict.items():
        for operation in operations:
            # plt.gca().add_patch(plt.Rectangle(
                # (operation[1], machine), operation[2] - 0.1, 0.9, name="cos"))
            rectangles.append((str(operation[0]), mpatch.Rectangle(
                (operation[1], machine + 0.5), operation[2] - 0.2, 0.9, color=colorsHEX[machine]), ))

    for r in rectangles:
        ax.add_artist(r[1])
        rx, ry = r[1].get_xy()
        cx = rx + r[1].get_width() / 2.0
        cy = ry + r[1].get_height() / 2.0

        ax.annotate(r[0], (cx, cy), color='black', weight='bold',
                    fontsize=8, ha='center', va='center')

    # rysowanie barier ramki
    for line in lines:
        plt.axvline(x=line, color='red', linewidth=1, linestyle='--')

    # ax.set_xlim((0, get_result(jobs, solution) + 1))
    ax.set_xlim(0, 65)
    ax.set_ylim((0, len(jobs) + 1))
    ax.set_xticks(range(0, get_result(jobs, solution) + 1, 2))
    ax.set_yticks(range(len(jobs) + 1))
    ax.set_yticklabels(['', *map(str, range(len(jobs)))])
    ax.tick_params(left=False)
    ax.set_ylabel('Machines')
    ax.set_xlabel('Time')
    if folder is None:
        plt.show()
    else:
        folder_path = './img/gantt/' + folder
        Path(folder_path).mkdir(parents=True, exist_ok=True)
        number = len(glob.glob(folder_path + '/*'))
        plt.savefig(folder_path + '/' + '0' * (4 - len(str(number))) + str(number)
                    + '_' + str(get_result(jobs, solution)))
    plt.close()


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
