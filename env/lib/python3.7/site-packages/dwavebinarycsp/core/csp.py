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
Constraint satisfaction problems require that all a problem's variables be assigned
values, out of a finite domain, that result in the satisfying of all constraints.
The :class:`ConstraintSatisfactionProblem` class aggregates all constraints and variables
defined for a problem and provides functionality to assist in problem solution, such
as verifying whether a candidate solution satisfies the constraints.
"""
from collections import Callable, Iterable, defaultdict

import dimod

from dwavebinarycsp.core.constraint import Constraint


class ConstraintSatisfactionProblem(object):
    """A constraint satisfaction problem.

    Args:
        vartype (:class:`~dimod.Vartype`/str/set):
            Variable type for the binary quadratic model. Supported values are:

            * :attr:`~dimod.Vartype.SPIN`, ``'SPIN'``, ``{-1, 1}``
            * :attr:`~dimod.Vartype.BINARY`, ``'BINARY'``, ``{0, 1}``

    Attributes:
        constraints (list[:obj:`.Constraint`]):
            Constraints that together constitute the constraint satisfaction problem. Valid solutions
            satisfy all of the constraints.

        variables (dict[variable, list[:obj:`.Constraint`]]):
            Variables of the constraint satisfaction problem as a dict, where keys are the variables
            and values a list of all of constraints associated with the variable.

        vartype (:class:`dimod.Vartype`):
            Enumeration of valid variable types. Supported values are :attr:`~dimod.Vartype.SPIN`
            or :attr:`~dimod.Vartype.BINARY`. If `vartype` is SPIN, variables can be assigned -1 or 1;
            if BINARY, variables can be assigned 0 or 1.

    Example:
        This example creates a binary-valued constraint satisfaction problem, adds two constraints,
        :math:`a = b` and :math:`b \\ne c`, and tests :math:`a,b,c = 1,1,0`.

        >>> import dwavebinarycsp
        >>> import operator
        >>> csp = dwavebinarycsp.ConstraintSatisfactionProblem('BINARY')
        >>> csp.add_constraint(operator.eq, ['a', 'b'])
        >>> csp.add_constraint(operator.ne, ['b', 'c'])
        >>> csp.check({'a': 1, 'b': 1, 'c': 0})
        True

    """
    @dimod.decorators.vartype_argument('vartype')
    def __init__(self, vartype):
        self.vartype = vartype
        self.constraints = []
        self.variables = defaultdict(list)

    def __len__(self):
        return self.constraints.__len__()

    def add_constraint(self, constraint, variables=tuple()):
        """Add a constraint.

        Args:
            constraint (function/iterable/:obj:`.Constraint`):
                Constraint definition in one of the supported formats:

                1. Function, with input arguments matching the order and
                   :attr:`~.ConstraintSatisfactionProblem.vartype` type of the `variables`
                   argument, that evaluates True when the constraint is satisfied.
                2. List explicitly specifying each allowed configuration as a tuple.
                3. :obj:`.Constraint` object built either explicitly or by :mod:`dwavebinarycsp.factories`.

            variables(iterable):
                Variables associated with the constraint. Not required when `constraint` is
                a :obj:`.Constraint` object.

        Examples:
            This example defines a function that evaluates True when the constraint is satisfied.
            The function's input arguments match the order and type of the `variables` argument.

            >>> import dwavebinarycsp
            >>> csp = dwavebinarycsp.ConstraintSatisfactionProblem(dwavebinarycsp.BINARY)
            >>> def all_equal(a, b, c):  # works for both dwavebinarycsp.BINARY and dwavebinarycsp.SPIN
            ...     return (a == b) and (b == c)
            >>> csp.add_constraint(all_equal, ['a', 'b', 'c'])
            >>> csp.check({'a': 0, 'b': 0, 'c': 0})
            True
            >>> csp.check({'a': 0, 'b': 0, 'c': 1})
            False

            This example explicitly lists allowed configurations.

            >>> import dwavebinarycsp
            >>> csp = dwavebinarycsp.ConstraintSatisfactionProblem(dwavebinarycsp.SPIN)
            >>> eq_configurations = {(-1, -1), (1, 1)}
            >>> csp.add_constraint(eq_configurations, ['v0', 'v1'])
            >>> csp.check({'v0': -1, 'v1': +1})
            False
            >>> csp.check({'v0': -1, 'v1': -1})
            True

            This example uses a :obj:`.Constraint` object built by :mod:`dwavebinarycsp.factories`.

            >>> import dwavebinarycsp
            >>> import dwavebinarycsp.factories.constraint.gates as gates
            >>> csp = dwavebinarycsp.ConstraintSatisfactionProblem(dwavebinarycsp.BINARY)
            >>> csp.add_constraint(gates.and_gate(['a', 'b', 'c']))  # add an AND gate
            >>> csp.add_constraint(gates.xor_gate(['a', 'c', 'd']))  # add an XOR gate
            >>> csp.check({'a': 1, 'b': 0, 'c': 0, 'd': 1})
            True

        """
        if isinstance(constraint, Constraint):
            if variables and (tuple(variables) != constraint.variables):
                raise ValueError("mismatched variables and Constraint")
        elif isinstance(constraint, Callable):
            constraint = Constraint.from_func(constraint, variables, self.vartype)
        elif isinstance(constraint, Iterable):
            constraint = Constraint.from_configurations(constraint, variables, self.vartype)
        else:
            raise TypeError("Unknown constraint type given")

        self.constraints.append(constraint)
        for v in constraint.variables:
            self.variables[v].append(constraint)

    def add_variable(self, v):
        """Add a variable.

        Args:
            v (variable):
                Variable in the constraint satisfaction problem. May be of any type that
                can be a dict key.

        Examples:
            This example adds two variables, one of which is already used in a constraint
            of the constraint satisfaction problem.

            >>> import dwavebinarycsp
            >>> import operator
            >>> csp = dwavebinarycsp.ConstraintSatisfactionProblem(dwavebinarycsp.SPIN)
            >>> csp.add_constraint(operator.eq, ['a', 'b'])
            >>> csp.add_variable('a')  # does nothing, already added as part of the constraint
            >>> csp.add_variable('c')
            >>> csp.check({'a': -1, 'b': -1, 'c': 1})
            True
            >>> csp.check({'a': -1, 'b': -1, 'c': -1})
            True

        """
        self.variables[v]  # because defaultdict will create it if it's not there

    def check(self, solution):
        """Check that a solution satisfies all of the constraints.

        Args:
            solution (container):
                An assignment of values for the variables in the constraint satisfaction problem.

        Returns:
            bool: True if the solution satisfies all of the constraints; False otherwise.

        Examples:
            This example creates a binary-valued constraint satisfaction problem, adds
            two logic gates implementing Boolean constraints, :math:`c = a \wedge b`
            and :math:`d = a \oplus c`, and verifies that the combined problem is satisfied
            for a given assignment.

            >>> import dwavebinarycsp
            >>> import dwavebinarycsp.factories.constraint.gates as gates
            >>> csp = dwavebinarycsp.ConstraintSatisfactionProblem(dwavebinarycsp.BINARY)
            >>> csp.add_constraint(gates.and_gate(['a', 'b', 'c']))  # add an AND gate
            >>> csp.add_constraint(gates.xor_gate(['a', 'c', 'd']))  # add an XOR gate
            >>> csp.check({'a': 1, 'b': 0, 'c': 0, 'd': 1})
            True

        """
        return all(constraint.check(solution) for constraint in self.constraints)

    def fix_variable(self, v, value):
        """Fix the value of a variable and remove it from the constraint satisfaction problem.

        Args:
            v (variable):
                Variable to be fixed in the constraint satisfaction problem.

            value (int):
                Value assigned to the variable. Values must match the
                :attr:`~.ConstraintSatisfactionProblem.vartype` of the constraint
                satisfaction problem.

        Examples:
            This example creates a spin-valued constraint satisfaction problem, adds two constraints,
            :math:`a = b` and :math:`b \\ne c`, and fixes variable b to +1.

            >>> import dwavebinarycsp
            >>> import operator
            >>> csp = dwavebinarycsp.ConstraintSatisfactionProblem(dwavebinarycsp.SPIN)
            >>> csp.add_constraint(operator.eq, ['a', 'b'])
            >>> csp.add_constraint(operator.ne, ['b', 'c'])
            >>> csp.check({'a': +1, 'b': +1, 'c': -1})
            True
            >>> csp.check({'a': -1, 'b': -1, 'c': +1})
            True
            >>> csp.fix_variable('b', +1)
            >>> csp.check({'a': +1, 'b': +1, 'c': -1})  # 'b' is ignored
            True
            >>> csp.check({'a': -1, 'b': -1, 'c': +1})
            False
            >>> csp.check({'a': +1, 'c': -1})
            True
            >>> csp.check({'a': -1, 'c': +1})
            False

        """
        if v not in self.variables:
            raise ValueError("given variable {} is not part of the constraint satisfaction problem".format(v))

        for constraint in self.variables[v]:
            constraint.fix_variable(v, value)

        del self.variables[v]  # delete the variable


CSP = ConstraintSatisfactionProblem
"""An alias for :class:`.ConstraintSatisfactionProblem`."""
