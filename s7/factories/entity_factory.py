"""Generate SOFT7 entities, wrapped as pydantic data models."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from pydantic import ConfigDict, Field, create_model

from s7.pydantic_models.soft7_entity import (
    SOFT7Entity,
    SOFT7IdentityURIType,
    parse_identity,
    parse_input_entity,
)
from s7.pydantic_models.soft7_instance import (
    SOFT7EntityInstance,
    generate_dimensions_docstring,
    generate_list_property_type,
    generate_model_docstring,
    generate_properties_docstring,
)

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Union

    from s7.pydantic_models.soft7_entity import (
        ListPropertyType,
    )


LOGGER = logging.getLogger(__name__)


def create_entity(
    entity: Union[SOFT7Entity, dict[str, Any], Path, SOFT7IdentityURIType, str],
) -> type[SOFT7EntityInstance]:
    """Create and return a SOFT7 entity as a pydantic model.

    TODO: Utilize the `generated_classes` module and check whether we can return an
        already created model based on the inputs given here.

    TODO: Determine what to do with regards to differing inputs, but similar names.

    Parameters:
        entity: A SOFT7 entity (data model). It can be supplied as a URL reference,
            path or as a raw JSON/YAML string or Python `dict`.

    Returns:
        A SOFT7 entity as a pydantic model.

    """
    import s7.factories.generated_classes as module_namespace

    # Parse the input entity
    entity = parse_input_entity(entity)

    # Split the identity into its parts
    _, _, name = parse_identity(entity.identity)

    # Create the entity model's dimensions
    dimensions: dict[str, tuple[Union[type[Optional[int]], object], Any]] = (
        # Value must be a (<type>, <default>) or (<type>, <FieldInfo>) tuple
        # Note, Field() returns a FieldInfo instance (but is set to return an Any type).
        {
            dimension_name: (
                Optional[int],
                Field(None, description=dimension_description),
            )
            for dimension_name, dimension_description in entity.dimensions.items()
        }
        if entity.dimensions
        else {}
    )

    if dimensions:
        Dimensions = create_model(
            f"{name.replace(' ', '')}EntityDimensions",
            __config__=ConfigDict(extra="forbid", frozen=True, validate_default=False),
            __doc__=generate_dimensions_docstring(entity),
            __base__=None,
            __module__=module_namespace.__name__,
            __validators__=None,
            __cls_kwargs__=None,
            **dimensions,
        )

    # Pre-calculate property types
    property_types: dict[str, type[ListPropertyType]] = {
        property_name: generate_list_property_type(property_value)
        for property_name, property_value in entity.properties.items()
    }

    # Create the entity model's properties
    properties: dict[
        str, tuple[Union[type[Optional[ListPropertyType]], object], Any]
    ] = {
        # Value must be a (<type>, <default>) or (<type>, <FieldInfo>) tuple
        # Note, Field() returns a FieldInfo instance (but is set to return an Any type).
        property_name: (
            Optional[property_types[property_name]],
            Field(
                None,
                description=property_value.description or "",
                title=property_name.replace(" ", "_"),
                json_schema_extra={
                    f"x-soft7-{field}": getattr(property_value, field)
                    for field in property_value.model_fields
                    if (
                        field not in ("description", "type")
                        and getattr(property_value, field)
                    )
                },
            ),
        )
        for property_name, property_value in entity.properties.items()
    }

    Properties = create_model(
        f"{name.replace(' ', '')}EntityProperties",
        __config__=ConfigDict(extra="forbid", frozen=True, validate_default=False),
        __doc__=generate_properties_docstring(entity, property_types),
        __base__=None,
        __module__=module_namespace.__name__,
        __validators__=None,
        __cls_kwargs__=None,
        **properties,
    )

    # Generate the fields_definitions for the final model
    fields_definitions: dict[str, Any] = {
        # Value must be a (<type>, <default>) or (<type>, <FieldInfo>) tuple
        # Note, Field() returns a FieldInfo instance (but is set to return an Any type).
        "properties": (
            Properties,
            Field(description=f"The {name} SOFT7 entity properties."),
        )
    }
    if dimensions:
        fields_definitions["dimensions"] = (
            Dimensions,
            Field(description=f"The {name} SOFT7 entity dimensions."),
        )

    EntityInstance = create_model(
        f"{name.replace(' ', '')}Entity",
        __config__=None,
        __doc__=generate_model_docstring(entity, property_types),
        __base__=SOFT7EntityInstance,
        __module__=module_namespace.__name__,
        __validators__=None,
        __cls_kwargs__=None,
        **fields_definitions,
    )

    # Set the entity class variable
    EntityInstance.entity = entity

    # Register the classes with the generated_classes globals
    if dimensions:
        module_namespace.register_class(Dimensions)
    module_namespace.register_class(Properties)
    module_namespace.register_class(EntityInstance)

    return EntityInstance
