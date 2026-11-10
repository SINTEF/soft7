"""SOFT7 exceptions."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any


class S7Error(Exception):
    """Base class for all SOFT7 exceptions."""


class S7EntityError(S7Error):
    """Base class for all SOFT7 entity exceptions."""


class EntityNotFound(S7EntityError, FileNotFoundError):
    """Raised when an entity is or can not be found."""


class OTEAPIDeprecationWarning(DeprecationWarning):
    """Warning for SOFT7 functionality relying on OTEAPI, which will be removed.

    See https://github.com/SINTEF/soft7/issues/222.
    """


_DEPRECATED_OTEAPI_EXCEPTIONS = (
    "ConfigsNotFound",
    "InsufficientData",
    "InvalidMapping",
    "S7OTEAPIPluginError",
    "SOFT7FunctionError",
)
"""Deprecated exceptions only used by OTEAPI-related functionality.

They live in `s7._oteapi_exceptions` and are lazily retrieved by `__getattr__()`.
"""


def __getattr__(name: str) -> Any:
    """Retrieve the deprecated OTEAPI-related exceptions with a deprecation warning."""
    if name in _DEPRECATED_OTEAPI_EXCEPTIONS:
        from s7 import _oteapi_exceptions
        from s7._oteapi_deprecation import warn_oteapi_deprecated

        warn_oteapi_deprecated(f"`s7.exceptions.{name}`")
        return getattr(_oteapi_exceptions, name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


class MissingExtra(S7Error, ImportError):
    """Raised when functionality requiring a non-installed package extra is used."""

    def __init__(self, extra: str, feature: str) -> None:
        self.extra = extra
        self.feature = feature
        super().__init__(
            f"{feature} requires the {extra!r} extra to be installed. Install it "
            f"with: pip install 'soft7[{extra}]'"
        )

    def __reduce__(self) -> tuple[type[MissingExtra], tuple[str, str]]:
        """Support pickling, since the signature differs from `self.args`."""
        return (type(self), (self.extra, self.feature))


def raise_if_extra_missing(
    exc: ImportError, extra: str, feature: str, packages: tuple[str, ...]
) -> None:
    """Raise `MissingExtra` if `exc` is due to a missing top-level extra package.

    Other import errors, e.g., from a broken dependency of an installed extra, are
    left for the caller to re-raise, since telling the user to install an extra that
    is already installed would be misleading.

    Parameters:
        exc: The caught import error.
        extra: Name of the package extra.
        feature: Description of the functionality requiring the extra.
        packages: Top-level packages provided by the extra.

    """
    if (
        isinstance(exc, ModuleNotFoundError)
        and exc.name is not None
        and exc.name.partition(".")[0] in packages
    ):
        raise MissingExtra(extra, feature) from exc
