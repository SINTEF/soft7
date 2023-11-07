"""Pydantic model for the SOFT7 data source instance."""
from pathlib import Path
from typing import TYPE_CHECKING, cast as type_cast

import yaml
from oteapi.models import ResourceConfig
from pydantic import ConfigDict, BaseModel

from s7.pydantic_models.oteapi import HashableResourceConfig
from s7.pydantic_models.soft7_entity import (
    CallableAttributesMixin,
    SOFT7Entity,
    map_soft_to_py_types,
    parse_identity,
)

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Union

    from pydantic.main import Model

    from s7.pydantic_models.soft7_entity import PropertyType, SOFT7EntityProperty


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


def parse_inputs(
    entity: "Union[SOFT7Entity, dict[str, Any], Path, str]",
    resource_config: "Union[HashableResourceConfig, ResourceConfig, dict[str, Any]]",
) -> tuple[SOFT7Entity, HashableResourceConfig]:
    """Parse inputs for creating a SOFT7 Data Source entity."""
    # Handle the case of data model being a string/path to a YAML file
    if isinstance(entity, (str, Path)):
        entity_path = Path(entity).resolve()

        if not entity_path.exists():
            raise FileNotFoundError(
                f"Could not find a data model YAML file at {entity_path}"
            )

        entity = yaml.safe_load(entity_path.read_text(encoding="utf8"))

        if not isinstance(entity, dict):
            raise TypeError(
                f"Data model YAML file at {entity_path} did not contain a " "dictionary"
            )

    # Now the data model is either a SOFT7Entity instance or a dictionary, ready to be
    # used to create the SOFT7Entity instance.
    if isinstance(entity, dict):
        entity = SOFT7Entity(**entity)

    if not isinstance(entity, SOFT7Entity):
        raise TypeError(
            f"entity must be a 'SOFT7Entity', instead it was a {type(entity)}"
        )

    # Handle the case of resource_config being a dictionary or a "pure" OTEAPI Core
    # ResourceConfig. We need to convert it to a HashableResourceConfig.
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
            "resource_config must be a 'HashableResourceConfig', instead it was a "
            f"{type(resource_config)}"
        )

    return entity, resource_config


def generate_dimensions_docstring(entity: "SOFT7Entity") -> str:
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


def generate_model_docstring(
    entity: "SOFT7Entity", property_types: dict[str, type["PropertyType"]]
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
        property_type = type_cast("str", property_types[property_name])

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
    value: "SOFT7EntityProperty", dimensions: "Model"
) -> "type[PropertyType]":
    """Generate a SOFT7 entity instance property type from a SOFT7EntityProperty."""
    if TYPE_CHECKING:  # pragma: no cover
        property_type: "type[PropertyType]"

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
