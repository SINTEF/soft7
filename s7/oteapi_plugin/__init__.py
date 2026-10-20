"""SOFT7 OTEAPI plugin.

This requires the `oteapi` extra to be installed.
"""

from __future__ import annotations

from s7.exceptions import MissingExtra

try:
    import oteapi  # noqa: F401
except ImportError as exc:
    raise MissingExtra("oteapi", "The SOFT7 OTEAPI plugin") from exc
