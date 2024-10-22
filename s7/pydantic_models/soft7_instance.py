"""Pydantic model for the SOFT7 data source instance."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar, Optional, cast, get_args

from pydantic import (
    AnyUrl,
    BaseModel,
    ConfigDict,
    TypeAdapter,
    ValidationError,
    conlist,
    model_validator,
)
from pydantic._internal._repr import PlainRepr, display_as_type

from s7.pydantic_models.soft7_entity import (
    SOFT7Entity,
    SOFT7IdentityURIType,
    map_soft_to_py_types,
    parse_identity,
)

if TYPE_CHECKING:  # pragma: no cover
    from typing import Union

    from pydantic.main import Model

    from s7.pydantic_models.soft7_entity import (
        ListPropertyType,
        PropertyType,
        SOFT7EntityProperty,
        UnshapedPropertyType,
    )


LOGGER = logging.getLogger(__name__)


class SOFT7EntityInstance(BaseModel):
    """A SOFT7 entity instance."""

    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=False)

    # Metadata, i.e., the SOFT7 entity
    # Will not be part of fields on the instance
    entity: ClassVar[SOFT7Entity]

    dimensions: Optional[BaseModel] = None
    properties: BaseModel

    @model_validator(mode="after")
    def validate_shaped_properties(self) -> SOFT7EntityInstance:
        """Validate that the shape of the properties matches the dimensions."""
        shaped_properties = {
            property_name: entity_property_value.shape
            for property_name, entity_property_value in self.entity.properties.items()
            if entity_property_value.shape
        }

        for property_name, shape in shaped_properties.items():
            property_value = getattr(self.properties, property_name)

            # Let us ignore None valued properties
            if property_value is None:
                continue

            # Retrieve the dimension values for dimensions in the shape
            if self.dimensions is None:
                if shape:
                    raise ValueError(
                        f"Property {property_name!r} is shaped, but no dimensions are "
                        "defined for the instance."
                    )
                literal_dimensions = []
            else:
                try:
                    literal_dimensions = [
                        getattr(self.dimensions, dimension_name)
                        for dimension_name in shape
                    ]
                except AttributeError as exc:
                    raise ValueError(
                        f"Property {property_name!r} is shaped, but not all the "
                        "dimensions are defined"
                    ) from exc

            if not all(isinstance(_, int) for _ in literal_dimensions):
                raise TypeError(
                    f"Property {property_name!r} is shaped, but not all the dimensions "
                    "are integers for its shape."
                )

            if TYPE_CHECKING:  # pragma: no cover
                literal_dimensions = cast(list[int], literal_dimensions)

            # Get the inner most (non-list) Python type/class
            property_type = self.properties.model_fields[property_name].annotation

            while True:
                _temp = property_type
                property_type = next(iter(get_args(property_type)), property_type)
                if property_type == _temp:
                    break

            if property_type is None:
                raise TypeError(
                    "Could not determine the inner most Python type for property"
                    f"{property_name!r}"
                )

            # Sanity checks
            if not issubclass(property_type, BaseModel):
                # Ensure the property type matches the property type defined in the
                # entity.
                try:
                    entity_property_type = map_soft_to_py_types[
                        self.entity.properties[property_name].type  # type: ignore[index]
                    ]
                except KeyError as exc:
                    raise ValueError(
                        f"Property {property_name!r} is a shaped, non-referenced type "
                        "property, but the given SOFT property type could not be "
                        "mapped to a Python type."
                    ) from exc

                if property_type != entity_property_type:
                    raise ValueError(
                        f"Property {property_name!r} is a shaped, non-referenced type "
                        "property, but the inner most Python type does not match the "
                        "expected Python type given from the entity property's `type`."
                    )

            # Go through the dimensions in reversed order and nest the property type in
            # on itself.
            for literal_dimension in reversed(literal_dimensions):
                # The literal dimension defines the number of times the property type is
                # repeated.
                property_type = conlist(
                    property_type,
                    min_length=literal_dimension,
                    max_length=literal_dimension,
                )

            # Validate the property value against the property type
            try:
                TypeAdapter(property_type).validate_python(property_value)
            except ValidationError as exc:
                raise ValueError(
                    f"Property {property_name!r} is shaped, but the shape does not "
                    "match the property value"
                ) from exc

        return self


def generate_dimensions_docstring(entity: SOFT7Entity) -> str:
    """Generated a docstring for the dimensions model."""
    _, _, name = parse_identity(entity.identity)

    attributes = (
        [
            f"{dimension_name} (int): {dimension_description}\n"
            for dimension_name, dimension_description in entity.dimensions.items()
        ]
        if entity.dimensions
        else []
    )

    return f"""{name.replace(' ', '')}Dimensions

    Dimensions for the {name} SOFT7 data source.

    SOFT7 Entity: {entity.identity}

    {'Attributes:' if attributes else ''}
        {(' ' * 8).join(attributes)}
    """


def generate_properties_docstring(
    entity: SOFT7Entity,
    property_types: Union[
        dict[str, type[PropertyType]], dict[str, type[ListPropertyType]]
    ],
) -> str:
    """Generated a docstring for the properties model."""
    _, _, name = parse_identity(entity.identity)

    attributes = []
    for property_name, property_value in entity.properties.items():
        property_type_repr = PlainRepr(display_as_type(property_types[property_name]))

        attributes.append(
            f"{property_name} ({property_type_repr}): "
            f"{property_value.description}\n"
        )

    return f"""{name.replace(' ', '')}Properties

    Properties for the {name} SOFT7 data source.

    SOFT7 Entity: {entity.identity}

    Attributes:
        {(' ' * 8).join(attributes)}
    """


def generate_model_docstring(
    entity: SOFT7Entity,
    property_types: Union[
        dict[str, type[PropertyType]], dict[str, type[ListPropertyType]]
    ],
) -> str:
    """Generated a docstring for the data source model."""
    namespace, version, name = parse_identity(entity.identity)

    description = entity.description.replace("\n", "\n    ")

    dimensions = (
        [
            f"{dimension_name} (int): {dimension_description}\n"
            for dimension_name, dimension_description in entity.dimensions.items()
        ]
        if entity.dimensions
        else []
    )

    properties = []
    for property_name, property_value in entity.properties.items():
        property_type_repr = PlainRepr(display_as_type(property_types[property_name]))

        properties.append(
            f"{property_name} ({property_type_repr}): "
            f"{property_value.description}\n"
        )

    return f"""{name}

    {description}

    SOFT7 Entity Metadata:
        Identity: {entity.identity}

        Namespace: {namespace}
        Version: {version if version else "N/A"}
        Name: {name}

    {'Dimensions:' if dimensions else 'There are no dimensions defined.'}
        {(' ' * 8).join(dimensions)}
    Attributes:
        {(' ' * 8).join(properties)}
    """


def generate_property_type(
    value: SOFT7EntityProperty, dimensions: Model
) -> type[PropertyType]:
    """Generate a SOFT7 entity instance property type from a SOFT7EntityProperty."""
    from s7.factories import create_entity

    # Get the Python type for the property as defined by SOFT7 data types.
    property_type: Union[
        type[UnshapedPropertyType], SOFT7IdentityURIType
    ] = map_soft_to_py_types.get(
        value.type, value.type  # type: ignore[arg-type]
    )

    if isinstance(property_type, AnyUrl):
        # If the property type is a SOFT7IdentityURI, it means it should be a
        # SOFT7 Entity instance, NOT a SOFT7 Data source. Highlander rules apply:
        # There can be only one Data source per generated data source.
        property_type: type[SOFT7EntityInstance] = create_entity(value.type)  # type: ignore[no-redef]

    if value.shape:
        # Go through the dimensions in reversed order and nest the property type in on
        # itself.
        for dimension_name in reversed(value.shape):
            dimension: Optional[int] = getattr(dimensions, dimension_name, None)

            if dimension is None:
                raise ValueError(
                    f"Dimension {dimension_name!r} is not defined in the data model "
                    "or cannot be resolved."
                )

            if not isinstance(dimension, int):
                raise TypeError(
                    f"Dimension values must be integers, got {type(dimension)} for "
                    f"{dimension_name!r}."
                )

            # The dimension defines the number of times the property type is repeated.
            property_type: type[PropertyType] = tuple[(property_type,) * dimension]  # type: ignore[misc,no-redef]

    return property_type  # type: ignore[return-value]


def generate_list_property_type(value: SOFT7EntityProperty) -> type[ListPropertyType]:
    """Generate a SOFT7 entity instance property type from a SOFT7EntityProperty.

    But make it up of lists, not tuples.
    This makes it unnecessary to retrieve the actual dimension values, as they are not
    needed.
    """
    from s7.factories import create_entity

    # Get the Python type for the property as defined by SOFT7 data types.
    property_type: Union[
        type[UnshapedPropertyType], SOFT7IdentityURIType
    ] = map_soft_to_py_types.get(
        value.type, value.type  # type: ignore[arg-type]
    )

    if isinstance(value.type, AnyUrl):
        # If the property type is a SOFT7IdentityURI, it means it should be another
        # SOFT7 entity instance.
        # We need to get the property type for the SOFT7 entity instance.
        property_type: type[SOFT7EntityInstance] = create_entity(value.type)  # type: ignore[no-redef]

    if value.shape:
        # For each dimension listed in shape, nest the property type in on itself.
        for _ in range(len(value.shape)):
            property_type: type[ListPropertyType] = list[property_type]  # type: ignore[valid-type,no-redef]

    return property_type  # type: ignore[return-value]
