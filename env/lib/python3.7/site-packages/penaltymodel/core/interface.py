"""penaltymodel provides functionality for accessing PenaltyModel factories.

Accessing Factories
-------------------

Any factories that have been identified through the :const:`FACTORY_ENTRYPOINT` entrypoint
and installed on the python path can be accessed through the :func:`get_penalty_model`
function.

Examples:
    >>> import networkx as nx
    >>> import dimod
    >>> graph = nx.path_graph(5)
    >>> decision_variables = (0, 4)  # the ends of the path
    >>> feasible_configurations = {(-1, -1), (1, 1)}  # we want the ends of the path to agree
    >>> spec = pm.Specification(graph, decision_variables, feasible_configurations, dimod.SPIN)
    >>> widget = pm.get_penalty_model(spec)

Functions and Utilities
-----------------------
"""

from pkg_resources import iter_entry_points

from penaltymodel.core.exceptions import FactoryException, ImpossiblePenaltyModel

__all__ = ['FACTORY_ENTRYPOINT', 'CACHE_ENTRYPOINT', 'get_penalty_model', 'penaltymodel_factory',
           'iter_factories', 'iter_caches']

FACTORY_ENTRYPOINT = 'penaltymodel_factory'
"""str: constant used when assigning entrypoints for factories."""

CACHE_ENTRYPOINT = 'penaltymodel_cache'
"""str: constant used when assigning entrypoints for caches."""


def get_penalty_model(specification):
    """Retrieve a PenaltyModel from one of the available factories.

    Args:
        specification (:class:`.Specification`): The specification
            for the desired PenaltyModel.

    Returns:
        :class:`.PenaltyModel`/None: A PenaltyModel as returned by
        the highest priority factory, or None if no factory could
        produce it.

    Raises:
        :exc:`ImpossiblePenaltyModel`: If the specification
            describes a penalty model that cannot be built by any
            factory.

    """

    # Iterate through the available factories until one gives a penalty model
    for factory in iter_factories():
        try:
            pm = factory(specification)
        except ImpossiblePenaltyModel as e:
            # information about impossible models should be propagated
            raise e
        except FactoryException:
            # any other type of factory exception, continue through the list
            continue

        # if penalty model was found, broadcast to all of the caches. This could be done
        # asynchronously
        for cache in iter_caches():
            cache(pm)

        return pm

    return None


def penaltymodel_factory(priority):
    """Decorator to assign a `priority` attribute to the decorated function.

    Args:
        priority (int): The priority of the factory. Factories are queried
            in order of decreasing priority.

    Examples:
        Decorate penalty model factories like:

        >>> @pm.penaltymodel_factory(105)
        ... def factory_function(spec):
        ...     pass
        >>> factory_function.priority
        105

    """
    def _entry_point(f):
        f.priority = priority
        return f
    return _entry_point


def iter_factories():
    """Iterate through all factories identified by the factory entrypoint.

    Yields:
        function: A function that accepts a :class:`.Specification` and
        returns a :class:`.PenaltyModel`.

    """
    # retrieve all of the factories with
    factories = (entry.load() for entry in iter_entry_points(FACTORY_ENTRYPOINT))

    # sort the factories from highest priority to lowest. Any factory with unknown priority
    # gets assigned priority -1000.
    for factory in sorted(factories, key=lambda f: getattr(f, 'priority', -1000), reverse=True):
        yield factory


def iter_caches():
    """Iterator over the PenaltyModel caches.

    Yields:
        function: A function that accepts a :class:`PenaltyModel` and caches
        it.

    """
    # for caches we don't need an order
    return iter(entry.load() for entry in iter_entry_points(CACHE_ENTRYPOINT))
