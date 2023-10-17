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
from typing import TYPE_CHECKING, Annotated, cast as type_cast

import yaml
from oteapi.models import ResourceConfig
from otelib import OTEClient
from pydantic import Field, create_model, ConfigDict
from pydantic_core import PydanticUndefined

from s7.pydantic_models.oteapi import HashableResourceConfig
from s7.pydantic_models.soft7 import (
    SOFT7DataSource,
    SOFT7Entity,
    map_soft_to_py_types,
    parse_identity,
)

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Optional, Union, Literal

    from pydantic.main import Model

    from s7.pydantic_models.soft7 import (
        GetData,
        UnshapedPropertyType,
        SOFT7EntityProperty,
    )

    ShapedPropertyType = tuple[Union["ShapedPropertyType", UnshapedPropertyType], ...]
    PropertyType = Union[UnshapedPropertyType, ShapedPropertyType]


def _parse_inputs(
    data_model: "Union[SOFT7Entity, dict[str, Any], Path, str]",
    resource_config: "Union[HashableResourceConfig, ResourceConfig, dict[str, Any]]",
) -> tuple[SOFT7Entity, HashableResourceConfig]:
    """Parse inputs for creating a SOFT7 Data Source entity."""
    # Handle the case of data model being a string/path to a YAML file
    if isinstance(data_model, (str, Path)):
        data_model_path = Path(data_model).resolve()

        if not data_model_path.exists():
            raise FileNotFoundError(
                f"Could not find a data model YAML file at {data_model_path}"
            )

        data_model = yaml.safe_load(data_model_path.read_text(encoding="utf8"))

        if not isinstance(data_model, dict):
            raise TypeError(
                f"Data model YAML file at {data_model_path} did not contain a "
                "dictionary"
            )

    # Now the data model is either a SOFT7Entity instance or a dictionary, ready to be
    # used to create the SOFT7Entity instance.
    if isinstance(data_model, dict):
        data_model = SOFT7Entity(**data_model)

    if not isinstance(data_model, SOFT7Entity):
        raise TypeError(
            f"data_model must be a 'SOFT7Entity', instead it was a {type(data_model)}"
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

    return data_model, resource_config


def _generate_dimensions_docstring(data_model: "SOFT7Entity") -> str:
    """Generated a docstring for the dimensions model."""
    _, _, name = parse_identity(data_model.identity)

    attributes = (
        [
            f"{dimension_name} (int): {dimension_description}\n"
            for dimension_name, dimension_description in data_model.dimensions.items()
        ]
        if data_model.dimensions
        else []
    )

    return f"""DataSourceDimensions

    Dimensions for the {name} SOFT7 data source.

    SOFT7 Entity: {data_model.identity}

    {'Attributes:' if attributes else ''}
        {(' ' * 8).join(attributes)}
    """


def _generate_model_docstring(
    data_model: "SOFT7Entity", dimensions_data: "Model"
) -> str:
    """Generated a docstring for the data source model."""
    namespace, version, name = parse_identity(data_model.identity)

    description = data_model.description.replace("\n", "\n    ")

    dimensions = (
        [
            f"{dimension_name} (int): {dimension_description}\n"
            for dimension_name, dimension_description in data_model.dimensions.items()
        ]
        if data_model.dimensions
        else []
    )

    properties = []
    for property_name, property_value in data_model.properties.items():
        property_type = _generate_property_type(property_value, dimensions_data)

        properties.append(
            f"{property_name} ({type_cast('str', property_type)}): "
            f"{property_value.description}\n"
        )

    return f"""{name}

    {description}

    SOFT7 Entity Metadata:
        Identity: {data_model.identity}

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
) -> "PropertyType":
    """Generate a SOFT7 entity instance property type from a SOFT7EntityProperty."""
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

            dimension = getattr(dimensions, dimension_name)

            if not isinstance(dimension, int):
                raise TypeError(
                    f"Dimension values must be integers, got {type(dimension)} for "
                    f"{dimension_name!r}"
                )

            # The dimension defines the number of times the property type is repeated.
            property_type = type((property_type,) * dimension)  # type: ignore[assignment]

    return property_type  # type: ignore[return-value]


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

    def __get_data(name: str) -> "Any":
        f"""Get a named {category} from the data resource.

        Properties:
            name: The name of a datum in the resource's {category} to get.

        Returns:
            The value of the named datum in the resource's {category}.

        """
        if data is PydanticUndefined:
            if category in optional_categories:
                return None

            raise AttributeError(
                f"{name!r} is not defined for the resource's {category}"
            )

        if name in data:
            return data[name]

        raise AttributeError(
            f"{name!r} could not be determined for the resource's {category}"
        )

    return __get_data


def create_entity(
    data_model: "Union[SOFT7Entity, dict[str, Any], Path, str]",
    resource_config: "Union[HashableResourceConfig, ResourceConfig, dict[str, Any]]",
) -> type[SOFT7DataSource]:
    """Create and return a SOFT7 entity wrapped as a pydantic model.

    Parameters:
        data_model: A SOFT7 data model entity or a string/path to a YAML file of the
            data model.
        resource_config: A
            [`ResourceConfig`](https://emmc-asbl.github.io/oteapi-core/latest/
            all_models/#oteapi.models.ResourceConfig)
            or a valid dictionary that can be used to instantiate it.

    Returns:
        A SOFT7 entity class wrapped as a pydantic data model.

    """
    data_model, resource_config = _parse_inputs(data_model, resource_config)

    # Split the identity into its parts
    namespace, version, name = parse_identity(data_model.identity)

    # Create the dimensions model
    dimensions = (
        {
            dimension_name: Annotated[
                int,
                Field(
                    default_factory=lambda: _get_data(resource_config, "dimensions"),
                    description=dimension_description,
                ),
            ]
            for dimension_name, dimension_description in data_model.dimensions.items()
        }
        if data_model.dimensions
        else {}
    )

    dimensions_model = create_model(
        f"{name.replace(' ', '')}Dimensions",
        __config__=ConfigDict(extra="forbid", frozen=True, validate_default=False),
        __base__=None,
        __module__=__name__,
        __validators__=None,
        __cls_kwargs__={"__doc__": _generate_dimensions_docstring(data_model)},
        **dimensions,
    )
    dimensions_model_instance = dimensions_model()

    # Create the SOFT7 metadata fields for the data source model
    # All of these fields will be excluded from the data source model represntation as
    # well as the serialized JSON schema or Python dictionary.
    soft7_metadata: dict[str, tuple[Union[type, object], "Any"]] = {
        # Value must be a (<type>, <default>) or (<type>, <FieldInfo>) tuple
        # Note, Field() returns a FieldInfo instance (but is set to return an Any type).
        "dimensions": (
            dimensions_model,
            Field(dimensions_model_instance, repr=False, exclude=True),
        ),
        "identity": (
            data_model.model_fields["identity"].rebuild_annotation(),
            Field(data_model.identity, repr=False, exclude=True),
        ),
        "namespace": (str, Field(namespace, repr=False, exclude=True)),
        "version": (Optional[str], Field(version, repr=False, exclude=True)),
        "name": (str, Field(name, repr=False, exclude=True)),
    }

    # Generate the data source model class docstring
    __doc__ = _generate_model_docstring(data_model, dimensions_model_instance)

    # Create the data source model's properties
    field_definitions: dict[str, tuple["PropertyType", "Any"]] = {
        # Value must be a (<type>, <default>) or (<type>, <FieldInfo>) tuple
        # Note, Field() returns a FieldInfo instance (but is set to return an Any type).
        property_name: (
            _generate_property_type(property_value, dimensions_model_instance),
            Field(
                default_factory=lambda: _get_data(resource_config, "properties"),
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
        for property_name, property_value in data_model.properties.items()
    }

    # Ensure there is no overlap between the SOFT7 metadata fields and the data source
    # model properties and the data source model properties are not trying to hack the
    # attribute retrieval mechanism.
    if any(field.startswith("soft7___") for field in field_definitions):
        raise ValueError(
            "The data model properties are not allowed to overwrite or mock SOFT7 "
            "metadata fields."
        )

    return create_model(
        name.replace(" ", ""),
        __config__=None,
        __base__=SOFT7DataSource,
        __module__=__name__,
        __validators__=None,
        __cls_kwargs__={"__doc__": __doc__},
        **{
            # SOFT7 metadata fields
            **{f"soft7___{name}": value for name, value in soft7_metadata.items()},
            # Data source properties
            **field_definitions,
        },
    )
