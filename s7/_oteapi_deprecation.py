"""Internal helpers for deprecating the OTEAPI-related functionality.

All OTEAPI-related functionality is deprecated and will be removed, see
https://github.com/SINTEF/soft7/issues/222.
"""

from __future__ import annotations

import sys
import warnings

from s7.exceptions import OTEAPIDeprecationWarning

OTEAPI_REMOVAL_ISSUE = "https://github.com/SINTEF/soft7/issues/222"


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


def _is_import_machinery(filename: str) -> bool:
    """Whether a frame's file belongs to the import machinery.

    This mirrors how `warnings` skips frames when applying a `stacklevel`.
    """
    return "importlib" in filename and "_bootstrap" in filename


def warn_oteapi_deprecated_module(module: str) -> None:
    """Emit an `OTEAPIDeprecationWarning` for importing `module`.

    The warning is only emitted when `module` is imported from outside SOFT7, so that
    importing one deprecated module does not result in a cascade of warnings from the
    deprecated modules it imports in turn.

    Important:
        This must be called from the top level of the module being deprecated.

    Parameters:
        module: The name of the deprecated module, i.e., `__name__`.

    """
    # Frame 0 is this function and frame 1 the body of the deprecated module.
    # Skip the import machinery to find the module importing the deprecated module.
    frame = sys._getframe(2)
    while frame is not None and _is_import_machinery(frame.f_code.co_filename):
        frame = frame.f_back

    importer = frame.f_globals.get("__name__", "") if frame is not None else ""
    if importer == "s7" or importer.startswith("s7."):
        return

    # Relative to this function, stack level 2 is the deprecated module's body and 3
    # the importing code, since `warnings` also skips the import machinery.
    warn_oteapi_deprecated(f"The {module!r} module", stacklevel=3)
