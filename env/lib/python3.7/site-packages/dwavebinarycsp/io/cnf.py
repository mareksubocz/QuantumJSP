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
The DIMACS format is used to encode boolean satisfiability problems in conjunctive normal form.
"""
import re

import dimod

from dwavebinarycsp import ConstraintSatisfactionProblem

_PROBLEM_REGEX = r'^p cnf (\d+) (\d+)'
_CLAUSE_REGEX = r'^-?[0-9]\d*(?:\W-?[1-9]\d*)*\W0$'


def load_cnf(fp):
    """Load a constraint satisfaction problem from a .cnf file.

    Args:
        fp (file, optional):
            `.write()`-supporting `file object`_ DIMACS CNF formatted_ file.

    Returns:
        :obj:`.ConstraintSatisfactionProblem` a binary-valued SAT problem.

    Examples:

        >>> import dwavebinarycsp as dbcsp
        ...
        >>> with open('test.cnf', 'r') as fp: # doctest: +SKIP
        ...     csp = dbcsp.cnf.load_cnf(fp)

    .. _file object: https://docs.python.org/3/glossary.html#term-file-object

    .. _formatted: http://www.satcompetition.org/2009/format-benchmarks2009.html


    """

    fp = iter(fp)  # handle lists/tuples/etc

    csp = ConstraintSatisfactionProblem(dimod.BINARY)

    # first look for the problem
    num_clauses = num_variables = 0
    problem_pattern = re.compile(_PROBLEM_REGEX)
    for line in fp:
        matches = problem_pattern.findall(line)
        if matches:
            if len(matches) > 1:
                raise ValueError
            nv, nc = matches[0]
            num_variables, num_clauses = int(nv), int(nc)
            break

    # now parse the clauses, picking up where we left off looking for the header
    clause_pattern = re.compile(_CLAUSE_REGEX)
    for line in fp:
        if clause_pattern.match(line) is not None:
            clause = [int(v) for v in line.split(' ')[:-1]]  # line ends with a trailing 0

            # -1 is the notation for NOT(1)
            variables = [abs(v) for v in clause]

            f = _cnf_or(clause)

            csp.add_constraint(f, variables)

    for v in range(1, num_variables+1):
        csp.add_variable(v)
    for v in csp.variables:
        if v > num_variables:
            msg = ("given .cnf file's header defines variables [1, {}] and {} clauses "
                   "but constraints a reference to variable {}").format(num_variables, num_clauses, v)
            raise ValueError(msg)

    if len(csp) != num_clauses:
        msg = ("given .cnf file's header defines {} "
               "clauses but the file contains {}").format(num_clauses, len(csp))
        raise ValueError(msg)

    return csp


def _cnf_or(clause):
    def f(*args):
        return any(v == int(c > 0) for v, c in zip(args, clause))
    return f
