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
"""
Constraints can sometimes be reduced into several smaller constraints.
"""

import itertools

from collections import defaultdict


def irreducible_components(constraint):
    """Determine the sets of variables that are irreducible.

    Let V(C) denote the variables of constraint C. For a configuration x, let x|A denote the
    restriction of the configuration to the variables of A. Constraint C is reducible if there
    is a partition of V(C) into nonempty subsets A and B, and two constraints C_A and C_B, with
    V(C_A) = A and C_B V(C_B) = B, such that a configuration x is feasible in C if and only if x|A
    is feasible in C_A and x|B is feasible in C_B. A constraint is irreducible if it is not
    reducible.

    Args:
        constraint (:obj:`.Constraint`):
            Constraint to attempt to reduce.

    Returns:
        list[tuple]: List of tuples in which each tuple is a set of variables that is irreducible.

    Examples:
        This example reduces a constraint, created by specifying its valid configurations, to two
        constraints. The original constraint, that valid configurations for a,b,c are 0,0,1 and
        1,1,1, can be represented by two reduced constraints, for example, (c=1) & (a=b). For
        comparison, an attempt to reduce a constraint representing an AND gate fails to find a
        valid reduction.

        >>> import dwavebinarycsp
        >>> const = dwavebinarycsp.Constraint.from_configurations([(0, 0, 1), (1, 1, 1)],
        ...                                                       ['a', 'b', 'c'], dwavebinarycsp.BINARY)
        >>> dwavebinarycsp.irreducible_components(const)
        [('c',), ('a', 'b')]
        >>> const_and = dwavebinarycsp.Constraint.from_configurations([(0, 0, 0), (0, 1, 0), (1, 0, 0), (1, 1, 1)],
        ...                                                           ['a', 'b', 'c'], dwavebinarycsp.BINARY)
        >>> dwavebinarycsp.irreducible_components(const_and)
        [('a', 'b', 'c')]

    """

    # developer note: we could calculate the correlation on the variables and thereby reduce the
    # number of subsets we need to check in the next step.

    return _irreducible_components(constraint.configurations, constraint.variables)


def _irreducible_components(configurations, variables):

    num_variables = len(variables)

    # if len(configurations) <= 1:
    #     # if there is only one configuration then it is irreducible
    #     return [variables]

    # for every not-trivial subset (and it's complement), check if the contraint
    # is composed of the product of complement and subset
    # subset and complement are defined over the indices in the configurations for simplicity
    for i in range(1, num_variables // 2 + 1):
        for subset in itertools.combinations(range(num_variables), i):
            complement = tuple(v for v in range(num_variables) if v not in subset)

            # by using sets we only keep the unique configurations
            subset_configurations = {tuple(config[v] for v in subset) for config in configurations}
            complement_configurations = {tuple(config[v] for v in complement) for config in configurations}

            if len(configurations) == len(subset_configurations) * len(complement_configurations):

                subset_variables = tuple(variables[v] for v in subset)
                complement_variables = tuple(variables[v] for v in complement)

                subset_components = _irreducible_components(subset_configurations, subset_variables)
                complement_components = _irreducible_components(complement_configurations, complement_variables)

                return subset_components + complement_components

    return [variables]
