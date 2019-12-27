"""
Exceptions
----------
"""


class FactoryException(Exception):
    """General exception for a factory being not able to produce a penalty model."""


class ImpossiblePenaltyModel(FactoryException):
    """PenaltyModel is impossible to build."""


class MissingPenaltyModel(FactoryException):
    """PenaltyModel is missing from the cache or otherwise unavailable."""
