"""Generate SOFT7 entity instances based on basic information:

1. Data source (DB, File, Webpage, ...)
2. Generic data source parser
3. Data source parser configuration
4. SOFT7 entity (data model).

Parts 2 and 3 are together considered to produce the "specific parser".
Parts 1 through 3 are provided through a single dictionary based on the
`ResourceConfig` from `oteapi.models`.

"""
import json
from pathlib import Path
from typing import TYPE_CHECKING, Optional, cast as type_cast

import yaml
from oteapi.models import ResourceConfig
from otelib import OTEClient
from pydantic import Field, create_model, ConfigDict, BaseModel
from pydantic_core import PydanticUndefined

from s7.pydantic_models.oteapi import HashableResourceConfig
from s7.pydantic_models.soft7 import (
    SOFT7DataSource,
    SOFT7Entity,
    CallableAttributesMixin,
    map_soft_to_py_types,
    parse_identity,
)

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Union, Literal

    from pydantic.main import Model

    from s7.pydantic_models.soft7 import (
        GetData,
        PropertyType,
        SOFT7EntityProperty,
    )


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


def _parse_inputs(
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


def _generate_dimensions_docstring(entity: "SOFT7Entity") -> str:
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


def _generate_model_docstring(
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


def _generate_property_type(
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


def _get_data(
    config: HashableResourceConfig,
    category: 'Literal["dimensions", "properties"]',
    *,
    url: "Optional[str]" = None,
) -> "GetData":
    """Get a datum from category.

    Everything in the __get_data() function will not be called until the first time
    the attribute `name` is accessed.

    To do something "lazy", it should be moved to the __get_data() function.
    To instead pre-cache something, it should be moved outside of the __get_data()
    function.

    Parameters:
        config: The OTEAPI data resource configuration.
        category: Either of the top-level SOFT7 Entity fields `dimensions` or
            `properties`.
        url: The base URL of the OTEAPI service instance to use.

    Returns:
        A function that will return the value of a named dimension or property.

    """
    # OTEAPI Pipeline
    client = OTEClient(url or "http://localhost:8080")
    data_resource = client.create_dataresource(**config.model_dump())
    result: "dict[str, Any]" = json.loads(data_resource.get())

    # TODO: This whole section should be updated to properly resolve how data is to be
    # retrieved from external sources through the OTEAPI. For now, we just "say" that
    # the `result` contains keys equal to the top-level SOFT7 entity fields, i.e., what
    # is called `category` here.
    data = result.get(category, PydanticUndefined)

    optional_categories = [
        field_name
        for field_name, field_info in SOFT7Entity.model_fields.items()
        if field_info.is_required() is False
    ]

    # Remove unused variables from memory
    del client
    del data_resource
    del result

    def __get_data(soft7_property: str) -> "Any":
        """Get a named datum (property or dimension) from the data resource.

        Properties:
            soft7_property: The name of a datum to get, i.e., the SOFT7 data resource
                property (or dimension).

        Returns:
            The value of the SOFT7 data resource property (or dimension).

        """
        if data is PydanticUndefined:
            if category in optional_categories:
                return None

            raise AttributeError(
                f"{soft7_property!r} is not defined for the resource's {category}"
            )

        if soft7_property in data:
            return data[soft7_property]

        raise AttributeError(
            f"{soft7_property!r} could not be determined for the resource's {category}"
        )

    return __get_data


def create_datasource(
    entity: "Union[SOFT7Entity, dict[str, Any], Path, str]",
    resource_config: "Union[HashableResourceConfig, ResourceConfig, dict[str, Any]]",
    oteapi_url: "Optional[str]" = None,
) -> SOFT7DataSource:
    """Create and return a SOFT7 Data Source from  wrapped as a pydantic model.

    Parameters:
        entity: A SOFT7 entity (data model) or a string/path to a YAML file of the
            entity.
        resource_config: A
            [`ResourceConfig`](https://emmc-asbl.github.io/oteapi-core/latest/
            all_models/#oteapi.models.ResourceConfig)
            or a valid dictionary that can be used to instantiate it.
        oteapi_url: The base URL of the OTEAPI service to use.

    Returns:
        A SOFT7 entity class wrapped as a pydantic data model.

    """
    entity, resource_config = _parse_inputs(entity, resource_config)

    # Split the identity into its parts
    namespace, version, name = parse_identity(entity.identity)

    # Create the dimensions model
    dimensions: dict[str, tuple[type[int], "GetData"]] = (
        # Value must be a (<type>, <default>) or (<type>, <FieldInfo>) tuple
        # Note, Field() returns a FieldInfo instance (but is set to return an Any type).
        {
            dimension_name: (
                int,
                Field(
                    default_factory=lambda: _get_data(
                        resource_config, "dimensions", url=oteapi_url
                    ),
                    description=dimension_description,
                ),
            )
            for dimension_name, dimension_description in entity.dimensions.items()
        }
        if entity.dimensions
        else {}
    )

    dimensions_model = create_model(
        f"{name.replace(' ', '')}Dimensions",
        __config__=None,
        __base__=DataSourceDimensions,
        __module__=__name__,
        __validators__=None,
        __cls_kwargs__=None,
        **dimensions,
    )

    # Update the class docstring
    dimensions_model.__doc__ = _generate_dimensions_docstring(entity)

    dimensions_model_instance = dimensions_model()

    # Create the SOFT7 metadata fields for the data source model
    # All of these fields will be excluded from the data source model representation as
    # well as the serialized JSON schema or Python dictionary.
    soft7_metadata: dict[str, tuple["Union[type, object]", "Any"]] = {
        # Value must be a (<type>, <default>) or (<type>, <FieldInfo>) tuple
        # Note, Field() returns a FieldInfo instance (but is set to return an Any type).
        "dimensions": (
            dimensions_model,
            Field(dimensions_model_instance, repr=False, exclude=True),
        ),
        "identity": (
            entity.model_fields["identity"].rebuild_annotation(),
            Field(entity.identity, repr=False, exclude=True),
        ),
        "namespace": (str, Field(namespace, repr=False, exclude=True)),
        "version": (Optional[str], Field(version, repr=False, exclude=True)),
        "name": (str, Field(name, repr=False, exclude=True)),
    }

    # Pre-calculate property types
    property_types: dict[str, type["PropertyType"]] = {
        property_name: _generate_property_type(
            property_value, dimensions_model_instance
        )
        for property_name, property_value in entity.properties.items()
    }

    # Generate the data source model class docstring
    __doc__ = _generate_model_docstring(entity, property_types)

    # Create the data source model's properties
    field_definitions: dict[str, tuple["type[PropertyType]", "GetData"]] = {
        # Value must be a (<type>, <default>) or (<type>, <FieldInfo>) tuple
        # Note, Field() returns a FieldInfo instance (but is set to return an Any type).
        property_name: (
            property_types[property_name],
            Field(
                default_factory=lambda: _get_data(
                    resource_config, "properties", url=oteapi_url
                ),
                description=property_value.description or "",
                title=property_name.replace(" ", "_"),
                json_schema_extra={
                    f"x-soft7-{field}": getattr(property_value, field)
                    for field in property_value.model_fields
                    if (
                        field not in ("description", "type_")
                        and getattr(property_value, field)
                    )
                },
            ),
        )
        for property_name, property_value in entity.properties.items()
    }

    # Ensure there is no overlap between the SOFT7 metadata fields and the data source
    # model properties and the data source model properties are not trying to hack the
    # attribute retrieval mechanism.
    if any(field.startswith("soft7___") for field in field_definitions):
        raise ValueError(
            "The data model properties are not allowed to overwrite or mock SOFT7 "
            "metadata fields."
        )

    DataSourceModel = create_model(
        name.replace(" ", ""),
        __config__=None,
        __base__=SOFT7DataSource,
        __module__=__name__,
        __validators__=None,
        __cls_kwargs__=None,
        **{
            # SOFT7 metadata fields
            **{f"soft7___{name}": value for name, value in soft7_metadata.items()},
            # Data source properties
            **field_definitions,
        },
    )

    # Update the class docstring
    DataSourceModel.__doc__ = __doc__

    return DataSourceModel()  # type: ignore[call-arg]
