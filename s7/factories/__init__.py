"""Public factory functions for creating SOFT7-related classes and instances."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .entity_factory import create_entity

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any

    from .datasource_factory import create_datasource

__all__ = ("create_datasource", "create_entity")


def __getattr__(name: str) -> Any:
    """Lazily import `create_datasource()`.

    It requires the `oteapi` extra, which should not be needed to use
    `create_entity()`.
    """
    if name == "create_datasource":
        from .datasource_factory import create_datasource

        return create_datasource

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
