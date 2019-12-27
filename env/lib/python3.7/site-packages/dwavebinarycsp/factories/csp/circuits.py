# encoding: utf-8
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

from collections import defaultdict

import dimod

from dwavebinarycsp.core.csp import ConstraintSatisfactionProblem
from dwavebinarycsp.factories.constraint.gates import and_gate, halfadder_gate, fulladder_gate

__all__ = ['multiplication_circuit']


def multiplication_circuit(nbit, vartype=dimod.BINARY):
    """Multiplication circuit constraint satisfaction problem.

    A constraint satisfaction problem that represents the binary multiplication :math:`ab=p`,
    where the multiplicands are binary variables of length `nbit`; for example,
    :math:`2^ma_{nbit} + ... + 4a_2 + 2a_1 + a0`.

    The square below shows a graphic representation of the circuit::

      ________________________________________________________________________________
      |                                         and20         and10         and00    |
      |                                           |             |             |      |
      |                           and21         add11──and11  add01──and01    |      |
      |                             |┌───────────┘|┌───────────┘|             |      |
      |             and22         add12──and12  add02──and02    |             |      |
      |               |┌───────────┘|┌───────────┘|             |             |      |
      |             add13─────────add03           |             |             |      |
      |  ┌───────────┘|             |             |             |             |      |
      | p5            p4            p3            p2            p1            p0     |
      --------------------------------------------------------------------------------

    Args:
        nbit (int): Number of bits in the multiplicands.
        vartype (Vartype, optional, default='BINARY'): Variable type. Accepted
            input values:

            * Vartype.SPIN, 'SPIN', {-1, 1}
            * Vartype.BINARY, 'BINARY', {0, 1}

    Returns:
        CSP (:obj:`.ConstraintSatisfactionProblem`): CSP that is satisfied when variables
        :math:`a,b,p` are assigned values that correctly solve binary multiplication :math:`ab=p`.

    Examples:
        This example creates a multiplication circuit CSP that multiplies two 3-bit numbers,
        which is then formulated as a binary quadratic model (BQM). It fixes the multiplacands
        as :math:`a=5, b=3` (:math:`101` and :math:`011`) and uses a simulated annealing sampler
        to find the product, :math:`p=15` (:math:`001111`).

        >>> import dwavebinarycsp
        >>> from dwavebinarycsp.factories.csp.circuits import multiplication_circuit
        >>> import neal
        >>> csp = multiplication_circuit(3)
        >>> bqm = dwavebinarycsp.stitch(csp)
        >>> bqm.fix_variable('a0', 1); bqm.fix_variable('a1', 0); bqm.fix_variable('a2', 1)
        >>> bqm.fix_variable('b0', 1); bqm.fix_variable('b1', 1); bqm.fix_variable('b2', 0)
        >>> sampler = neal.SimulatedAnnealingSampler()
        >>> response = sampler.sample(bqm)
        >>> p = next(response.samples(n=1, sorted_by='energy'))
        >>> print(p['p5'], p['p4'], p['p3'], p['p2'], p['p1'], p['p0'])    # doctest: +SKIP
        0 0 1 1 1 1

    """

    if nbit < 1:
        raise ValueError("num_multiplier_bits, num_multiplicand_bits must be positive integers")

    num_multiplier_bits = num_multiplicand_bits = nbit

    # also checks the vartype argument
    csp = ConstraintSatisfactionProblem(vartype)

    # throughout, we will use the following convention:
    #   i to refer to the bits of the multiplier
    #   j to refer to the bits of the multiplicand
    #   k to refer to the bits of the product

    # create the variables corresponding to the input and output wires for the circuit
    a = {i: 'a%d' % i for i in range(nbit)}
    b = {j: 'b%d' % j for j in range(nbit)}
    p = {k: 'p%d' % k for k in range(nbit + nbit)}

    # we will want to store the internal variables somewhere
    AND = defaultdict(dict)  # the output of the AND gate associated with ai, bj is stored in AND[i][j]
    SUM = defaultdict(dict)  # the sum of the ADDER gate associated with ai, bj is stored in SUM[i][j]
    CARRY = defaultdict(dict)  # the carry of the ADDER gate associated with ai, bj is stored in CARRY[i][j]

    # we follow a shift adder
    for i in range(num_multiplier_bits):
        for j in range(num_multiplicand_bits):

            ai = a[i]
            bj = b[j]

            if i == 0 and j == 0:
                # in this case there are no inputs from lower bits, so our only input is the AND
                # gate. And since we only have one bit to add, we don't need an adder, no have a
                # carry out
                andij = AND[i][j] = p[0]

                gate = and_gate([ai, bj, andij], vartype=vartype, name='AND(%s, %s) = %s' % (ai, bj, andij))
                csp.add_constraint(gate)

                continue

            # we always need an AND gate
            andij = AND[i][j] = 'and%s,%s' % (i, j)

            gate = and_gate([ai, bj, andij], vartype=vartype, name='AND(%s, %s) = %s' % (ai, bj, andij))
            csp.add_constraint(gate)

            # the number of inputs will determine the type of adder
            inputs = [andij]

            # determine if there is a carry in
            if i - 1 in CARRY and j in CARRY[i - 1]:
                inputs.append(CARRY[i - 1][j])

            # determine if there is a sum in
            if i - 1 in SUM and j + 1 in SUM[i - 1]:
                inputs.append(SUM[i - 1][j + 1])

            # ok, add create adders if necessary
            if len(inputs) == 1:
                # we don't need an adder and we don't have a carry
                SUM[i][j] = andij
            elif len(inputs) == 2:
                # we need a HALFADDER so we have a sum and a carry

                if j == 0:
                    sumij = SUM[i][j] = p[i]
                else:
                    sumij = SUM[i][j] = 'sum%d,%d' % (i, j)

                carryij = CARRY[i][j] = 'carry%d,%d' % (i, j)

                name = 'HALFADDER(%s, %s) = %s, %s' % (inputs[0], inputs[1], sumij, carryij)
                gate = halfadder_gate([inputs[0], inputs[1], sumij, carryij], vartype=vartype, name=name)
                csp.add_constraint(gate)
            else:
                assert len(inputs) == 3, 'unexpected number of inputs'

                # we need a FULLADDER so we have a sum and a carry

                if j == 0:
                    sumij = SUM[i][j] = p[i]
                else:
                    sumij = SUM[i][j] = 'sum%d,%d' % (i, j)

                carryij = CARRY[i][j] = 'carry%d,%d' % (i, j)

                name = 'FULLADDER(%s, %s, %s) = %s, %s' % (inputs[0], inputs[1], inputs[2], sumij, carryij)
                gate = fulladder_gate([inputs[0], inputs[1], inputs[2], sumij, carryij], vartype=vartype, name=name)
                csp.add_constraint(gate)

    # now we have a final row of full adders
    for col in range(nbit - 1):
        inputs = [CARRY[nbit - 1][col], SUM[nbit - 1][col + 1]]

        if col == 0:
            sumout = p[nbit + col]
            carryout = CARRY[nbit][col] = 'carry%d,%d' % (nbit, col)

            name = 'HALFADDER(%s, %s) = %s, %s' % (inputs[0], inputs[1], sumout, carryout)
            gate = halfadder_gate([inputs[0], inputs[1], sumout, carryout], vartype=vartype, name=name)
            csp.add_constraint(gate)

            continue

        inputs.append(CARRY[nbit][col - 1])

        sumout = p[nbit + col]
        if col < nbit - 2:
            carryout = CARRY[nbit][col] = 'carry%d,%d' % (nbit, col)
        else:
            carryout = p[2 * nbit - 1]

        name = 'FULLADDER(%s, %s, %s) = %s, %s' % (inputs[0], inputs[1], inputs[2], sumout, carryout)
        gate = fulladder_gate([inputs[0], inputs[1], inputs[2], sumout, carryout], vartype=vartype, name=name)
        csp.add_constraint(gate)

    return csp
