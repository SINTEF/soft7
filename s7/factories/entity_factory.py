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
    from typing import Any

    from s7.pydantic_models.soft7_entity import (
        ListPropertyType,
    )


LOGGER = logging.getLogger(__name__)


def create_entity(
    entity: SOFT7Entity | dict[str, Any] | Path | SOFT7IdentityURIType | str,
) -> type[SOFT7EntityInstance]:
    """Create and return a SOFT7 entity as a pydantic model.

    If the entity instance class has already been created, it will be returned
    as is from the `generated_classes` module.

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

    # Check if the entity has already been created
    existing_cls: type[SOFT7EntityInstance] | None = getattr(
        module_namespace, f"{name.replace(' ', '')}Entity", None
    )

    if existing_cls and issubclass(existing_cls, SOFT7EntityInstance):
        # Check the existing class' entity attribute
        if existing_cls.entity == entity:
            LOGGER.debug("The %s entity class already exists.", name)
            return existing_cls
        raise ValueError(
            f"The {name} entity class already exists, but with a different SOFT7 "
            "entity."
        )

    if existing_cls:
        raise ValueError(
            f"The {name} entity class already exists, but is not a SOFT7EntityInstance "
            "type."
        )

    LOGGER.debug("Creating the %s entity class anew.", name)

    # Create the entity model's dimensions
    dimensions: dict[str, tuple[type[int | None] | object, Any]] = (
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
        Dimensions = create_model(  # type: ignore[call-overload]
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
    properties: dict[str, tuple[type[ListPropertyType | None] | object, Any]] = {
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
                    for field in property_value.__class__.model_fields
                    if (
                        field not in ("description", "type")
                        and getattr(property_value, field)
                    )
                },
            ),
        )
        for property_name, property_value in entity.properties.items()
    }

    Properties = create_model(  # type: ignore[call-overload]
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
