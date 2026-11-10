"""SOFT7 OTEAPI plugin.

This requires the `oteapi` extra to be installed.

Deprecated:
    All OTEAPI-related functionality is deprecated and will be removed,
    see https://github.com/SINTEF/soft7/issues/222.
"""

from __future__ import annotations

from s7._oteapi_deprecation import warn_oteapi_deprecated_module
from s7.exceptions import raise_if_extra_missing

try:
    import oteapi  # noqa: F401
except ImportError as exc:
    raise_if_extra_missing(exc, "oteapi", "The SOFT7 OTEAPI plugin", ("oteapi",))
    raise

warn_oteapi_deprecated_module(__name__)
