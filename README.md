# Quantum-Based Job Shop Scheduling

A heuristic approach on how to optimally schedule jobs using a quantum computer.

Given a set of jobs and a finite number of machines, how should we schedule our jobs
on those machines such that all our jobs are completed at the earliest possible time?
This question is the job shop scheduling problem!

## Running the tests

### Installing libraries and dependencies
To run the script, you have to install required python libraries:

https://docs.ocean.dwavesys.com/en/latest/overview/install.html

To do that on D-wave's Quantum Computer rather than it's simulation,
you also need to create an account and configure a solver:

https://docs.ocean.dwavesys.com/en/latest/overview/dwavesys.html#dwavesys

### Simple execution on a chosen dataset

```
python3 demo.py input_file.txt
```

## Algorithm in work

<img src="img/solutions5_2_cropped.gif"/>

## References
D. Venturelli, D. Marchand, and G. Rojo, "Quantum Annealing Implementation of Job-Shop Scheduling", https://arxiv.org/abs/1506.08479v2

D-wave's Quantum Computer JSP Demo:
https://github.com/dwave-examples/job-shop-scheduling/tree/104b3206f9c650b28383ffb571a8d677c9a81549
