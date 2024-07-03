"""Customized OTEAPI pydantic models."""

from __future__ import annotations

from collections.abc import Hashable
from typing import TYPE_CHECKING

from oteapi.models import (
    FunctionConfig,
    GenericConfig,
    MappingConfig,
    ParserConfig,
    ResourceConfig,
)
from pydantic import AnyUrl

from s7.pydantic_models.soft7_entity import SOFT7IdentityURI, SOFT7IdentityURIType

if TYPE_CHECKING:  # pragma: no cover
    from typing import Union

    from s7.pydantic_models.soft7_instance import SOFT7EntityInstance


class HashableMixin:
    """Mixin to make pydantic models hashable."""

    def __hash__(self) -> int:
        """Hash the model."""
        if isinstance(self, GenericConfig):
            return hash(
                tuple(
                    (
                        (field_name, field_value)
                        if (isinstance(field_value, Hashable) or field_value is None)
                        else (field_name, None)
                    )
                    for field_name, field_value in self
                )
            )
        raise NotImplementedError(
            f"Hashing of {self.__class__.__name__} is not implemented."
        )


class HashableFunctionConfig(FunctionConfig, HashableMixin):
    """FunctionConfig, but hashable."""


class HashableMappingConfig(MappingConfig, HashableMixin):
    """MappingConfig, but hashable."""


class HashableParserConfig(ParserConfig, HashableMixin):
    """ParserConfig, but hashable."""


class HashableResourceConfig(ResourceConfig, HashableMixin):
    """ResourceConfig, but hashable."""


def default_soft7_ote_function_config(
    entity: Union[type[SOFT7EntityInstance], SOFT7IdentityURIType, str],
) -> HashableFunctionConfig:
    """Create a default SOFT7 OTEAPI Function strategy configuration."""
    return HashableFunctionConfig(
        description="SOFT7 OTEAPI Function configuration.",
        functionType="SOFT7",
        configuration={
            "entity": (
                SOFT7IdentityURI(str(entity))
                if entity and isinstance(entity, (AnyUrl, str))
                else entity
            )
        },
    )
