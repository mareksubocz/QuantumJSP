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

import itertools

import dimod

from dwavebinarycsp.core.constraint import Constraint

__all__ = ['sat2in4']


@dimod.decorators.vartype_argument('vartype')
def sat2in4(pos, neg=tuple(), vartype=dimod.BINARY, name='2-in-4'):
    """Two-in-four (2-in-4) satisfiability.

    Args:
        pos (iterable):
            Variable labels, as an iterable, for non-negated variables of the constraint.
            Exactly four variables are specified by `pos` and `neg` together.
        neg (tuple):
            Variable labels, as an iterable, for negated variables of the constraint.
            Exactly four variables are specified by `pos` and `neg` together.
        vartype (Vartype, optional, default='BINARY'): Variable type. Accepted
            input values:

            * Vartype.SPIN, 'SPIN', {-1, 1}
            * Vartype.BINARY, 'BINARY', {0, 1}
        name (str, optional, default='2-in-4'): Name for the constraint.

    Returns:
        Constraint(:obj:`.Constraint`): Constraint that is satisfied when its variables are
        assigned values that satisfy a two-in-four satisfiability problem.

    Examples:
        >>> import dwavebinarycsp
        >>> import dwavebinarycsp.factories.constraint.sat as sat
        >>> csp = dwavebinarycsp.ConstraintSatisfactionProblem(dwavebinarycsp.BINARY)
        >>> csp.add_constraint(sat.sat2in4(['w', 'x', 'y', 'z'], vartype='BINARY', name='sat1'))
        >>> csp.check({'w': 1, 'x': 1, 'y': 0, 'z': 0})
        True

    """
    pos = tuple(pos)
    neg = tuple(neg)

    variables = pos + neg

    if len(variables) != 4:
        raise ValueError("")

    if neg and (len(neg) < 4):
        # because 2-in-4 sat is symmetric, all negated is the same as none negated

        const = sat2in4(pos=variables, vartype=vartype)  # make one that has no negations
        for v in neg:
            const.flip_variable(v)
            const.name = name  # overwrite the name directly

        return const

    # we can just construct them directly for speed
    if vartype is dimod.BINARY:
        configurations = frozenset([(0, 0, 1, 1),
                                    (0, 1, 0, 1),
                                    (1, 0, 0, 1),
                                    (0, 1, 1, 0),
                                    (1, 0, 1, 0),
                                    (1, 1, 0, 0)])
    else:
        # SPIN, vartype is checked by the decorator
        configurations = frozenset([(-1, -1, +1, +1),
                                    (-1, +1, -1, +1),
                                    (+1, -1, -1, +1),
                                    (-1, +1, +1, -1),
                                    (+1, -1, +1, -1),
                                    (+1, +1, -1, -1)])

    def func(a, b, c, d):
        if a == b:
            return (b != c) and (c == d)
        elif a == c:
            # a != b
            return b == d
        else:
            # a != b, a != c => b == c
            return a == d

    return Constraint(func, configurations, variables, vartype=vartype, name=name)
