"""Internal helpers for deprecating the OTEAPI-related functionality.

All OTEAPI-related functionality is deprecated and will be removed, see
https://github.com/SINTEF/soft7/issues/222.
"""

from __future__ import annotations

import importlib
import os
import sys
import warnings

from s7.exceptions import OTEAPIDeprecationWarning

OTEAPI_REMOVAL_ISSUE = "https://github.com/SINTEF/soft7/issues/222"

_OTEAPI_IMPORTERS = frozenset(
    {
        "s7.factories",  # Lazily imports `create_datasource()`
        "s7.factories.datasource_factory",
        "s7.oteapi_plugin",
        "s7.pydantic_models.datasource",
        "s7.pydantic_models.oteapi",
    }
)
"""SOFT7 modules that may import the deprecated modules without a warning.

These are explicitly listed, instead of considering all `s7.*` modules, since other
packages may extend the `s7` namespace, e.g., `s7.graphtools` from
[SOFT7 GraphTools](https://github.com/SemanticMatter/s7_graphtools). These should
still be warned.
"""


def warn_oteapi_deprecated(feature: str, *, stacklevel: int = 2) -> None:
    """Emit an `OTEAPIDeprecationWarning` for `feature`.

    Parameters:
        feature: Description of the deprecated functionality.
        stacklevel: Stack level of the warning, relative to the caller of this
            function, i.e., `2` (default) attributes the warning to the caller's
            caller.

    """
    warnings.warn(
        f"{feature} is deprecated and will be removed in a future version of SOFT7, "
        "together with all other OTEAPI-related functionality. "
        f"See {OTEAPI_REMOVAL_ISSUE}",
        OTEAPIDeprecationWarning,
        stacklevel=stacklevel + 1,
    )


_IMPORTLIB_DIR = os.path.dirname(importlib.__file__) + os.sep  # noqa: PTH120


def _is_skipped_by_warnings(filename: str) -> bool:
    """Whether `warnings` skips a frame from `filename` when applying a `stacklevel`.

    This mirrors the check used by CPython's `warnings` module.
    """
    return "importlib" in filename and "_bootstrap" in filename


def _is_importlib(filename: str) -> bool:
    """Whether a frame from `filename` belongs to the `importlib` package.

    This includes the frozen import machinery, `importlib.import_module()`, and
    `importlib.metadata.EntryPoint.load()`.
    """
    return _is_skipped_by_warnings(filename) or filename.startswith(_IMPORTLIB_DIR)


def warn_oteapi_deprecated_module(module: str) -> None:
    """Emit an `OTEAPIDeprecationWarning` for importing `module`.

    The warning is attributed to the code importing `module`, skipping all of
    `importlib`. That is, for `importlib.import_module()` and entry point loading, the
    warning points to the code calling these functions.

    The warning is not emitted when `module` is imported by SOFT7's own
    OTEAPI-related modules, so that importing one deprecated module does not result in
    a cascade of warnings from the deprecated modules it imports in turn.

    Note:
        As for any import-time warning, the warning is only emitted for the first
        import of `module`. If `module` was first imported silently by SOFT7 itself,
        e.g., through `s7.factories.create_datasource`, a subsequent import does not
        warn. Calling `create_datasource()` still warns.

    Important:
        This must be called from the top level of the module being deprecated.

    Parameters:
        module: The name of the deprecated module, i.e., `__name__`.

    """
    # Frame 0 is this function and frame 1 the body of the deprecated module.
    # Relative to this function, the module body has stack level 2.
    frame = sys._getframe(1).f_back
    stacklevel = 2

    # Skip `importlib` to find the code importing the deprecated module.
    # Keep track of the stack level as counted by `warnings`, which only skips some of
    # the `importlib` frames.
    while frame is not None and _is_importlib(frame.f_code.co_filename):
        if not _is_skipped_by_warnings(frame.f_code.co_filename):
            stacklevel += 1
        frame = frame.f_back

    if frame is None:  # pragma: no cover
        importer = ""
    else:
        importer = frame.f_globals.get("__name__", "")
        if not _is_skipped_by_warnings(frame.f_code.co_filename):
            stacklevel += 1

    if importer in _OTEAPI_IMPORTERS or importer.startswith("s7.oteapi_plugin."):
        return

    warn_oteapi_deprecated(f"The {module!r} module", stacklevel=stacklevel)
