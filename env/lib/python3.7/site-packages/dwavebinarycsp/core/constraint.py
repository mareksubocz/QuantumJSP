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
Solutions to a constraint satisfaction problem must satisfy certains conditions, the
constraints of the problem, such as equality and inequality constraints.
The :class:`Constraint` class defines constraints and provides functionality to
assist in constraint definition, such as verifying whether a candidate solution satisfies
a constraint.
"""
import itertools

from collections import Sized, Callable

import dimod

from dwavebinarycsp.exceptions import UnsatError

__all__ = ['Constraint']


class Constraint(Sized):
    """A constraint.

    Attributes:
        variables (tuple):
            Variables associated with the constraint.

        func (function):
            Function that returns True for configurations of variables that satisfy the
            constraint. Inputs to the function are ordered by :attr:`~Constraint.variables`.

        configurations (frozenset[tuple]):
            Valid configurations of the variables. Each configuration is a tuple of variable
            assignments ordered by :attr:`~Constraint.variables`.

        vartype (:class:`dimod.Vartype`):
            Variable type for the constraint. Accepted input values:

            * :attr:`~dimod.Vartype.SPIN`, ``'SPIN'``, ``{-1, 1}``
            * :attr:`~dimod.Vartype.BINARY`, ``'BINARY'``, ``{0, 1}``

        name (str):
            Name for the constraint. If not provided on construction, defaults to
            'Constraint'.

    Examples:
        This example defines a constraint, named "plus1", based on a function that
        is True for :math:`(y1,y0) = (x1,x0)+1` on binary variables, and demonstrates
        some of the constraint's functionality.

        >>> import dwavebinarycsp
        >>> def plus_one(y1, y0, x1, x0):  # y=x++ for two bit binary numbers
        ...     return (y1, y0, x1, x0) in [(0, 1, 0, 0), (1, 0, 0, 1), (1, 1, 1, 0)]
        ...
        >>> const = dwavebinarycsp.Constraint.from_func(
        ...               plus_one,
        ...               ['out1', 'out0', 'in1', 'in0'],
        ...               dwavebinarycsp.BINARY,
        ...               name='plus1')
        >>> print(const.name)   # Check constraint defined as intended
        plus1
        >>> len(const)
        4
        >>> in0, in1, out0, out1 = 0, 0, 1, 0
        >>> const.func(out1, out0, in1, in0)   # Order matches variables
        True

        This example defines a constraint based on specified valid configurations
        that represents an AND gate for spin variables, and demonstrates some of
        the constraint's functionality.

        >>> import dwavebinarycsp
        >>> const = dwavebinarycsp.Constraint.from_configurations(
        ...           [(-1, -1, -1), (-1, -1, 1), (-1, 1, -1), (1, 1, 1)],
        ...           ['y', 'x1', 'x2'],
        ...           dwavebinarycsp.SPIN)
        >>> print(const.name)   # Check constraint defined as intended
        Constraint
        >>> isinstance(const, dwavebinarycsp.core.constraint.Constraint)
        True
        >>> (-1, 1, -1) in const.configurations   # Order matches variables: y,x1,x2
        True

    """

    __slots__ = ('vartype', 'variables', 'configurations', 'func', 'name')

    #
    # Construction
    #

    @dimod.decorators.vartype_argument('vartype')
    def __init__(self, func, configurations, variables, vartype, name=None):

        self.vartype = vartype  # checked by decorator

        if not isinstance(func, Callable):
            raise TypeError("expected input 'func' to be callable")
        self.func = func

        self.variables = variables = tuple(variables)
        num_variables = len(variables)

        if not isinstance(configurations, frozenset):
            configurations = frozenset(tuple(config) for config in configurations)  # cast to tuples
        if len(configurations) == 0 and num_variables > 0:
            raise ValueError("constraint must have at least one feasible configuration")
        if not all(len(config) == num_variables for config in configurations):
            raise ValueError("all configurations should be of the same length")
        if len(vartype.value.union(*configurations)) >= 3:
            raise ValueError("configurations do not match vartype")
        self.configurations = configurations

        if name is None:
            name = 'Constraint'
        self.name = name

    @classmethod
    @dimod.decorators.vartype_argument('vartype')
    def from_func(cls, func, variables, vartype, name=None):
        """Construct a constraint from a validation function.

        Args:
            func (function):
                Function that evaluates True when the variables satisfy the constraint.

            variables (iterable):
                Iterable of variable labels.

            vartype (:class:`~dimod.Vartype`/str/set):
                Variable type for the constraint. Accepted input values:

                * :attr:`~dimod.Vartype.SPIN`, ``'SPIN'``, ``{-1, 1}``
                * :attr:`~dimod.Vartype.BINARY`, ``'BINARY'``, ``{0, 1}``

            name (string, optional, default='Constraint'):
                Name for the constraint.

        Examples:
            This example creates a constraint that binary variables `a` and `b`
            are not equal.

            >>> import dwavebinarycsp
            >>> import operator
            >>> const = dwavebinarycsp.Constraint.from_func(operator.ne, ['a', 'b'], 'BINARY')
            >>> print(const.name)
            Constraint
            >>> (0, 1) in const.configurations
            True

            This example creates a constraint that :math:`out = NOT(x)`
            for spin variables.

            >>> import dwavebinarycsp
            >>> def not_(y, x):  # y=NOT(x) for spin variables
            ...     return (y == -x)
            ...
            >>> const = dwavebinarycsp.Constraint.from_func(
            ...               not_,
            ...               ['out', 'in'],
            ...               {1, -1},
            ...               name='not_spin')
            >>> print(const.name)
            not_spin
            >>> (1, -1) in const.configurations
            True

        """
        variables = tuple(variables)

        configurations = frozenset(config
                                   for config in itertools.product(vartype.value, repeat=len(variables))
                                   if func(*config))

        return cls(func, configurations, variables, vartype, name)

    @classmethod
    def from_configurations(cls, configurations, variables, vartype, name=None):
        """Construct a constraint from valid configurations.

        Args:
            configurations (iterable[tuple]):
                Valid configurations of the variables. Each configuration is a tuple of variable
                assignments ordered by :attr:`~Constraint.variables`.

            variables (iterable):
                Iterable of variable labels.

            vartype (:class:`~dimod.Vartype`/str/set):
                Variable type for the constraint. Accepted input values:

                * :attr:`~dimod.Vartype.SPIN`, ``'SPIN'``, ``{-1, 1}``
                * :attr:`~dimod.Vartype.BINARY`, ``'BINARY'``, ``{0, 1}``

            name (string, optional, default='Constraint'):
                Name for the constraint.

        Examples:

            This example creates a constraint that variables `a` and `b` are not equal.

            >>> import dwavebinarycsp
            >>> const = dwavebinarycsp.Constraint.from_configurations([(0, 1), (1, 0)],
            ...                   ['a', 'b'], dwavebinarycsp.BINARY)
            >>> print(const.name)
            Constraint
            >>> (0, 0) in const.configurations   # Order matches variables: a,b
            False

            This example creates a constraint based on specified valid configurations
            that represents an OR gate for spin variables.

            >>> import dwavebinarycsp
            >>> const = dwavebinarycsp.Constraint.from_configurations(
            ...           [(-1, -1, -1), (1, -1, 1), (1, 1, -1), (1, 1, 1)],
            ...           ['y', 'x1', 'x2'],
            ...           dwavebinarycsp.SPIN, name='or_spin')
            >>> print(const.name)
            or_spin
            >>> (1, 1, -1) in const.configurations   # Order matches variables: y,x1,x2
            True

        """
        def func(*args): return args in configurations

        return cls(func, configurations, variables, vartype, name)

    #
    # Special Methods
    #

    def __len__(self):
        """The number of variables."""
        return self.variables.__len__()

    def __repr__(self):
        return "Constraint.from_configurations({}, {}, {}, name='{}')".format(self.configurations,
                                                                              self.variables,
                                                                              self.vartype,
                                                                              self.name)

    def __eq__(self, constraint):
        return self.variables == constraint.variables and self.configurations == constraint.configurations

    def __ne__(self, constraint):
        return not self.__eq__(constraint)

    def __hash__(self):
        # uniquely defined by configurations/variables
        return hash((self.configurations, self.variables))

    def __or__(self, const):
        if not isinstance(const, Constraint):
            raise TypeError("unsupported operand type(s) for |: 'Constraint' and '{}'".format(type(const).__name__))

        if const and self and self.vartype is not const.vartype:
            raise ValueError("operand | only meaningful for Constraints with matching vartype")

        shared_variables = set(self.variables).intersection(const.variables)

        # dev note: if they share all variables, we could just act on the configurations

        if not shared_variables:
            # in this case we just append
            variables = self.variables + const.variables

            n = len(self)  # need to know how to divide up the variables

            def union(*args):
                return self.func(*args[:n]) or const.func(*args[n:])

            return self.from_func(union, variables, self.vartype, name='{} | {}'.format(self.name, const.name))

        variables = self.variables + tuple(v for v in const.variables if v not in shared_variables)

        def union(*args):
            solution = dict(zip(variables, args))
            return self.check(solution) or const.check(solution)

        return self.from_func(union, variables, self.vartype, name='{} | {}'.format(self.name, const.name))

    def __and__(self, const):
        if not isinstance(const, Constraint):
            raise TypeError("unsupported operand type(s) for &: 'Constraint' and '{}'".format(type(const).__name__))

        if const and self and self.vartype is not const.vartype:
            raise ValueError("operand & only meaningful for Constraints with matching vartype")

        shared_variables = set(self.variables).intersection(const.variables)

        # dev note: if they share all variables, we could just act on the configurations
        name = '{} & {}'.format(self.name, const.name)

        if not shared_variables:
            # in this case we just append
            variables = self.variables + const.variables

            n = len(self)  # need to know how to divide up the variables

            def intersection(*args):
                return self.func(*args[:n]) and const.func(*args[n:])

            return self.from_func(intersection, variables, self.vartype, name=name)

        variables = self.variables + tuple(v for v in const.variables if v not in shared_variables)

        def intersection(*args):
            solution = dict(zip(variables, args))
            return self.check(solution) and const.check(solution)

        return self.from_func(intersection, variables, self.vartype, name=name)

    #
    # verification
    #

    def check(self, solution):
        """Check that a solution satisfies the constraint.

        Args:
            solution (container):
                An assignment for the variables in the constraint.

        Returns:
            bool: True if the solution satisfies the constraint; otherwise False.

        Examples:
            This example creates a constraint that :math:`a \\ne b` on binary variables
            and tests it for two candidate solutions, with additional unconstrained
            variable c.

            >>> import dwavebinarycsp
            >>> const = dwavebinarycsp.Constraint.from_configurations([(0, 1), (1, 0)],
            ...             ['a', 'b'], dwavebinarycsp.BINARY)
            >>> solution = {'a': 1, 'b': 1, 'c': 0}
            >>> const.check(solution)
            False
            >>> solution = {'a': 1, 'b': 0, 'c': 0}
            >>> const.check(solution)
            True

        """
        return self.func(*(solution[v] for v in self.variables))

    #
    # transformation
    #

    def fix_variable(self, v, value):
        """Fix the value of a variable and remove it from the constraint.

        Args:
            v (variable):
                Variable in the constraint to be set to a constant value.

            val (int):
                Value assigned to the variable. Values must match the :class:`.Vartype` of the
                constraint.

        Examples:
            This example creates a constraint that :math:`a \\ne b` on binary variables,
            fixes variable a to 0, and tests two candidate solutions.

            >>> import dwavebinarycsp
            >>> const = dwavebinarycsp.Constraint.from_func(operator.ne,
            ...             ['a', 'b'], dwavebinarycsp.BINARY)
            >>> const.fix_variable('a', 0)
            >>> const.check({'b': 1})
            True
            >>> const.check({'b': 0})
            False

        """
        variables = self.variables
        try:
            idx = variables.index(v)
        except ValueError:
            raise ValueError("given variable {} is not part of the constraint".format(v))

        if value not in self.vartype.value:
            raise ValueError("expected value to be in {}, received {} instead".format(self.vartype.value, value))

        configurations = frozenset(config[:idx] + config[idx + 1:]  # exclude the fixed var
                                   for config in self.configurations
                                   if config[idx] == value)

        if not configurations:
            raise UnsatError("fixing {} to {} makes this constraint unsatisfiable".format(v, value))

        variables = variables[:idx] + variables[idx + 1:]

        self.configurations = configurations
        self.variables = variables

        def func(*args): return args in configurations
        self.func = func

        self.name = '{} ({} fixed to {})'.format(self.name, v, value)

    def flip_variable(self, v):
        """Flip a variable in the constraint.

        Args:
            v (variable):
                Variable in the constraint to take the complementary value of its
                construction value.

        Examples:
            This example creates a constraint that :math:`a = b` on binary variables
            and flips variable a.

            >>> import dwavebinarycsp
            >>> const = dwavebinarycsp.Constraint.from_func(operator.eq,
            ...             ['a', 'b'], dwavebinarycsp.BINARY)
            >>> const.check({'a': 0, 'b': 0})
            True
            >>> const.flip_variable('a')
            >>> const.check({'a': 1, 'b': 0})
            True
            >>> const.check({'a': 0, 'b': 0})
            False

        """
        try:
            idx = self.variables.index(v)
        except ValueError:
            raise ValueError("variable {} is not a variable in constraint {}".format(v, self.name))

        if self.vartype is dimod.BINARY:

            original_func = self.func

            def func(*args):
                new_args = list(args)
                new_args[idx] = 1 - new_args[idx]  # negate v
                return original_func(*new_args)

            self.func = func

            self.configurations = frozenset(config[:idx] + (1 - config[idx],) + config[idx + 1:]
                                            for config in self.configurations)

        else:  # SPIN

            original_func = self.func

            def func(*args):
                new_args = list(args)
                new_args[idx] = -new_args[idx]  # negate v
                return original_func(*new_args)

            self.func = func

            self.configurations = frozenset(config[:idx] + (-config[idx],) + config[idx + 1:]
                                            for config in self.configurations)

        self.name = '{} ({} flipped)'.format(self.name, v)

    #
    # copies and projections
    #

    def copy(self):
        """Create a copy.

        Examples:
            This example copies constraint :math:`a \\ne b` and tests a solution
            on the copied constraint.

            >>> import dwavebinarycsp
            >>> import operator
            >>> const = dwavebinarycsp.Constraint.from_func(operator.ne,
            ...             ['a', 'b'], 'BINARY')
            >>> const2 = const.copy()
            >>> const2 is const
            False
            >>> const2.check({'a': 1, 'b': 1})
            False

        """
        # each object is itself immutable (except the function)
        return self.__class__(self.func, self.configurations, self.variables, self.vartype, name=self.name)

    def projection(self, variables):
        """Create a new constraint that is the projection onto a subset of the variables.

        Args:
            variables (iterable):
                Subset of the constraint's variables.

        Returns:
            :obj:`.Constraint`: A new constraint over a subset of the variables.

        Examples:

            >>> import dwavebinarycsp
            ...
            >>> const = dwavebinarycsp.Constraint.from_configurations([(0, 0), (0, 1)],
            ...                                                       ['a', 'b'],
            ...                                                       dwavebinarycsp.BINARY)
            >>> proj = const.projection(['a'])
            >>> proj.variables
            ['a']
            >>> proj.configurations
            {(0,)}

        """
        # resolve iterables or mutability problems by casting the variables to a set
        variables = set(variables)

        if not variables.issubset(self.variables):
            raise ValueError("Cannot project to variables not in the constraint.")

        idxs = [i for i, v in enumerate(self.variables) if v in variables]

        configurations = frozenset(tuple(config[i] for i in idxs) for config in self.configurations)
        variables = tuple(self.variables[i] for i in idxs)

        return self.from_configurations(configurations, variables, self.vartype)
