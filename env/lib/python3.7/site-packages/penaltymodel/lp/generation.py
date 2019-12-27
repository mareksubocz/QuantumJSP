import dimod
from itertools import product
import numpy as np
from scipy.optimize import linprog

#TODO: put these values in a common penaltymodel folder
MIN_LINEAR_BIAS = -2
MAX_LINEAR_BIAS = 2
MIN_QUADRATIC_BIAS = -1
MAX_QUADRATIC_BIAS = 1
DEFAULT_GAP = 2


def get_item(dictionary, tuple_key, default_value):
    """Grab values from a dictionary using an unordered tuple as a key.

    Dictionary should not contain None, 0, or False as dictionary values.

    Args:
        dictionary: Dictionary that uses two-element tuple as keys
        tuple_key: Unordered tuple of two elements
        default_value: Value that is returned when the tuple_key is not found in the dictionary
    """
    u, v = tuple_key

    # Grab tuple-values from dictionary
    tuple1 = dictionary.get((u, v), None)
    tuple2 = dictionary.get((v, u), None)

    # Return the first value that is not {None, 0, False}
    return tuple1 or tuple2 or default_value


def _get_lp_matrix(spin_states, nodes, edges, offset_weight, gap_weight):
    """Creates an linear programming matrix based on the spin states, graph, and scalars provided.
    LP matrix:
        [spin_states, corresponding states of edges, offset_weight, gap_weight]

    Args:
        spin_states: Numpy array of spin states
        nodes: Iterable
        edges: Iterable of tuples
        offset_weight: Numpy 1-D array or number
        gap_weight: Numpy 1-D array or a number
    """
    if len(spin_states) == 0:
        return None

    # Set up an empty matrix
    n_states = len(spin_states)
    m_linear = len(nodes)
    m_quadratic = len(edges)
    matrix = np.empty((n_states, m_linear + m_quadratic + 2))   # +2 columns for offset and gap

    # Populate linear terms (i.e. spin states)
    if spin_states.ndim == 1:
        spin_states = np.expand_dims(spin_states, 1)
    matrix[:, :m_linear] = spin_states

    # Populate quadratic terms
    node_indices = dict(zip(nodes, range(m_linear)))
    for j, (u, v) in enumerate(edges):
        u_ind = node_indices[u]
        v_ind = node_indices[v]
        matrix[:, j + m_linear] = np.multiply(matrix[:, u_ind], matrix[:, v_ind])

    # Populate offset and gap columns, respectively
    matrix[:, -2] = offset_weight
    matrix[:, -1] = gap_weight
    return matrix


#TODO: check table is not empty (perhaps this check should be in bqm.stitch or as a common
# penaltymodel check)
def generate_bqm(graph, table, decision_variables,
                 linear_energy_ranges=None, quadratic_energy_ranges=None, min_classical_gap=2):
    """
    Args:
        graph: A networkx.Graph
        table: An iterable of valid spin configurations. Each configuration is a tuple of
            variable assignments ordered by `decision`.
        decision_variables: An ordered iterable of the variables in the binary quadratic model.
        linear_energy_ranges: Dictionary of the form {v: (min, max), ...} where min and
            max are the range of values allowed to v. The default range is [-2, 2].
        quadratic_energy_ranges: Dict of the form {(u, v): (min, max), ...} where min and max are
            the range of values allowed to (u, v). The default range is [-1, 1].
        min_classical_gap: A float. The minimum energy gap between the highest feasible state and
            the lowest infeasible state.
    """
    # Check for auxiliary variables in the graph
    if len(graph) != len(decision_variables):
        raise ValueError('Penaltymodel-lp does not handle problems with auxiliary variables')

    if not linear_energy_ranges:
        linear_energy_ranges = {}

    if not quadratic_energy_ranges:
        quadratic_energy_ranges = {}

    # Simplify graph naming
    # Note: nodes' and edges' order determine the column order of the LP
    nodes = decision_variables
    edges = graph.edges

    # Set variable names for lengths
    m_linear = len(nodes)                   # Number of linear biases
    m_quadratic = len(edges)                # Number of quadratic biases
    n_noted = len(table)                    # Number of spin combinations specified in the table
    n_unnoted = 2**m_linear - n_noted       # Number of spin combinations that were not specified

    # Linear programming matrix for spin states specified by 'table'
    noted_states = table.keys() if isinstance(table, dict) else table
    noted_states = list(noted_states)
    noted_matrix = _get_lp_matrix(np.asarray(noted_states), nodes, edges, 1, 0)

    # Linear programming matrix for spins states that were not specified by 'table'
    spin_states = product([-1, 1], repeat=m_linear) if m_linear > 1 else [-1, 1]
    unnoted_states = [state for state in spin_states if state not in noted_states]
    unnoted_matrix = _get_lp_matrix(np.asarray(unnoted_states), nodes, edges, 1, -1)
    if unnoted_matrix is not None:
        unnoted_matrix *= -1   # Taking negative in order to flip the inequality

    # Constraints
    if isinstance(table, dict):
        noted_bound = np.asarray([table[state] for state in noted_states])
        unnoted_bound = np.full((n_unnoted, 1), -1 * max(table.values()))  # -1 for flipped inequality
    else:
        noted_bound = np.zeros((n_noted, 1))
        unnoted_bound = np.zeros((n_unnoted, 1))

    # Bounds
    linear_range = (MIN_LINEAR_BIAS, MAX_LINEAR_BIAS)
    quadratic_range = (MIN_QUADRATIC_BIAS, MAX_QUADRATIC_BIAS)

    bounds = [linear_energy_ranges.get(node, linear_range) for node in nodes]
    bounds += [get_item(quadratic_energy_ranges, edge, quadratic_range) for edge in edges]

    # Note: Since ising has {-1, 1}, the largest possible gap is [-largest_bias, largest_bias],
    #   hence that 2 * sum(largest_biases)
    max_gap = 2 * sum(max(abs(lbound), abs(ubound)) for lbound, ubound in bounds)
    bounds.append((None, None))     # Bound for offset
    bounds.append((min_classical_gap, max_gap))     # Bound for gap.

    # Cost function
    cost_weights = np.zeros((1, m_linear + m_quadratic + 2))
    cost_weights[0, -1] = -1     # Only interested in maximizing the gap

    # Returns a Scipy OptimizeResult
    result = linprog(cost_weights.flatten(), A_eq=noted_matrix, b_eq=noted_bound,
                     A_ub=unnoted_matrix, b_ub=unnoted_bound, bounds=bounds)

    #TODO: propagate scipy.optimize.linprog's error message?
    if not result.success:
        raise ValueError('Penaltymodel-lp is unable to find a solution.')

    # Split result
    x = result.x
    h = x[:m_linear]
    j = x[m_linear:-2]
    offset = x[-2]
    gap = x[-1]

    if gap <= 0:
        raise ValueError('Penaltymodel-lp is unable to find a solution.')

    # Create BQM
    bqm = dimod.BinaryQuadraticModel.empty(dimod.SPIN)
    bqm.add_variables_from((v, bias) for v, bias in zip(nodes, h))
    bqm.add_interactions_from((u, v, bias) for (u, v), bias in zip(edges, j))
    bqm.add_offset(offset)

    return bqm, gap
