# Quantum Job Shop Scheduling Problem Solver

A heuristic approach on how to optimally schedule jobs using a quantum computer.

## General info
Given a set of jobs and a finite number of machines, how should we schedule our jobs
on those machines such that all our jobs are completed at the earliest possible time?
This question is the job shop scheduling problem!

## Table of contents
* [Running the tests](#running-the-tests)
* [Algorithm in work](#algorithm-in-work)
* [References](#references)

## Running the tests

### Installing libraries and dependencies
To run the script, you have to install required python libraries:

https://docs.ocean.dwavesys.com/en/latest/overview/install.html

To do that on D-wave's Quantum Computer rather than it's simulation,
you also need to create an account and configure a solver:

https://docs.ocean.dwavesys.com/en/latest/overview/dwavesys.html#dwavesys

### Quick

```
python3 demo.py data/ft06.txt
```

## Algorithm in work

<img src="img/solutions5_2_cropped.gif"/>

## References
D. Venturelli, D. Marchand, and G. Rojo, "Quantum Annealing Implementation of Job-Shop Scheduling", https://arxiv.org/abs/1506.08479v2
