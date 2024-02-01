"""Pydantic data models for the SOFT7 OTEAPI plugin."""

from __future__ import annotations

from typing import Annotated, Any, Literal, Optional

from oteapi.models import AttrDict, DataCacheConfig
from pydantic import Field, field_validator

from s7.exceptions import EntityNotFound
from s7.factories.entity_factory import create_entity_instance
from s7.pydantic_models.oteapi import HashableFunctionConfig
from s7.pydantic_models.soft7_entity import parse_identity
from s7.pydantic_models.soft7_instance import SOFT7EntityInstance, parse_input_entity


class SOFT7GeneratorConfig(AttrDict):
    """SOFT7 Generator strategy-specific configuration."""

    entity: Annotated[
        type[SOFT7EntityInstance],
        Field(description="The SOFT7 entity to be used for the generator."),
    ]

    datacache_config: Annotated[
        Optional[DataCacheConfig],
        Field(
            description=(
                "Configurations for the data cache for storing the downloaded file "
                "content."
            ),
        ),
    ] = None

    @field_validator("entity", mode="before")
    @classmethod
    def ensure_entity_is_cls(cls, value: Any) -> type[SOFT7EntityInstance]:
        """Ensure the given entity is a SOFT7EntityInstance class."""
        if isinstance(value, type) and issubclass(value, SOFT7EntityInstance):
            # The entity is already a SOFT7EntityInstance (or subclass) type.
            return value

        # The entity is not a SOFT7EntityInstance (or subclass) type.
        # Try to parse it as a SOFT7 Entity.
        try:
            entity = parse_input_entity(value)
        except (TypeError, EntityNotFound) as exc:
            raise ValueError(
                f"Invalid value {value!r} for the 'entity' field in "
                "SOFT7GeneratorConfig."
            ) from exc

        # Try to retrieve the SOFT7EntityInstance class from the generated_classes
        # module. If unsuccessful, we create it.
        _, _, name = parse_identity(entity.identity)
        name = name.replace(" ", "")

        try:
            import s7.factories.generated_classes as lookup_module

            return getattr(lookup_module, name)
        except AttributeError:
            return create_entity_instance(entity)


class SOFT7FunctionConfig(HashableFunctionConfig):
    """SOFT7 OTEAPI Function strategy configuration."""

    functionType: Annotated[
        Literal["soft7", "SOFT7"],
        Field(
            description=HashableFunctionConfig.model_fields["functionType"].description,
        ),
    ]

    configuration: Annotated[
        SOFT7GeneratorConfig, Field(description=SOFT7GeneratorConfig.__doc__)
    ]
