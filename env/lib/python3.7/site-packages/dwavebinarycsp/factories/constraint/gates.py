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

import dimod

from dwavebinarycsp.core.constraint import Constraint

__all__ = ['and_gate',
           'or_gate',
           'xor_gate',
           'halfadder_gate',
           'fulladder_gate']


@dimod.decorators.vartype_argument('vartype')
def and_gate(variables, vartype=dimod.BINARY, name='AND'):
    """AND gate.

    Args:
        variables (list): Variable labels for the and gate as `[in1, in2, out]`,
            where `in1, in2` are inputs and `out` the gate's output.
        vartype (Vartype, optional, default='BINARY'): Variable type. Accepted
            input values:

            * Vartype.SPIN, 'SPIN', {-1, 1}
            * Vartype.BINARY, 'BINARY', {0, 1}
        name (str, optional, default='AND'): Name for the constraint.

    Returns:
        Constraint(:obj:`.Constraint`): Constraint that is satisfied when its variables are
        assigned values that match the valid states of an AND gate.

    Examples:
        >>> import dwavebinarycsp
        >>> import dwavebinarycsp.factories.constraint.gates as gates
        >>> csp = dwavebinarycsp.ConstraintSatisfactionProblem(dwavebinarycsp.BINARY)
        >>> csp.add_constraint(gates.and_gate(['a', 'b', 'c'], name='AND1'))
        >>> csp.check({'a': 1, 'b': 0, 'c': 0})
        True
    """

    variables = tuple(variables)

    if vartype is dimod.BINARY:
        configurations = frozenset([(0, 0, 0),
                                    (0, 1, 0),
                                    (1, 0, 0),
                                    (1, 1, 1)])

        def func(in1, in2, out): return (in1 and in2) == out

    else:
        # SPIN, vartype is checked by the decorator
        configurations = frozenset([(-1, -1, -1),
                                    (-1, +1, -1),
                                    (+1, -1, -1),
                                    (+1, +1, +1)])

        def func(in1, in2, out): return ((in1 > 0) and (in2 > 0)) == (out > 0)

    return Constraint(func, configurations, variables, vartype=vartype, name=name)


@dimod.decorators.vartype_argument('vartype')
def or_gate(variables, vartype=dimod.BINARY, name='OR'):
    """OR gate.

    Args:
        variables (list): Variable labels for the and gate as `[in1, in2, out]`,
            where `in1, in2` are inputs and `out` the gate's output.
        vartype (Vartype, optional, default='BINARY'): Variable type. Accepted
            input values:

            * Vartype.SPIN, 'SPIN', {-1, 1}
            * Vartype.BINARY, 'BINARY', {0, 1}
        name (str, optional, default='OR'): Name for the constraint.

    Returns:
        Constraint(:obj:`.Constraint`): Constraint that is satisfied when its variables are
        assigned values that match the valid states of an OR gate.

    Examples:
        >>> import dwavebinarycsp
        >>> import dwavebinarycsp.factories.constraint.gates as gates
        >>> csp = dwavebinarycsp.ConstraintSatisfactionProblem(dwavebinarycsp.SPIN)
        >>> csp.add_constraint(gates.or_gate(['x', 'y', 'z'], {-1,1}, name='OR1'))
        >>> csp.check({'x': 1, 'y': -1, 'z': 1})
        True
    """

    variables = tuple(variables)

    if vartype is dimod.BINARY:
        configs = frozenset([(0, 0, 0),
                             (0, 1, 1),
                             (1, 0, 1),
                             (1, 1, 1)])

        def func(in1, in2, out): return (in1 or in2) == out

    else:
        # SPIN, vartype is checked by the decorator
        configs = frozenset([(-1, -1, -1),
                             (-1, +1, +1),
                             (+1, -1, +1),
                             (+1, +1, +1)])

        def func(in1, in2, out): return ((in1 > 0) or (in2 > 0)) == (out > 0)

    return Constraint(func, configs, variables, vartype=vartype, name=name)


@dimod.decorators.vartype_argument('vartype')
def xor_gate(variables, vartype=dimod.BINARY, name='XOR'):
    """XOR gate.

    Args:
        variables (list): Variable labels for the and gate as `[in1, in2, out]`,
            where `in1, in2` are inputs and `out` the gate's output.
        vartype (Vartype, optional, default='BINARY'): Variable type. Accepted
            input values:

            * Vartype.SPIN, 'SPIN', {-1, 1}
            * Vartype.BINARY, 'BINARY', {0, 1}
        name (str, optional, default='XOR'): Name for the constraint.

    Returns:
        Constraint(:obj:`.Constraint`): Constraint that is satisfied when its variables are
        assigned values that match the valid states of an XOR gate.

    Examples:
        >>> import dwavebinarycsp
        >>> import dwavebinarycsp.factories.constraint.gates as gates
        >>> csp = dwavebinarycsp.ConstraintSatisfactionProblem(dwavebinarycsp.BINARY)
        >>> csp.add_constraint(gates.xor_gate(['x', 'y', 'z'], name='XOR1'))
        >>> csp.check({'x': 1, 'y': 1, 'z': 1})
        False
    """

    variables = tuple(variables)
    if vartype is dimod.BINARY:
        configs = frozenset([(0, 0, 0),
                             (0, 1, 1),
                             (1, 0, 1),
                             (1, 1, 0)])

        def func(in1, in2, out): return (in1 != in2) == out

    else:
        # SPIN, vartype is checked by the decorator
        configs = frozenset([(-1, -1, -1),
                             (-1, +1, +1),
                             (+1, -1, +1),
                             (+1, +1, -1)])

        def func(in1, in2, out): return ((in1 > 0) != (in2 > 0)) == (out > 0)

    return Constraint(func, configs, variables, vartype=vartype, name=name)


@dimod.decorators.vartype_argument('vartype')
def halfadder_gate(variables, vartype=dimod.BINARY, name='HALF_ADDER'):
    """Half adder.

    Args:
        variables (list): Variable labels for the and gate as `[in1, in2, sum, carry]`,
            where `in1, in2` are inputs to be added and `sum` and 'carry' the resultant
            outputs.
        vartype (Vartype, optional, default='BINARY'): Variable type. Accepted
            input values:

            * Vartype.SPIN, 'SPIN', {-1, 1}
            * Vartype.BINARY, 'BINARY', {0, 1}
        name (str, optional, default='HALF_ADDER'): Name for the constraint.

    Returns:
        Constraint(:obj:`.Constraint`): Constraint that is satisfied when its variables are
        assigned values that match the valid states of a Boolean half adder.

    Examples:
        >>> import dwavebinarycsp
        >>> import dwavebinarycsp.factories.constraint.gates as gates
        >>> csp = dwavebinarycsp.ConstraintSatisfactionProblem(dwavebinarycsp.BINARY)
        >>> csp.add_constraint(gates.halfadder_gate(['a', 'b', 'total', 'carry'], name='HA1'))
        >>> csp.check({'a': 1, 'b': 1, 'total': 0, 'carry': 1})
        True

    """

    variables = tuple(variables)

    if vartype is dimod.BINARY:
        configs = frozenset([(0, 0, 0, 0),
                             (0, 1, 1, 0),
                             (1, 0, 1, 0),
                             (1, 1, 0, 1)])

    else:
        # SPIN, vartype is checked by the decorator
        configs = frozenset([(-1, -1, -1, -1),
                             (-1, +1, +1, -1),
                             (+1, -1, +1, -1),
                             (+1, +1, -1, +1)])

    def func(augend, addend, sum_, carry):
        total = (augend > 0) + (addend > 0)
        if total == 0:
            return (sum_ <= 0) and (carry <= 0)
        elif total == 1:
            return (sum_ > 0) and (carry <= 0)
        elif total == 2:
            return (sum_ <= 0) and (carry > 0)
        else:
            raise ValueError("func recieved unexpected values")

    return Constraint(func, configs, variables, vartype=vartype, name=name)


@dimod.decorators.vartype_argument('vartype')
def fulladder_gate(variables, vartype=dimod.BINARY, name='FULL_ADDER'):
    """Full adder.

    Args:
        variables (list): Variable labels for the and gate as `[in1, in2, in3, sum, carry]`,
            where `in1, in2, in3` are inputs to be added and `sum` and 'carry' the resultant
            outputs.
        vartype (Vartype, optional, default='BINARY'): Variable type. Accepted
            input values:

            * Vartype.SPIN, 'SPIN', {-1, 1}
            * Vartype.BINARY, 'BINARY', {0, 1}
        name (str, optional, default='FULL_ADDER'): Name for the constraint.

    Returns:
        Constraint(:obj:`.Constraint`): Constraint that is satisfied when its variables are
        assigned values that match the valid states of a Boolean full adder.

    Examples:
        >>> import dwavebinarycsp
        >>> import dwavebinarycsp.factories.constraint.gates as gates
        >>> csp = dwavebinarycsp.ConstraintSatisfactionProblem(dwavebinarycsp.BINARY)
        >>> csp.add_constraint(gates.fulladder_gate(['a', 'b', 'c_in', 'total', 'c_out'], name='FA1'))
        >>> csp.check({'a': 1, 'b': 0, 'c_in': 1, 'total': 0, 'c_out': 1})
        True

    """

    variables = tuple(variables)

    if vartype is dimod.BINARY:
        configs = frozenset([(0, 0, 0, 0, 0),
                             (0, 0, 1, 1, 0),
                             (0, 1, 0, 1, 0),
                             (0, 1, 1, 0, 1),
                             (1, 0, 0, 1, 0),
                             (1, 0, 1, 0, 1),
                             (1, 1, 0, 0, 1),
                             (1, 1, 1, 1, 1)])

    else:
        # SPIN, vartype is checked by the decorator
        configs = frozenset([(-1, -1, -1, -1, -1),
                             (-1, -1, +1, +1, -1),
                             (-1, +1, -1, +1, -1),
                             (-1, +1, +1, -1, +1),
                             (+1, -1, -1, +1, -1),
                             (+1, -1, +1, -1, +1),
                             (+1, +1, -1, -1, +1),
                             (+1, +1, +1, +1, +1)])

    def func(in1, in2, in3, sum_, carry):
        total = (in1 > 0) + (in2 > 0) + (in3 > 0)
        if total == 0:
            return (sum_ <= 0) and (carry <= 0)
        elif total == 1:
            return (sum_ > 0) and (carry <= 0)
        elif total == 2:
            return (sum_ <= 0) and (carry > 0)
        elif total == 3:
            return (sum_ > 0) and (carry > 0)
        else:
            raise ValueError("func recieved unexpected values")

    return Constraint(func, configs, variables, vartype=vartype, name=name)
