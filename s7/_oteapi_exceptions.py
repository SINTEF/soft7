"""SOFT7 exceptions only used by the deprecated OTEAPI-related functionality.

These are deprecated and will be removed together with all other OTEAPI-related
functionality, see https://github.com/SINTEF/soft7/issues/222.

They are kept here, instead of in `s7.exceptions`, so they can be used internally
without emitting deprecation warnings. Accessing them through `s7.exceptions` still
works, but emits an `s7.exceptions.OTEAPIDeprecationWarning`.

Their `__module__` is set to `s7.exceptions`, i.e., where they were originally defined
and are still publicly available. This keeps reprs and tracebacks unchanged, and
pickles compatible with previous versions of SOFT7. Note, (un)pickling them therefore
also emits a deprecation warning.
"""

from __future__ import annotations

from s7.exceptions import S7EntityError, S7Error


class ConfigsNotFound(S7EntityError, FileNotFoundError):
    """Raised when the configs are or can not be found."""

    __module__ = "s7.exceptions"


class S7OTEAPIPluginError(S7Error):
    """Base class for all SOFT7 OTEAPI plugin exceptions."""

    __module__ = "s7.exceptions"


class SOFT7FunctionError(S7OTEAPIPluginError):
    """Base class for all JSON to SOFT7 Entity OTEAPI parse strategy exceptions."""

    __module__ = "s7.exceptions"


class InsufficientData(SOFT7FunctionError, ValueError):
    """Raised when the data is insufficient to generate a SOFT7 entity."""

    __module__ = "s7.exceptions"


class InvalidMapping(SOFT7FunctionError, ValueError):
    """Raised when the mapping is invalid."""

    __module__ = "s7.exceptions"
