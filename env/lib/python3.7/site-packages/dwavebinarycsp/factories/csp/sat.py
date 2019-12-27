# Copyright 2018 D-Wave Systems Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#
# ================================================================================================

from functools import reduce
from math import factorial
from operator import mul
from random import choice, sample, random

from six.moves import range

import dimod

from dwavebinarycsp.core.csp import ConstraintSatisfactionProblem
from dwavebinarycsp.factories.constraint.sat import sat2in4
from dwavebinarycsp.factories.constraint.gates import xor_gate

__all__ = ['random_2in4sat',
           'random_xorsat']


def random_2in4sat(num_variables, num_clauses, vartype=dimod.BINARY, satisfiable=True):
    """Random two-in-four (2-in-4) constraint satisfaction problem.

    Args:
        num_variables (integer): Number of variables (at least four).
        num_clauses (integer): Number of constraints that together constitute the
            constraint satisfaction problem.
        vartype (Vartype, optional, default='BINARY'): Variable type. Accepted
            input values:

            * Vartype.SPIN, 'SPIN', {-1, 1}
            * Vartype.BINARY, 'BINARY', {0, 1}
        satisfiable (bool, optional, default=True): True if the CSP can be satisfied.

    Returns:
        CSP (:obj:`.ConstraintSatisfactionProblem`): CSP that is satisfied when its variables
        are assigned values that satisfy a two-in-four satisfiability problem.

    Examples:
        This example creates a CSP with 6 variables and two random constraints and checks
        whether a particular assignment of variables satisifies it.

        >>> import dwavebinarycsp
        >>> import dwavebinarycsp.factories as sat
        >>> csp = sat.random_2in4sat(6, 2)
        >>> csp.constraints    # doctest: +SKIP
        [Constraint.from_configurations(frozenset({(1, 0, 1, 0), (1, 0, 0, 1), (1, 1, 1, 1), (0, 1, 1, 0), (0, 0, 0, 0),
         (0, 1, 0, 1)}), (2, 4, 0, 1), Vartype.BINARY, name='2-in-4'),
         Constraint.from_configurations(frozenset({(1, 0, 1, 1), (1, 1, 0, 1), (1, 1, 1, 0), (0, 0, 0, 1),
         (0, 1, 0, 0), (0, 0, 1, 0)}), (1, 2, 4, 5), Vartype.BINARY, name='2-in-4')]
        >>> csp.check({0: 1, 1: 0, 2: 1, 3: 1, 4: 0, 5: 0})       # doctest: +SKIP
        True


    """

    if num_variables < 4:
        raise ValueError("a 2in4 problem needs at least 4 variables")
    if num_clauses > 16 * _nchoosek(num_variables, 4):  # 16 different negation patterns
        raise ValueError("too many clauses")

    # also checks the vartype argument
    csp = ConstraintSatisfactionProblem(vartype)

    variables = list(range(num_variables))

    constraints = set()

    if satisfiable:
        values = tuple(vartype.value)
        planted_solution = {v: choice(values) for v in variables}

        configurations = [(0, 0, 1, 1), (0, 1, 0, 1), (1, 0, 0, 1),
                          (0, 1, 1, 0), (1, 0, 1, 0), (1, 1, 0, 0)]

        while len(constraints) < num_clauses:
            # sort the variables because constraints are hashed on configurations/variables
            # because 2-in-4 sat is symmetric, we would not get a hash conflict for different
            # variable orders
            constraint_variables = sorted(sample(variables, 4))

            # pick (uniformly) a configuration and determine which variables we need to negate to
            # match the chosen configuration
            config = choice(configurations)
            pos = tuple(v for idx, v in enumerate(constraint_variables) if config[idx] == (planted_solution[v] > 0))
            neg = tuple(v for idx, v in enumerate(constraint_variables) if config[idx] != (planted_solution[v] > 0))

            const = sat2in4(pos=pos, neg=neg, vartype=vartype)

            assert const.check(planted_solution)

            constraints.add(const)
    else:
        while len(constraints) < num_clauses:
            # sort the variables because constraints are hashed on configurations/variables
            # because 2-in-4 sat is symmetric, we would not get a hash conflict for different
            # variable orders
            constraint_variables = sorted(sample(variables, 4))

            # randomly determine negations
            pos = tuple(v for v in constraint_variables if random() > .5)
            neg = tuple(v for v in constraint_variables if v not in pos)

            const = sat2in4(pos=pos, neg=neg, vartype=vartype)

            constraints.add(const)

    for const in constraints:
        csp.add_constraint(const)

    # in case any variables didn't make it in
    for v in variables:
        csp.add_variable(v)

    return csp


def random_xorsat(num_variables, num_clauses, vartype=dimod.BINARY, satisfiable=True):
    """Random XOR constraint satisfaction problem.

    Args:
        num_variables (integer): Number of variables (at least three).
        num_clauses (integer): Number of constraints that together constitute the
            constraint satisfaction problem.
        vartype (Vartype, optional, default='BINARY'): Variable type. Accepted
            input values:

            * Vartype.SPIN, 'SPIN', {-1, 1}
            * Vartype.BINARY, 'BINARY', {0, 1}
        satisfiable (bool, optional, default=True): True if the CSP can be satisfied.

    Returns:
        CSP (:obj:`.ConstraintSatisfactionProblem`): CSP that is satisfied when its variables
        are assigned values that satisfy a XOR satisfiability problem.

    Examples:
        This example creates a CSP with 5 variables and two random constraints and checks
        whether a particular assignment of variables satisifies it.

        >>> import dwavebinarycsp
        >>> import dwavebinarycsp.factories as sat
        >>> csp = sat.random_xorsat(5, 2)
        >>> csp.constraints    # doctest: +SKIP
        [Constraint.from_configurations(frozenset({(1, 0, 0), (1, 1, 1), (0, 1, 0), (0, 0, 1)}), (4, 3, 0),
         Vartype.BINARY, name='XOR (0 flipped)'),
         Constraint.from_configurations(frozenset({(1, 1, 0), (0, 1, 1), (0, 0, 0), (1, 0, 1)}), (2, 0, 4),
         Vartype.BINARY, name='XOR (2 flipped) (0 flipped)')]
        >>> csp.check({0: 1, 1: 0, 2: 0, 3: 1, 4: 1})       # doctest: +SKIP
        True

    """
    if num_variables < 3:
        raise ValueError("a xor problem needs at least 3 variables")
    if num_clauses > 8 * _nchoosek(num_variables, 3):  # 8 different negation patterns
        raise ValueError("too many clauses")

    # also checks the vartype argument
    csp = ConstraintSatisfactionProblem(vartype)

    variables = list(range(num_variables))

    constraints = set()

    if satisfiable:
        values = tuple(vartype.value)
        planted_solution = {v: choice(values) for v in variables}

        configurations = [(0, 0, 0), (0, 1, 1), (1, 0, 1), (1, 1, 0)]

        while len(constraints) < num_clauses:
            # because constraints are hashed on configurations/variables, and because the inputs
            # to xor can be swapped without loss of generality, we can order them
            x, y, z = sample(variables, 3)
            if y > x:
                x, y = y, x

            # get the constraint
            const = xor_gate([x, y, z], vartype=vartype)

            # pick (uniformly) a configuration and determine which variables we need to negate to
            # match the chosen configuration
            config = choice(configurations)

            for idx, v in enumerate(const.variables):
                if config[idx] != (planted_solution[v] > 0):
                    const.flip_variable(v)

            assert const.check(planted_solution)

            constraints.add(const)
    else:
        while len(constraints) < num_clauses:
            # because constraints are hashed on configurations/variables, and because the inputs
            # to xor can be swapped without loss of generality, we can order them
            x, y, z = sample(variables, 3)
            if y > x:
                x, y = y, x

            # get the constraint
            const = xor_gate([x, y, z], vartype=vartype)

            # randomly flip each variable in the constraint
            for idx, v in enumerate(const.variables):
                if random() > .5:
                    const.flip_variable(v)

            assert const.check(planted_solution)

            constraints.add(const)

    for const in constraints:
        csp.add_constraint(const)

    # in case any variables didn't make it in
    for v in variables:
        csp.add_variable(v)

    return csp


def _nchoosek(n, k):
    return reduce(mul, range(n, n - k, -1), 1) // factorial(k)
