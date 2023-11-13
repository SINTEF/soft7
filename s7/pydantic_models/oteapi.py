"""Customized OTEAPI pydantic models."""
from __future__ import annotations

from collections.abc import Hashable
from typing import TYPE_CHECKING

from oteapi.models import FunctionConfig, MappingConfig, ResourceConfig

if TYPE_CHECKING:  # pragma: no cover
    pass


class HashableMixin:
    """Mixin to make pydantic models hashable."""

    def __hash__(self) -> int:
        return hash(
            tuple(
                (field_name, field_value)
                if (isinstance(field_value, Hashable) or field_value is None)
                else (field_name, None)
                for field_name, field_value in self
            )
        )


class HashableResourceConfig(ResourceConfig, HashableMixin):
    """ResourceConfig, but hashable."""


class HashableMappingConfig(MappingConfig, HashableMixin):
    """MappingConfig, but hashable."""


class HashableFunctionConfig(FunctionConfig, HashableMixin):
    """FunctionConfig, but hashable."""


def default_soft7_ote_function_config() -> HashableFunctionConfig:
    """Create a default SOFT7 OTEAPI Function strategy configuration."""
    return HashableFunctionConfig(
        description="SOFT7 OTEAPI Function configuration.",
        functionType="SOFT7",
    )
