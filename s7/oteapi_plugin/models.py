"""Pydantic data models for the SOFT7 OTEAPI plugin."""

from __future__ import annotations

import sys
from typing import Annotated, Any, Optional

if sys.version_info >= (3, 10):
    from typing import Literal
else:
    from typing_extensions import Literal

from oteapi.models import AttrDict
from oteapi.strategies.mapping.mapping import MappingStrategyConfig
from pydantic import Field, field_validator

from s7.exceptions import EntityNotFound
from s7.factories import create_entity
from s7.pydantic_models.oteapi import HashableFunctionConfig
from s7.pydantic_models.soft7_entity import parse_identity, parse_input_entity
from s7.pydantic_models.soft7_instance import SOFT7EntityInstance

PrefixesType: Any = MappingStrategyConfig.model_fields["prefixes"].rebuild_annotation()
TriplesType: Any = MappingStrategyConfig.model_fields["triples"].rebuild_annotation()


class SOFT7GeneratorConfig(AttrDict):
    """SOFT7 Generator strategy-specific configuration.

    Inherit from the MappingStrategyConfig to include the prefixes and triples fields,
    as well as any connected validation or serialization functionality that may be part
    of the MappingStrategyConfig.
    """

    entity: Annotated[
        type[SOFT7EntityInstance],
        Field(description="The SOFT7 entity to be used for the generator."),
    ]

    # Data mapping information
    # Field added from a mapping strategy.
    prefixes: Annotated[
        Optional[PrefixesType],
        Field(description=MappingStrategyConfig.model_fields["prefixes"].description),
    ] = None
    triples: Annotated[
        Optional[TriplesType],
        Field(description=MappingStrategyConfig.model_fields["triples"].description),
    ] = None

    # Parsed data content
    # Field added from a parser strategy.
    content: Annotated[
        Optional[dict],
        Field(description="The parsed data content to be used for the generator."),
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
                f"SOFT7GeneratorConfig. Internal error: {exc}"
            ) from exc

        # Try to retrieve the SOFT7EntityInstance class from the generated_classes
        # module. If unsuccessful, we create it.
        _, _, name = parse_identity(entity.identity)
        name = name.replace(" ", "")

        try:
            import s7.factories.generated_classes as lookup_module

            return getattr(lookup_module, name)
        except AttributeError:
            return create_entity(entity)


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
