"""
Utilities for access to the sqlite cache.

"""
import sqlite3
import os
import json
import struct
import base64

from six import itervalues
import penaltymodel.core as pm

import dimod

from penaltymodel.cache.schema import schema
from penaltymodel.cache.cache_manager import cache_file

__all__ = ["cache_connect",
           "insert_graph", "iter_graph",
           "insert_feasible_configurations", "iter_feasible_configurations",
           "insert_ising_model", "iter_ising_model",
           "insert_penalty_model", "iter_penalty_model_from_specification"]


def cache_connect(database=None):
    """Returns a connection object to a sqlite database.

    Args:
        database (str, optional): The path to the database the user wishes
            to connect to. If not specified, a default is chosen using
            :func:`.cache_file`. If the special database name ':memory:'
            is given, then a temporary database is created in memory.

    Returns:
        :class:`sqlite3.Connection`

    """
    if database is None:
        database = cache_file()

    if os.path.isfile(database):
        # just connect to the database as-is
        conn = sqlite3.connect(database)
    else:
        # we need to populate the database
        conn = sqlite3.connect(database)
        conn.executescript(schema)

    with conn as cur:
        # turn on foreign keys, allows deletes to cascade.
        cur.execute("PRAGMA foreign_keys = ON;")

    conn.row_factory = sqlite3.Row

    return conn


def insert_graph(cur, nodelist, edgelist, encoded_data=None):
    """Insert a graph into the cache.

    A graph is stored by number of nodes, number of edges and a
    json-encoded list of edges.

    Args:
        cur (:class:`sqlite3.Cursor`): An sqlite3 cursor. This function
            is meant to be run within a :obj:`with` statement.
        nodelist (list): The nodes in the graph.
        edgelist (list): The edges in the graph.
        encoded_data (dict, optional): If a dictionary is provided, it
            will be populated with the serialized data. This is useful for
            preventing encoding the same information many times.

    Notes:
        This function assumes that the nodes are index-labeled and range
        from 0 to num_nodes - 1.

        In order to minimize the total size of the cache, it is a good
        idea to sort the nodelist and edgelist before inserting.

    Examples:
        >>> nodelist = [0, 1, 2]
        >>> edgelist = [(0, 1), (1, 2)]
        >>> with pmc.cache_connect(':memory:') as cur:
        ...     pmc.insert_graph(cur, nodelist, edgelist)

        >>> nodelist = [0, 1, 2]
        >>> edgelist = [(0, 1), (1, 2)]
        >>> encoded_data = {}
        >>> with pmc.cache_connect(':memory:') as cur:
        ...     pmc.insert_graph(cur, nodelist, edgelist, encoded_data)
        >>> encoded_data['num_nodes']
        3
        >>> encoded_data['num_edges']
        2
        >>> encoded_data['edges']
        '[[0,1],[1,2]]'

    """
    if encoded_data is None:
        encoded_data = {}

    if 'num_nodes' not in encoded_data:
        encoded_data['num_nodes'] = len(nodelist)
    if 'num_edges' not in encoded_data:
        encoded_data['num_edges'] = len(edgelist)
    if 'edges' not in encoded_data:
        encoded_data['edges'] = json.dumps(edgelist, separators=(',', ':'))

    insert = \
        """
        INSERT OR IGNORE INTO graph(num_nodes, num_edges, edges)
        VALUES (:num_nodes, :num_edges, :edges);
        """

    cur.execute(insert, encoded_data)


def iter_graph(cur):
    """Iterate over all graphs in the cache.

    Args:
        cur (:class:`sqlite3.Cursor`): An sqlite3 cursor. This function
            is meant to be run within a :obj:`with` statement.

    Yields:
        tuple: A 2-tuple containing:

            list: The nodelist for a graph in the cache.

            list: the edgelist for a graph in the cache.

    Examples:
        >>> nodelist = [0, 1, 2]
        >>> edgelist = [(0, 1), (1, 2)]
        >>> with pmc.cache_connect(':memory:') as cur:
        ...     pmc.insert_graph(cur, nodelist, edgelist)
        ...     list(pmc.iter_graph(cur))
        [([0, 1, 2], [[0, 1], [1, 2]])]

    """
    select = """SELECT num_nodes, num_edges, edges from graph;"""
    for num_nodes, num_edges, edges in cur.execute(select):
        yield list(range(num_nodes)), json.loads(edges)


def insert_feasible_configurations(cur, feasible_configurations, encoded_data=None):
    """Insert a group of feasible configurations into the cache.

    Args:
        cur (:class:`sqlite3.Cursor`): An sqlite3 cursor. This function
            is meant to be run within a :obj:`with` statement.
        feasible_configurations (dict[tuple[int]): The set of feasible
            configurations. Each key should be a tuple of variable assignments.
            The values are the relative energies.
        encoded_data (dict, optional): If a dictionary is provided, it
            will be populated with the serialized data. This is useful for
            preventing encoding the same information many times.

    Examples:
        >>> feasible_configurations = {(-1, -1): 0.0, (+1, +1): 0.0}
        >>> with pmc.cache_connect(':memory:') as cur:
        ...     pmc.insert_feasible_configurations(cur, feasible_configurations)

    """
    if encoded_data is None:
        encoded_data = {}

    if 'num_variables' not in encoded_data:
        encoded_data['num_variables'] = len(next(iter(feasible_configurations)))
    if 'num_feasible_configurations' not in encoded_data:
        encoded_data['num_feasible_configurations'] = len(feasible_configurations)
    if 'feasible_configurations' not in encoded_data or 'energies' not in encoded_data:
        encoded = {_serialize_config(config): en for config, en in feasible_configurations.items()}

        configs, energies = zip(*sorted(encoded.items()))
        encoded_data['feasible_configurations'] = json.dumps(configs, separators=(',', ':'))
        encoded_data['energies'] = json.dumps(energies, separators=(',', ':'))

    insert = """
            INSERT OR IGNORE INTO feasible_configurations(
                num_variables,
                num_feasible_configurations,
                feasible_configurations,
                energies)
            VALUES (
                :num_variables,
                :num_feasible_configurations,
                :feasible_configurations,
                :energies);
            """

    cur.execute(insert, encoded_data)


def _serialize_config(config):
    """Turns a config into an integer treating each of the variables as spins.

    Examples:
        >>> _serialize_config((0, 0, 1))
        1
        >>> _serialize_config((1, 1))
        3
        >>> _serialize_config((1, 0, 0))
        4

    """
    out = 0
    for bit in config:
        out = (out << 1) | (bit > 0)

    return out


def iter_feasible_configurations(cur):
    """Iterate over all of the sets of feasible configurations in the cache.

    Args:
        cur (:class:`sqlite3.Cursor`): An sqlite3 cursor. This function
            is meant to be run within a :obj:`with` statement.

    Yields:
        dict[tuple(int): number]: The feasible_configurations.

    """
    select = \
        """
        SELECT num_variables, feasible_configurations, energies
        FROM feasible_configurations
        """
    for num_variables, feasible_configurations, energies in cur.execute(select):
        configs = json.loads(feasible_configurations)
        energies = json.loads(energies)

        yield {_decode_config(config, num_variables): energy
               for config, energy in zip(configs, energies)}


def _decode_config(c, num_variables):
    """inverse of _serialize_config, always converts to spin."""
    def bits(c):
        n = 1 << (num_variables - 1)
        for __ in range(num_variables):
            yield 1 if c & n else -1
            n >>= 1
    return tuple(bits(c))


def insert_ising_model(cur, nodelist, edgelist, linear, quadratic, offset, encoded_data=None):
    """Insert an Ising model into the cache.

    Args:
        cur (:class:`sqlite3.Cursor`): An sqlite3 cursor. This function
            is meant to be run within a :obj:`with` statement.
        nodelist (list): The nodes in the graph.
        edgelist (list): The edges in the graph.
        linear (dict): The linear bias associated with each node in nodelist.
        quadratic (dict): The quadratic bias associated with teach edge in edgelist.
        offset (float): The constant offset applied to the ising problem.
        encoded_data (dict, optional): If a dictionary is provided, it
            will be populated with the serialized data. This is useful for
            preventing encoding the same information many times.

    """
    if encoded_data is None:
        encoded_data = {}

    # insert graph and partially populate encoded_data with graph info
    insert_graph(cur, nodelist, edgelist, encoded_data=encoded_data)

    # need to encode the biases
    if 'linear_biases' not in encoded_data:
        encoded_data['linear_biases'] = _serialize_linear_biases(linear, nodelist)
    if 'quadratic_biases' not in encoded_data:
        encoded_data['quadratic_biases'] = _serialize_quadratic_biases(quadratic, edgelist)
    if 'offset' not in encoded_data:
        encoded_data['offset'] = offset
    if 'max_quadratic_bias' not in encoded_data:
        encoded_data['max_quadratic_bias'] = max(itervalues(quadratic))
    if 'min_quadratic_bias' not in encoded_data:
        encoded_data['min_quadratic_bias'] = min(itervalues(quadratic))
    if 'max_linear_bias' not in encoded_data:
        encoded_data['max_linear_bias'] = max(itervalues(linear))
    if 'min_linear_bias' not in encoded_data:
        encoded_data['min_linear_bias'] = min(itervalues(linear))

    insert = \
        """
        INSERT OR IGNORE INTO ising_model(
            linear_biases,
            quadratic_biases,
            offset,
            max_quadratic_bias,
            min_quadratic_bias,
            max_linear_bias,
            min_linear_bias,
            graph_id)
        SELECT
            :linear_biases,
            :quadratic_biases,
            :offset,
            :max_quadratic_bias,
            :min_quadratic_bias,
            :max_linear_bias,
            :min_linear_bias,
            graph.id
        FROM graph WHERE
            num_nodes = :num_nodes AND
            num_edges = :num_edges AND
            edges = :edges;
        """

    cur.execute(insert, encoded_data)


def _serialize_linear_biases(linear, nodelist):
    """Serializes the linear biases.

    Args:
        linear: a interable object where linear[v] is the bias
            associated with v.
        nodelist (list): an ordered iterable containing the nodes.

    Returns:
        str: base 64 encoded string of little endian 8 byte floats,
            one for each of the biases in linear. Ordered according
            to nodelist.

    Examples:
        >>> _serialize_linear_biases({1: -1, 2: 1, 3: 0}, [1, 2, 3])
        'AAAAAAAA8L8AAAAAAADwPwAAAAAAAAAA'
        >>> _serialize_linear_biases({1: -1, 2: 1, 3: 0}, [3, 2, 1])
        'AAAAAAAAAAAAAAAAAADwPwAAAAAAAPC/'

    """
    linear_bytes = struct.pack('<' + 'd' * len(linear), *[linear[i] for i in nodelist])
    return base64.b64encode(linear_bytes).decode('utf-8')


def _serialize_quadratic_biases(quadratic, edgelist):
    """Serializes the quadratic biases.

    Args:
        quadratic (dict): a dict of the form {edge1: bias1, ...} where
            each edge is of the form (node1, node2).
        edgelist (list): a list of the form [(node1, node2), ...].

    Returns:
        str: base 64 encoded string of little endian 8 byte floats,
            one for each of the edges in quadratic. Ordered by edgelist.

    Example:
        >>> _serialize_quadratic_biases({(0, 1): -1, (1, 2): 1, (0, 2): .4},
        ...                             [(0, 1), (1, 2), (0, 2)])
        'AAAAAAAA8L8AAAAAAADwP5qZmZmZmdk/'

    """
    # assumes quadratic is upper-triangular or reflected in edgelist
    quadratic_list = [quadratic[(u, v)] if (u, v) in quadratic else quadratic[(v, u)]
                      for u, v in edgelist]
    quadratic_bytes = struct.pack('<' + 'd' * len(quadratic), *quadratic_list)
    return base64.b64encode(quadratic_bytes).decode('utf-8')


def iter_ising_model(cur):
    """Iterate over all of the Ising models in the cache.

    Args:
        cur (:class:`sqlite3.Cursor`): An sqlite3 cursor. This function
            is meant to be run within a :obj:`with` statement.

    Yields:
        tuple: A 5-tuple consisting of:

            list: The nodelist for a graph in the cache.

            list: the edgelist for a graph in the cache.

            dict: The linear biases of an Ising Model in the cache.

            dict: The quadratic biases of an Ising Model in the cache.

            float: The constant offset of an Ising Model in the cache.

    """
    select = \
        """
        SELECT linear_biases, quadratic_biases, num_nodes, edges, offset
        FROM ising_model, graph
        WHERE graph.id = ising_model.graph_id;
        """

    for linear_biases, quadratic_biases, num_nodes, edges, offset in cur.execute(select):
        nodelist = list(range(num_nodes))
        edgelist = json.loads(edges)
        yield (nodelist, edgelist,
               _decode_linear_biases(linear_biases, nodelist),
               _decode_quadratic_biases(quadratic_biases, edgelist),
               offset)


def _decode_linear_biases(linear_string, nodelist):
    """Inverse of _serialize_linear_biases.

    Args:
        linear_string (str): base 64 encoded string of little endian
            8 byte floats, one for each of the nodes in nodelist.
        nodelist (list): list of the form [node1, node2, ...].

    Returns:
        dict: linear biases in a dict.

    Examples:
        >>> _decode_linear_biases('AAAAAAAA8L8AAAAAAADwPwAAAAAAAAAA', [1, 2, 3])
        {1: -1.0, 2: 1.0, 3: 0.0}
        >>> _decode_linear_biases('AAAAAAAA8L8AAAAAAADwPwAAAAAAAAAA', [3, 2, 1])
        {1: 0.0, 2: 1.0, 3: -1.0}

    """
    linear_bytes = base64.b64decode(linear_string)
    return dict(zip(nodelist, struct.unpack('<' + 'd' * (len(linear_bytes) // 8), linear_bytes)))


def _decode_quadratic_biases(quadratic_string, edgelist):
    """Inverse of _serialize_quadratic_biases

    Args:
        quadratic_string (str) : base 64 encoded string of little
            endian 8 byte floats, one for each of the edges.
        edgelist (list): a list of edges of the form [(node1, node2), ...].

    Returns:
        dict: J. A dict of the form {edge1: bias1, ...} where each
            edge is of the form (node1, node2).

    Example:
        >>> _decode_quadratic_biases('AAAAAAAA8L8AAAAAAADwP5qZmZmZmdk/',
        ...                          [(0, 1), (1, 2), (0, 2)])
        {(0, 1): -1.0, (0, 2): 0.4, (1, 2): 1.0}

    """
    quadratic_bytes = base64.b64decode(quadratic_string)
    return {tuple(edge): bias for edge, bias in zip(edgelist,
            struct.unpack('<' + 'd' * (len(quadratic_bytes) // 8), quadratic_bytes))}


def insert_penalty_model(cur, penalty_model):
    """Insert a penalty model into the database.

    Args:
        cur (:class:`sqlite3.Cursor`): An sqlite3 cursor. This function
            is meant to be run within a :obj:`with` statement.
        penalty_model (:class:`penaltymodel.PenaltyModel`): A penalty
            model to be stored in the database.

    Examples:
        >>> import networkx as nx
        >>> import penaltymodel.core as pm
        >>> import dimod
        >>> graph = nx.path_graph(3)
        >>> decision_variables = (0, 2)
        >>> feasible_configurations = {(-1, -1): 0., (+1, +1): 0.}
        >>> spec = pm.Specification(graph, decision_variables, feasible_configurations, dimod.SPIN)
        >>> linear = {v: 0 for v in graph}
        >>> quadratic = {edge: -1 for edge in graph.edges}
        >>> model = dimod.BinaryQuadraticModel(linear, quadratic, 0.0, vartype=dimod.SPIN)
        >>> widget = pm.PenaltyModel.from_specification(spec, model, 2., -2)
        >>> with pmc.cache_connect(':memory:') as cur:
        ...     pmc.insert_penalty_model(cur, widget)

    """
    encoded_data = {}

    linear, quadratic, offset = penalty_model.model.to_ising()
    nodelist = sorted(linear)
    edgelist = sorted(sorted(edge) for edge in penalty_model.graph.edges)

    insert_graph(cur, nodelist, edgelist, encoded_data)
    insert_feasible_configurations(cur, penalty_model.feasible_configurations, encoded_data)
    insert_ising_model(cur, nodelist, edgelist, linear, quadratic, offset, encoded_data)

    encoded_data['decision_variables'] = json.dumps(penalty_model.decision_variables, separators=(',', ':'))
    encoded_data['classical_gap'] = penalty_model.classical_gap
    encoded_data['ground_energy'] = penalty_model.ground_energy

    insert = \
        """
        INSERT OR IGNORE INTO penalty_model(
            decision_variables,
            classical_gap,
            ground_energy,
            feasible_configurations_id,
            ising_model_id)
        SELECT
            :decision_variables,
            :classical_gap,
            :ground_energy,
            feasible_configurations.id,
            ising_model.id
        FROM feasible_configurations, ising_model, graph
        WHERE
            graph.edges = :edges AND
            graph.num_nodes = :num_nodes AND
            ising_model.graph_id = graph.id AND
            ising_model.linear_biases = :linear_biases AND
            ising_model.quadratic_biases = :quadratic_biases AND
            ising_model.offset = :offset AND
            feasible_configurations.num_variables = :num_variables AND
            feasible_configurations.num_feasible_configurations = :num_feasible_configurations AND
            feasible_configurations.feasible_configurations = :feasible_configurations AND
            feasible_configurations.energies = :energies;
        """

    cur.execute(insert, encoded_data)


def iter_penalty_model_from_specification(cur, specification):
    """Iterate through all penalty models in the cache matching the
    given specification.

    Args:
        cur (:class:`sqlite3.Cursor`): An sqlite3 cursor. This function
            is meant to be run within a :obj:`with` statement.
        specification (:class:`penaltymodel.Specification`): A specification
            for a penalty model.

    Yields:
        :class:`penaltymodel.PenaltyModel`

    """
    encoded_data = {}

    nodelist = sorted(specification.graph)
    edgelist = sorted(sorted(edge) for edge in specification.graph.edges)
    encoded_data['num_nodes'] = len(nodelist)
    encoded_data['num_edges'] = len(edgelist)
    encoded_data['edges'] = json.dumps(edgelist, separators=(',', ':'))
    encoded_data['num_variables'] = len(next(iter(specification.feasible_configurations)))
    encoded_data['num_feasible_configurations'] = len(specification.feasible_configurations)

    encoded = {_serialize_config(config): en for config, en in specification.feasible_configurations.items()}
    configs, energies = zip(*sorted(encoded.items()))
    encoded_data['feasible_configurations'] = json.dumps(configs, separators=(',', ':'))
    encoded_data['energies'] = json.dumps(energies, separators=(',', ':'))

    encoded_data['decision_variables'] = json.dumps(specification.decision_variables, separators=(',', ':'))
    encoded_data['classical_gap'] = json.dumps(specification.min_classical_gap, separators=(',', ':'))

    select = \
        """
        SELECT
            linear_biases,
            quadratic_biases,
            offset,
            decision_variables,
            classical_gap,
            ground_energy
        FROM penalty_model_view
        WHERE
            -- graph:
            num_nodes = :num_nodes AND
            num_edges = :num_edges AND
            edges = :edges AND
            -- feasible_configurations:
            num_variables = :num_variables AND
            num_feasible_configurations = :num_feasible_configurations AND
            feasible_configurations = :feasible_configurations AND
            energies = :energies AND
            -- decision variables:
            decision_variables = :decision_variables AND
            -- we could apply filters based on the energy ranges but in practice this seems slower
            classical_gap >= :classical_gap
        ORDER BY classical_gap DESC;
        """

    for row in cur.execute(select, encoded_data):
        # we need to build the model
        linear = _decode_linear_biases(row['linear_biases'], nodelist)
        quadratic = _decode_quadratic_biases(row['quadratic_biases'], edgelist)

        model = dimod.BinaryQuadraticModel(linear, quadratic, row['offset'], dimod.SPIN)  # always spin

        yield pm.PenaltyModel.from_specification(specification, model, row['classical_gap'], row['ground_energy'])
