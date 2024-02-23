"""SOFT7 exceptions."""

from __future__ import annotations


class S7Error(Exception):
    """Base class for all SOFT7 exceptions."""


class S7EntityError(S7Error):
    """Base class for all SOFT7 entity exceptions."""


class EntityNotFound(S7EntityError, FileNotFoundError):
    """Raised when an entity is or can not be found."""


class ConfigsNotFound(S7EntityError, FileNotFoundError):
    """Raised when the configs are or can not be found."""


class S7OTEAPIPluginError(S7Error):
    """Base class for all SOFT7 OTEAPI plugin exceptions."""


class SOFT7FunctionError(S7OTEAPIPluginError):
    """Base class for all JSON to SOFT7 Entity OTEAPI parse strategy exceptions."""


class InsufficientData(SOFT7FunctionError, ValueError):
    """Raised when the data is insufficient to generate a SOFT7 entity."""


class InvalidMapping(SOFT7FunctionError, ValueError):
    """Raised when the mapping is invalid."""
