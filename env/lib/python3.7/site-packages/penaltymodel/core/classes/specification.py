"""
Specification
-------------
"""
from __future__ import absolute_import

from numbers import Number
import itertools

import networkx as nx

import dimod
from six import itervalues, iteritems, iterkeys


__all__ = ['Specification']


class Specification(object):
    """Specification for a PenaltyModel.

    See :class:`.PenaltyModel` documentation for a fuller description of the
    different components. A specification can be thought of as an incomplete
    penalty model.

    Args:
        graph (:class:`networkx.Graph`/iterable[edge]):
            Defines the structure of the desired binary quadratic model. Each
            node in the graph represents a variable and each edge defines an
            interaction between two variables.
            If given as an iterable of edges, the graph will be constructed
            by adding each edge to an (initially) empty graph.

        decision_variables (iterable):
            The labels of the penalty model's decision variables. Each variable label
            in `decision_variables` must correspond to a node in `graph`.
            Should be an ordered iterable of hashable labels.

        feasible_configurations (dict[tuple[int], number]/iterable[tuple[int]]):
            The set of feasible configurations. Defines the allowed configurations
            of the decision variables allowed by the constraint.
            Each feasible configuration should be a tuple, each element of which
            must be of a value matching `vartype`. If given as a dict, the key
            is the feasible configuration and the value is the desired relative
            energy. If given as an iterable, it will be case to a dict where
            the relative energies are all 0.

        vartype (:class:`dimod.Vartype`/str/set):
            The variable type desired for the penalty model.
            Accepted input values:
            :class:`.Vartype.SPIN`, ``'SPIN'``, ``{-1, 1}``
            :class:`.Vartype.BINARY`, ``'BINARY'``, ``{0, 1}``

        ising_linear_ranges (dict[node, [number, number]], optional, default=None):
            When the penalty model is spin-valued, specifies the allowed range
            for each of the linear biases.
            If a dict, should be of the form {v: [min, max], ...} where v is
            a variable in the desired penalty model and (min, max) defines
            the acceptable range for the linear bias associated with v.
            If None, the default will be set to {v: [-1, 1], ...} for each
            v in graph.
            A partial assignment is allowed.

        ising_quadratic_ranges (dict[node, dict[node, [number, number]], optional, default=None):
            When the penalty model is spin-valued, specifies the allowed range
            for each of the quadratic biases.
            If a dict, should be of the form {v: {u: [min, max], ...}, ...} where
            u and v are variables in the desired penalty model and u, v have an
            interaction - there is an edge between nodes u, v in `graph`. (min, max)
            the acceptable range for the quadratic bias associated with u, v.
            If None, the default will be set to
            {v: {u: [min, max], ...}, u: {v: [min, max], ...}, ...} for each
            edge u, v in graph.
            A partial assignment is allowed.

    Examples:
        >>> import networkx as nx
        >>> import dimod
        >>> graph = nx.path_graph(5)
        >>> decision_variables = (0, 4)  # the ends of the path
        >>> feasible_configurations = {(-1, -1), (1, 1)}  # we want the ends of the path to agree
        >>> vartype = dimod.Vartype.SPIN
        >>> spec = pm.Specification(graph, decision_variables, feasible_configurations, vartype)

        If we want to make the interaction between (0, 1) ferromagnetic (negative):

        >>> ising_quadratic_ranges = {0: {1: (-1, 0)}}
        >>> spec = pm.Specification(graph, decision_variables, feasible_configurations, vartype)

    Attributes:
        decision_variables (tuple):
            The labels of the penalty model's decision variables. Each variable label
            in `decision_variables` must correspond to a node in `graph`.

        feasible_configurations (dict[tuple[int], number]):
            The set of feasible configurations. Defines the allowed configurations
            of the decision variables allowed by the constraint. The key is the
            allowed configuration, the value is the relative energy of each
            configuration.

        graph (:class:`networkx.Graph`):
            Defines the structure of the desired binary quadratic model. Each
            node in the graph represents a variable and each edge defines an
            interaction between two variables.

        ising_linear_ranges (dict[node, [number, number], optional, default=None):
            When the penalty model is spin-valued, specifies the allowed range
            for each of the linear biases.
            A dict of the form {v: [min, max], ...} where v is
            a variable in the desired penalty model and [min, max] defines
            the acceptable range for the linear bias associated with v.

        ising_quadratic_ranges (dict[node, dict[node, [number, number]]], optional, default=None):
            When the penalty model is spin-valued, specifies the allowed range
            for each of the quadratic biases.
            A dict of the form {v: {u: [min, max], ...}, u: {v: [min, max], ...}, ...} where
            u and v are variables in the desired penalty model and u, v have an
            interaction - there is an edge between nodes u, v in `graph`.

        min_classical_gap (float):
            This is a threshold value for the classical gap. It describes the minimum energy gap
            between the highest feasible state and the lowest infeasible state. Default value is 2.

    """
    @dimod.decorators.vartype_argument('vartype')
    def __init__(self, graph, decision_variables, feasible_configurations, vartype,
                 ising_linear_ranges=None, ising_quadratic_ranges=None, min_classical_gap=2):

        #
        # graph
        #
        if not isinstance(graph, nx.Graph):
            try:
                edges = graph
                graph = nx.Graph()
                graph.add_edges_from(edges)
            except TypeError:
                raise TypeError("expected graph to be a networkx Graph or an iterable of edges")
        self.graph = graph

        #
        # decision_variables
        #
        try:
            if not isinstance(decision_variables, tuple):
                decision_variables = tuple(decision_variables)
        except TypeError:
            raise TypeError("expected decision_variables to be an iterable")
        if not all(v in graph for v in decision_variables):
            raise ValueError("some vars in decision decision_variables do not have a corresponding node in graph")
        self.decision_variables = decision_variables
        num_dv = len(decision_variables)

        #
        # feasible_configurations
        #
        try:
            if not isinstance(feasible_configurations, dict):
                feasible_configurations = {config: 0.0 for config in feasible_configurations}
            else:
                if not all(isinstance(en, Number) for en in itervalues(feasible_configurations)):
                    raise ValueError("the energy fo each configuration should be numeric")
        except TypeError:
            raise TypeError("expected decision_variables to be an iterable")
        if not all(len(config) == num_dv for config in feasible_configurations):
            raise ValueError("the feasible configurations should all match the length of decision_variables")
        self.feasible_configurations = feasible_configurations

        #
        # energy ranges
        #
        self.ising_linear_ranges = self._check_ising_linear_ranges(ising_linear_ranges, graph)
        self.ising_quadratic_ranges = self._check_ising_quadratic_ranges(ising_quadratic_ranges, graph)

        #
        # min_classical_gap
        #
        if min_classical_gap <= 0:
            raise ValueError("min_classical_gap must be a positive number")
        self.min_classical_gap = min_classical_gap

        #
        # vartype
        #
        # check that our feasible configurations match
        seen_variable_types = set().union(*feasible_configurations)
        if not seen_variable_types.issubset(vartype.value):
            raise ValueError(("feasible_configurations type must match vartype. "
                              "feasible_configurations have values {}, "
                              "values permitted by vartype are {}.").format(seen_variable_types, vartype.value))
        self.vartype = vartype

    @staticmethod
    def _check_ising_linear_ranges(linear_ranges, graph):
        """check correctness/populate defaults for ising_linear_ranges."""
        if linear_ranges is None:
            linear_ranges = {}

        for v in graph:
            if v in linear_ranges:
                # check
                linear_ranges[v] = Specification._check_range(linear_ranges[v])
            else:
                # set default
                linear_ranges[v] = [-2, 2]

        return linear_ranges

    @staticmethod
    def _check_ising_quadratic_ranges(quad_ranges, graph):
        """check correctness/populate defaults for ising_quadratic_ranges."""
        if quad_ranges is None:
            quad_ranges = {}

        # first just populate the top level so we can rely on the structure
        for u in graph:
            if u not in quad_ranges:
                quad_ranges[u] = {}

        # next let's propgate and check what is already present
        for u, neighbors in iteritems(quad_ranges):
            for v, rang in iteritems(neighbors):
                # check the range
                rang = Specification._check_range(rang)

                if u in quad_ranges[v]:
                    # it's symmetric
                    if quad_ranges[u][v] != quad_ranges[v][u]:
                        raise ValueError("mismatched ranges for ising_quadratic_ranges")
                quad_ranges[v][u] = quad_ranges[u][v] = rang

        # finally fill in the missing stuff
        for u, v in graph.edges:
            if u not in quad_ranges[v]:
                quad_ranges[u][v] = quad_ranges[v][u] = [-1, 1]

        return quad_ranges

    @staticmethod
    def _check_range(range_):
        """Check that a range is in the format we expect [min, max] and return"""
        try:
            if not isinstance(range_, list):
                range_ = list(range_)
            min_, max_ = range_
        except (ValueError, TypeError):
            raise TypeError("each range in ising_linear_ranges should be a list of length 2.")
        if not isinstance(min_, Number) or not isinstance(max_, Number) or min_ > max_:
            raise ValueError(("each range in ising_linear_ranges should be a 2-tuple "
                              "(min, max) where min <= max"))
        return range_

    def __len__(self):
        return len(self.graph)

    def __eq__(self, specification):
        """Implemented equality checking. """

        # for specification, graph is considered equal if it has the same nodes
        # and edges
        return (isinstance(specification, Specification) and
                self.graph.edges == specification.graph.edges and
                self.graph.nodes == specification.graph.nodes and
                self.decision_variables == specification.decision_variables and
                self.feasible_configurations == specification.feasible_configurations)

    def __ne__(self, specification):
        return not self.__eq__(specification)

    def relabel_variables(self, mapping, inplace=True):
        """Relabel the variables and nodes according to the given mapping.

        Args:
            mapping (dict): a dict mapping the current variable/node labels
                to new ones.
            inplace (bool, optional, default=True):
                If True, the specification is updated in-place; otherwise, a new specification
                is returned.

        Returns:
            :class:`.Specification`: A Specification with the variables
            relabeled according to mapping. If copy=False returns itself,
            if copy=True returns a new Specification.

        """
        graph = self.graph
        ising_linear_ranges = self.ising_linear_ranges
        ising_quadratic_ranges = self.ising_quadratic_ranges

        try:
            old_labels = set(iterkeys(mapping))
            new_labels = set(itervalues(mapping))
        except TypeError:
            raise ValueError("mapping targets must be hashable objects")

        for v in new_labels:
            if v in graph and v not in old_labels:
                raise ValueError(('A variable cannot be relabeled "{}" without also relabeling '
                                  "the existing variable of the same name").format(v))

        if not inplace:
            return Specification(nx.relabel_nodes(graph, mapping, copy=True),  # also checks the mapping
                                 tuple(mapping.get(v, v) for v in self.decision_variables),
                                 self.feasible_configurations,  # does not change
                                 vartype=self.vartype,  # does not change
                                 ising_linear_ranges={mapping.get(v, v): ising_linear_ranges[v] for v in graph},
                                 ising_quadratic_ranges={mapping.get(v, v): {mapping.get(u, u): r
                                                                             for u, r in iteritems(neighbors)}
                                                         for v, neighbors in iteritems(ising_quadratic_ranges)})
        else:
            # now we need the ising_linear_ranges and ising_quadratic_ranges
            shared = old_labels & new_labels

            if shared:
                # in this case we need to transform to an intermediate state
                # counter will be used to generate the intermediate labels, as an easy optimization
                # we start the counter with a high number because often variables are labeled by
                # integers starting from 0
                counter = itertools.count(2 * len(self))

                old_to_intermediate = {}
                intermediate_to_new = {}

                for old, new in iteritems(mapping):
                    if old == new:
                        # we can remove self-labels
                        continue

                    if old in new_labels or new in old_labels:

                        # try to get a new unique label
                        lbl = next(counter)
                        while lbl in new_labels or lbl in old_labels:
                            lbl = next(counter)

                        # add it to the mapping
                        old_to_intermediate[old] = lbl
                        intermediate_to_new[lbl] = new

                    else:
                        old_to_intermediate[old] = new
                        # don't need to add it to intermediate_to_new because it is a self-label

                Specification.relabel_variables(self, old_to_intermediate, inplace=True)
                Specification.relabel_variables(self, intermediate_to_new, inplace=True)
                return self

            # modifies graph in place
            nx.relabel_nodes(self.graph, mapping, copy=False)

            # this is always a new object
            self.decision_variables = tuple(mapping.get(v, v) for v in self.decision_variables)

            # we can just relabel in-place without worrying about conflict
            for v in old_labels:
                if v in mapping:
                    ising_linear_ranges[mapping[v]] = ising_linear_ranges[v]
                    del ising_linear_ranges[v]

            # need to do the deeper level first
            for neighbors in itervalues(ising_quadratic_ranges):
                for v in list(neighbors):
                    if v in mapping:
                        neighbors[mapping[v]] = neighbors[v]
                        del neighbors[v]

            # now the top level
            for v in old_labels:
                if v in mapping:
                    ising_quadratic_ranges[mapping[v]] = ising_quadratic_ranges[v]
                    del ising_quadratic_ranges[v]

            return self
