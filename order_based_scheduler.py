from __future__ import print_function

from bisect import bisect_right
from platform import machine

import dwavebinarycsp


def get_jss_bqm(job_dict, stitch_kwargs=None):
    if stitch_kwargs is None:
        stitch_kwargs = {}

    scheduler = JobShopScheduler(job_dict)
    return scheduler.get_bqm(stitch_kwargs)


def sum_to_one(*args):
    return sum(args) == 1


def get_label(task, number_in_queue):
    """Creates a standardized name for variables in the constraint satisfaction problem,
    JobShopScheduler.csp.
    """
    return f"{task.number}_{number_in_queue}"


class Task:
    def __init__(self, job, position, machine, duration, number):
        self.job = job
        self.position = position
        self.machine = machine
        self.duration = duration
        self.number = number

    def __repr__(self):
        return ("{{job: {job}, position: {position}, machine: {machine},\
         duration: {duration}, number: {number}}}").format(**vars(self))


class JobShopScheduler:
    def __init__(self, job_dict):
        self.tasks = []
        # self.last_task_indices = []
        self.csp = dwavebinarycsp.ConstraintSatisfactionProblem(
            dwavebinarycsp.BINARY)

        # Populates self.tasks and self.max_time
        self._process_data(job_dict)

    def _process_data(self, jobs):
        """Process user input into a format that is more convenient for JobShopScheduler functions.
        """
        # Create and concatenate Task objects
        tasks = []

        for i, job_name, job_tasks in enumerate(jobs.items()):
            for j, (machine, time_span) in enumerate(job_tasks):
                number = j * len(jobs.items()) + i + 1
                tasks.append(Task(job_name, j, machine, time_span, number))

        # Update values
        self.tasks = tasks

    def _add_one_start_constraint(self):
        """self.csp gets the constraint: A task can start once and only once
        """
        for task in self.tasks:
            task_positions = {get_label(task, i) for i in range(self.tasks)}
            self.csp.add_constraint(sum_to_one, task_positions)

    def _add_exclusiveness_constraint(self):
        """A position in queue can be occupied by just one task
        """
        for i in range(self.tasks):
            task_positions = {get_label(task, i) for task in self.tasks}
            self.csp.add_constraint(sum_to_one, task_positions)

    def _add_precedence_constraint(self):  # FIXME
        """self.csp gets the constraint: Task must follow a particular order.
         Note: assumes self.tasks are sorted by jobs and then by position
        """
        valid_edges = {(0, 0), (1, 0), (0, 1)}
        for current_task, next_task in zip(self.tasks, self.tasks[1:]):
            if current_task.job != next_task.job:
                continue

            # Forming constraints with the relevant times of the next task
            for t in range(self.tasks):
                current_label = get_label(current_task, t)

                for tt in range(min(t + current_task.duration, self.tasks)):
                    next_label = get_label(next_task, tt)
                    self.csp.add_constraint(
                        valid_edges, {current_label, next_label})

    def get_bqm(self, stitch_kwargs=None):
        """Returns a BQM to the Job Shop Scheduling problem.
        Args:
            stitch_kwargs: A dict. Kwargs to be passed to dwavebinarycsp.stitch.
        """
        if stitch_kwargs is None:
            stitch_kwargs = {}

        # Apply constraints to self.csp
        self._add_one_start_constraint()
        self._add_precedence_constraint()
        self._add_exclusiveness_constraint()

        # Get BQM
        bqm = dwavebinarycsp.stitch(self.csp, **stitch_kwargs)

        # Edit BQM to encourage the shortest schedule
        # Overview of this added penalty:
        # - Want any-optimal-schedule-penalty < any-non-optimal-schedule-penalty
        # - Suppose there are N tasks that need to be scheduled and N > 0
        # - Suppose the the optimal end time for this schedule is t_N
        # - Then the worst optimal schedule would be if ALL the tasks ended at time t_N. (Since
        #   the optimal schedule is only dependent on when the LAST task is run, it is irrelevant
        #   when the first N-1 tasks end.) Note that by "worst" optimal schedule, I am merely
        #   referring to the most heavily penalized optimal schedule.
        #
        # Show math satisfies any-optimal-schedule-penalty < any-non-optimal-schedule-penalty:
        # - Penalty scheme. Each task is given the penalty: base^(task-end-time). The penalty
        #   of the entire schedule is the sum of penalties of these chosen tasks.
        # - Chose the base of my geometric series to be N+1. This simplifies the math and it will
        #   become apparent why it's handy later on.
        #
        # - Comparing the SUM of penalties between any optimal schedule (on left) with that of the
        #   WORST optimal schedule (on right). As shown below, in this penalty scheme, any optimal
        #   schedule penalty <= the worst optimal schedule.
        #     sum_i (N+1)^t_i <= N * (N+1)^t_N, where t_i the time when the task i ends  [eq 1]
        #
        # - Now let's show that all optimal schedule penalties < any non-optimal schedule penalty.
        #   We can prove this by applying eq 1 and simply proving that the worst optimal schedule
        #   penalty (below, on left) is always less than any non-optimal schedule penalty.
        #     N * (N+1)^t_N < (N+1)^(t_N + 1)
        #                               Note: t_N + 1 is the smallest end time for a non-optimal
        #                                     schedule. Hence, if t_N' is the end time of the last
        #                                     task of a non-optimal schedule, t_N + 1 <= t_N'
        #                   <= (N+1)^t_N'
        #                   < sum^(N-1) (N+1)^t_i' + (N+1)^t_N'
        #                   = sum^N (N+1)^t_i'
        #                               Note: sum^N (N+1)^t' is the sum of penalties for a
        #                                     non-optimal schedule
        #
        # - Therefore, with this penalty scheme, all optimal solution penalties < any non-optimal
        #   solution penalties
        # base = len(self.last_task_indices) + 1     # Base for exponent

        # for i in self.last_task_indices:
        # task = self.tasks[i]

        for t in range(self.max_time):
            end_time = t + task.duration

            # Check task's end time; do not add in absurd times
            if end_time > self.max_time:
                continue

            # Add bias to variable
            bias = 2 * base**(end_time - self.max_time)
            label = get_label(task, t)
            if label in pruned_variables:
                bqm.add_variable(label, bias)

        return bqm
