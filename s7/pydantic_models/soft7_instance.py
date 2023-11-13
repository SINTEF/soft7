"""Pydantic model for the SOFT7 data source instance."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar
from typing import cast as type_cast

import httpx
import yaml
from oteapi.models import ResourceConfig
from pydantic import (
    AnyHttpUrl,
    AnyUrl,
    BaseModel,
    ConfigDict,
    ValidationError,
    conlist,
    model_validator,
)

from s7.exceptions import EntityNotFound
from s7.pydantic_models.oteapi import HashableResourceConfig
from s7.pydantic_models.soft7_entity import (
    CallableAttributesMixin,
    SOFT7Entity,
    SOFT7IdentityURI,
    map_soft_to_py_types,
    parse_identity,
)

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, TypedDict

    from pydantic.main import Model

    from s7.pydantic_models.soft7_entity import PropertyType, SOFT7EntityProperty

    class SOFT7InstanceDict(TypedDict):
        """A dictionary representation of a SOFT7 instance."""

        dimensions: dict[str, int] | None
        properties: dict[str, Any]


LOGGER = logging.getLogger(__name__)


class SOFT7EntityInstance(BaseModel):
    """A SOFT7 entity instance."""

    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=False)

    # Metadata, i.e., the SOFT7 entity
    # Will not be part of fields on the instance
    entity: ClassVar[SOFT7Entity]

    dimensions: BaseModel | None
    properties: BaseModel

    @model_validator(mode="after")
    def validate_shaped_properties(self) -> SOFT7EntityInstance:
        """Validate that the shape of the properties matches the dimensions."""
        shaped_properties = {
            property_name: entity_property_value.shape
            for property_name, entity_property_value in self.entity.properties.items()
            if entity_property_value.shape
        }

        dimensions = self.dimensions.model_copy()
        properties = self.properties.model_copy()

        for property_name, shape in shaped_properties.items():
            property_value = getattr(properties, property_name)

            try:
                literal_dimensions = [
                    getattr(dimensions, dimension_name) for dimension_name in shape
                ]
            except AttributeError as exc:
                raise ValueError(
                    f"Property {property_name!r} is shaped, but not all the dimensions "
                    "are defined"
                ) from exc

            property_type = map_soft_to_py_types[
                getattr(self.entity.properties, property_name).type_
            ]

            # Go through the dimensions in reversed order and nest the property type in on
            # itself.
            for literal_dimension in reversed(literal_dimensions):
                # The literal dimension defines the number of times the property type is
                # repeated.
                property_type = conlist(property_type, min_length=literal_dimension, max_length=literal_dimension)  # type: ignore[misc]

            # Validate the property value against the property type
            try:
                property_type(property_value)
            except ValidationError as exc:
                raise ValueError(
                    f"Property {property_name!r} is shaped, but the shape does not match "
                    "the property value"
                ) from exc

        return self


class DataSourceDimensions(BaseModel, CallableAttributesMixin):
    """Dimensions for the SOFT7 data source.

    This doc-string will/should be overridden in the `create_datasource()` function.

    The configuration options:
    - `extra="forbid"`: Ensures an exception is raised if the instantiated data source
      tries to specify undefined properties.
    - `frozen=True`: Ensures an exception is raised if the instantiated data source
      tries to modify any properties, i.e., manually set an attribute value.
    - `validate_default=False`: Set explicitly (`False` is the default) to avoid a
      ValidationError when instantiating the data source. This is due to the properties
      being lazily retrieved from the data source.

    """

    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=False)


def parse_input_entity(
    entity: SOFT7Entity | dict[str, Any] | Path | AnyUrl | str,
) -> SOFT7Entity:
    """Parse input to a function that expects a SOFT7 entity."""
    # Handle the case of the entity being a string or a URL
    if isinstance(entity, (str, AnyUrl)):
        # If it's a string or URL, we expect to either be:
        # - A path to a YAML file.
        # - A SOFT7 entity identity.

        # Check if the string is a URL (i.e., a SOFT7 entity identity)
        try:
            SOFT7IdentityURI(entity)
        except ValidationError:
            # If it's not a URL, assume it's a path to a YAML file.
            entity = Path(entity)
        else:
            # If it is a URL, assume it's a SOFT7 entity identity.
            with httpx.Client(follow_redirects=True) as client:
                response = client.get(
                    str(entity), headers={"Accept": "application/yaml"}
                )

            if not response.is_success:
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as error:
                    raise EntityNotFound(
                        f"Could not retrieve SOFT7 entity online from {entity}"
                    ) from error

            # Using YAML parser, since _if_ the content is JSON, it's still valid YAML.
            # JSON is a subset of YAML.
            entity = yaml.safe_load(response.content)

    # Handle the case of the entity being a path to a YAML file
    if isinstance(entity, Path):
        entity_path = entity.resolve()

        if not entity_path.exists():
            raise EntityNotFound(f"Could not find an entity YAML file at {entity_path}")

        entity = yaml.safe_load(entity_path.read_text(encoding="utf8"))

    # Now the entity is either a SOFT7Entity instance or a dictionary, ready to be
    # used to create the SOFT7Entity instance.
    if isinstance(entity, dict):
        entity = SOFT7Entity(**entity)

    if not isinstance(entity, SOFT7Entity):
        raise TypeError(
            f"entity must be a 'SOFT7Entity', instead it was a {type(entity)}"
        )

    return entity


def parse_input_configs(
    resource_config: HashableResourceConfig
    | ResourceConfig
    | dict[str, Any]
    | AnyUrl
    | str,
) -> HashableResourceConfig:
    """Parse input to a function that expects a resource config."""
    # Handle the case of resource_config being a string or URL.
    if isinstance(resource_config, str):
        # Expect it to be either:
        # - A URL to a JSON/YAML resource online.
        # - A path to a JSON/YAML resource file.
        # - A JSON/YAML parseable string.

        # Check if the string is a URL
        try:
            AnyHttpUrl(resource_config)
        except ValidationError:
            # If it's not a URL, check whether it is a path to an (existing) file.
            resource_config_path = Path(resource_config).resolve()

            if resource_config_path.exists():
                # If it's a path to an existing file, assume it's a JSON/YAML file.
                resource_config = yaml.safe_load(
                    resource_config_path.read_text(encoding="utf8")
                )
            else:
                # If it's not a path to an existing file, assume it's a parseable
                # JSON/YAML
                resource_config = yaml.safe_load(resource_config)
        else:
            # If it is a URL, assume it's a URL to a JSON/YAML resource online.
            with httpx.Client(follow_redirects=True) as client:
                response = client.get(
                    str(resource_config), headers={"Accept": "application/yaml"}
                )

            if not response.is_success:
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as error:
                    raise EntityNotFound(
                        f"Could not retrieve resource config online from "
                        f"{resource_config}"
                    ) from error

            # Using YAML parser, since _if_ the content is JSON, it's still valid YAML.
            # JSON is a subset of YAML.
            resource_config = yaml.safe_load(response.content)

    # Handle the case of resource_config being a dictionary or a "pure" OTEAPI Core
    # ResourceConfig: We need to convert it to a HashableResourceConfig.
    if isinstance(resource_config, dict):
        resource_config = HashableResourceConfig(**resource_config)

    if isinstance(resource_config, ResourceConfig) and not isinstance(
        resource_config, HashableResourceConfig
    ):
        resource_config = HashableResourceConfig(
            **resource_config.model_dump(exclude_defaults=True)
        )

    if not isinstance(resource_config, HashableResourceConfig):
        raise TypeError(
            "resource_config must be an OTEAPI Core 'ResourceConfig', instead it was a "
            f"{type(resource_config)}"
        )

    return resource_config


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
    entity: SOFT7Entity, property_types: dict[str, type[PropertyType]]
) -> str:
    """Generated a docstring for the properties model."""
    _, _, name = parse_identity(entity.identity)

    attributes = []
    for property_name, property_value in entity.properties.items():
        property_type = type_cast("str", property_types[property_name])

        attributes.append(
            f"{property_name} ({property_type}): " f"{property_value.description}\n"
        )

    return f"""{name.replace(' ', '')}Properties

    Properties for the {name} SOFT7 data source.

    SOFT7 Entity: {entity.identity}

    Attributes:
        {(' ' * 8).join(attributes)}
    """


def generate_model_docstring(
    entity: SOFT7Entity, property_types: dict[str, type[PropertyType]]
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
        property_type = type_cast("str", property_types[property_name].__name__)

        properties.append(
            f"{property_name} ({property_type}): " f"{property_value.description}\n"
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
    if TYPE_CHECKING:  # pragma: no cover
        property_type: type[PropertyType]

    # Get the Python type for the property as defined by SOFT7 data types.
    property_type = map_soft_to_py_types[value.type_]

    if value.shape:
        # Go through the dimensions in reversed order and nest the property type in on
        # itself.
        for dimension_name in reversed(value.shape):
            if not hasattr(dimensions, dimension_name):
                raise ValueError(
                    f"Dimension {dimension_name!r} is not defined in the data model"
                )

            dimension: int = getattr(dimensions, dimension_name)

            if not isinstance(dimension, int):
                raise TypeError(
                    f"Dimension values must be integers, got {type(dimension)} for "
                    f"{dimension_name!r}"
                )

            # The dimension defines the number of times the property type is repeated.
            property_type = tuple[(property_type,) * dimension]  # type: ignore[misc]

    return property_type


def generate_list_property_type(value: SOFT7EntityProperty) -> type[PropertyType]:
    """Generate a SOFT7 entity instance property type from a SOFT7EntityProperty.

    But make it up of lists, not tuples.
    This makes it unnecessary to retrieve the actual dimension values, as they are not
    needed.
    """
    from s7.factories.entity_factory import create_entity

    if TYPE_CHECKING:  # pragma: no cover
        property_type: type[PropertyType]

    # Get the Python type for the property as defined by SOFT7 data types.
    property_type = map_soft_to_py_types[value.type_]

    if value.type_ == "ref":
        # If the property type is a BaseModel, it's a SOFT7 entity instance.
        # We need to get the property type for the SOFT7 entity instance.
        property_type = create_entity(value.ref)

    if value.shape:
        # For each dimension listed in shape, nest the property type in on itself.
        for _ in range(len(value.shape)):
            property_type = list[property_type]

    return property_type
