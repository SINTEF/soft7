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
