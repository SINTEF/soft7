"""SOFT7 exceptions only used by the deprecated OTEAPI-related functionality.

These are deprecated and will be removed together with all other OTEAPI-related
functionality, see https://github.com/SINTEF/soft7/issues/222.

They are kept here, instead of in `s7.exceptions`, so they can be used internally
without emitting deprecation warnings. Accessing them through `s7.exceptions` still
works, but emits an `s7.exceptions.OTEAPIDeprecationWarning`.
"""

from __future__ import annotations

from s7.exceptions import S7EntityError, S7Error


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
