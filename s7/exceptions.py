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
        super().__init__(
            f"{feature} requires the {extra!r} extra to be installed. Install it "
            f"with: pip install 'soft7[{extra}]'"
        )
