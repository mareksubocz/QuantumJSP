"""
PenaltyModel
------------
"""
from __future__ import absolute_import

from numbers import Number

from six import iteritems
import networkx as nx

from dimod import BinaryQuadraticModel, Vartype

from penaltymodel.core.classes.specification import Specification


__all__ = ['PenaltyModel']


class PenaltyModel(Specification):
    """Container class for the components that make up a penalty model.

    A penalty model is a small Ising problem or QUBO that has ground
    states that match the feasible configurations and excited states
    that have a classical energy greater than the ground energy by
    at least the classical gap.

    PenaltyModel is a subclass of :class:`.Specification`.

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

        vartype (:class:`.Vartype`/str/set):
            The variable type desired for the penalty model.
            Accepted input values:
            :class:`.Vartype.SPIN`, ``'SPIN'``, ``{-1, 1}``
            :class:`.Vartype.BINARY`, ``'BINARY'``, ``{0, 1}``

        model (:class:`dimod.BinaryQuadraticModel`): A binary quadratic model
            that has ground states that match the feasible_configurations.

        classical_gap (numeric): The difference in classical energy between the ground
            state and the first excited state. Must be positive.

        ground_energy (numeric): The minimum energy of all possible configurations.

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
        The penalty model can be created from its component parts:

        >>> import networkx as nx
        >>> import dimod
        >>> graph = nx.path_graph(3)
        >>> decision_variables = (0, 2)  # the ends of the path
        >>> feasible_configurations = {(-1, -1), (1, 1)}  # we want the ends of the path to agree
        >>> model = dimod.BinaryQuadraticModel({0: 0, 1: 0, 2: 0}, {(0, 1): -1, (1, 2): -1}, 0.0, dimod.SPIN)
        >>> classical_gap = 2.0
        >>> ground_energy = -2.0
        >>> widget = pm.PenaltyModel(graph, decision_variables, feasible_configurations, dimod.SPIN,
        ...                          model, classical_gap, ground_energy)

        Or it can be created from a specification:

        >>> spec = pm.Specification(graph, decision_variables, feasible_configurations, dimod.SPIN)
        >>> widget = pm.PenaltyModel.from_specification(spec, model, classical_gap, ground_energy)

    Attributes:
        decision_variables (tuple): Maps the feasible configurations
            to the graph.
        classical_gap (numeric): The difference in classical energy between the ground
            state and the first excited state. Must be positive.
        feasible_configurations (dict[tuple[int], number]):
            The set of feasible configurations. The value is the (relative)
            energy of each of the feasible configurations.
        graph (:class:`networkx.Graph`): The graph that defines the relation
            between variables in the penaltymodel.
            The node labels will be used as the variable labels in the
            binary quadratic model.
        ground_energy (numeric): The minimum energy of all possible configurations.
        ising_linear_ranges (dict[node, (number, number)]):
            Defines the energy ranges available for the linear
            biases of the penalty model.
        model (:class:`dimod.BinaryQuadraticModel`): A binary quadratic model
            that has ground states that match the feasible_configurations.
        ising_quadratic_ranges (dict[edge, (number, number)]):
            Defines the energy ranges available for the quadratic
            biases of the penalty model.
        vartype (:class:`dimod.Vartype`): The variable type.

    """
    def __init__(self, graph, decision_variables, feasible_configurations, vartype,
                 model, classical_gap, ground_energy,
                 ising_linear_ranges=None, ising_quadratic_ranges=None):

        Specification.__init__(self, graph, decision_variables, feasible_configurations,
                               vartype=vartype,
                               min_classical_gap=classical_gap,
                               ising_linear_ranges=ising_linear_ranges,
                               ising_quadratic_ranges=ising_quadratic_ranges)

        if self.vartype != model.vartype:
            model = model.change_vartype(self.vartype)

        # check the energy ranges
        ising_linear_ranges = self.ising_linear_ranges
        ising_quadratic_ranges = self.ising_quadratic_ranges
        if self.vartype is Vartype.SPIN:
            # check the ising energy ranges
            for v, bias in iteritems(model.linear):
                min_, max_ = ising_linear_ranges[v]
                if bias < min_ or bias > max_:
                    raise ValueError(("variable {} has bias {} outside of the specified range [{}, {}]"
                                      ).format(v, bias, min_, max_))
            for (u, v), bias in iteritems(model.quadratic):
                min_, max_ = ising_quadratic_ranges[u][v]
                if bias < min_ or bias > max_:
                    raise ValueError(("interaction {}, {} has bias {} outside of the specified range [{}, {}]"
                                      ).format(u, v, bias, min_, max_))

        if not isinstance(model, BinaryQuadraticModel):
            raise TypeError("expected 'model' to be a BinaryQuadraticModel")
        self.model = model

        if not isinstance(classical_gap, Number):
            raise TypeError("expected classical_gap to be numeric")
        if classical_gap <= 0.0:
            raise ValueError("classical_gap must be positive")
        self.classical_gap = classical_gap

        if not isinstance(ground_energy, Number):
            raise TypeError("expected ground_energy to be numeric")
        self.ground_energy = ground_energy

    @classmethod
    def from_specification(cls, specification, model, classical_gap, ground_energy):
        """Construct a PenaltyModel from a Specification.

        Args:
            specification (:class:`.Specification`): A specification that was used
                to generate the model.
            model (:class:`dimod.BinaryQuadraticModel`): A binary quadratic model
                that has ground states that match the feasible_configurations.
            classical_gap (numeric): The difference in classical energy between the ground
                state and the first excited state. Must be positive.
            ground_energy (numeric): The minimum energy of all possible configurations.

        Returns:
            :class:`.PenaltyModel`

        """

        # Author note: there might be a way that avoids rechecking all of the values without
        # side-effects or lots of repeated code, but this seems simpler and more explicit
        return cls(specification.graph,
                   specification.decision_variables,
                   specification.feasible_configurations,
                   specification.vartype,
                   model,
                   classical_gap,
                   ground_energy,
                   ising_linear_ranges=specification.ising_linear_ranges,
                   ising_quadratic_ranges=specification.ising_quadratic_ranges)

    def __eq__(self, penalty_model):
        # other values are derived
        return (isinstance(penalty_model, PenaltyModel) and
                Specification.__eq__(self, penalty_model) and
                self.model == penalty_model.model)

    def __ne__(self, penalty_model):
        return not self.__eq__(penalty_model)

    def relabel_variables(self, mapping, inplace=True):
        """Relabel the variables and nodes according to the given mapping.

        Args:
            mapping (dict[hashable, hashable]): A dict with the current
                variable labels as keys and new labels as values. A
                partial mapping is allowed.

            inplace (bool, optional, default=True):
                If True, the penalty model is updated in-place; otherwise, a new penalty model
                is returned.

        Returns:
            :class:`.PenaltyModel`: A PenaltyModel with the variables relabeled according to
            mapping.

        Examples:
            >>> spec = pm.Specification(nx.path_graph(3), (0, 2), {(-1, -1), (1, 1)}, dimod.SPIN)
            >>> model = dimod.BinaryQuadraticModel({0: 0, 1: 0, 2: 0}, {(0, 1): -1, (1, 2): -1}, 0.0, dimod.SPIN)
            >>> penalty_model = pm.PenaltyModel.from_specification(spec, model, 2., -2.)
            >>> relabeled_penalty_model = penalty_model.relabel_variables({0: 'a'}, inplace=False)
            >>> relabeled_penalty_model.decision_variables
            ('a', 2)

            >>> spec = pm.Specification(nx.path_graph(3), (0, 2), {(-1, -1), (1, 1)}, dimod.SPIN)
            >>> model = dimod.BinaryQuadraticModel({0: 0, 1: 0, 2: 0}, {(0, 1): -1, (1, 2): -1}, 0.0, dimod.SPIN)
            >>> penalty_model = pm.PenaltyModel.from_specification(spec, model, 2., -2.)
            >>> __ = penalty_model.relabel_variables({0: 'a'}, inplace=True)
            >>> penalty_model.decision_variables
            ('a', 2)

        """
        # just use the relabeling of each component
        if inplace:
            Specification.relabel_variables(self, mapping, inplace=True)
            self.model.relabel_variables(mapping, inplace=True)
            return self
        else:
            spec = Specification.relabel_variables(self, mapping, inplace=False)
            model = self.model.relabel_variables(mapping, inplace=False)
            return PenaltyModel.from_specification(spec, model, self.classical_gap, self.ground_energy)
