"""SOFT7 OTEAPI plugin.

This requires the `oteapi` extra to be installed.
"""

from __future__ import annotations

from s7.exceptions import raise_if_extra_missing

try:
    import oteapi  # noqa: F401
except ImportError as exc:
    raise_if_extra_missing(exc, "oteapi", "The SOFT7 OTEAPI plugin", ("oteapi",))
    raise
