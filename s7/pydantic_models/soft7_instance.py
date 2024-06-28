"""Pydantic model for the SOFT7 data source instance."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Optional, cast, get_args

import httpx
import yaml
from pydantic import (
    AnyHttpUrl,
    AnyUrl,
    BaseModel,
    ConfigDict,
    TypeAdapter,
    ValidationError,
    conlist,
    model_validator,
)
from pydantic._internal._repr import PlainRepr, display_as_type

from s7.exceptions import ConfigsNotFound, EntityNotFound, S7EntityError
from s7.pydantic_models.oteapi import (
    HashableFunctionConfig,
    HashableMappingConfig,
    HashableResourceConfig,
    default_soft7_ote_function_config,
)
from s7.pydantic_models.soft7_entity import (
    SOFT7Entity,
    s7_identity_uri,
    S7IdentityUriType,
    map_soft_to_py_types,
    parse_identity,
)

if TYPE_CHECKING:  # pragma: no cover
    import sys
    from typing import Any, TypedDict, Union

    if sys.version_info >= (3, 10):
        from typing import Literal
    else:
        from typing_extensions import Literal

    from oteapi.models import GenericConfig
    from pydantic.main import Model

    from s7.pydantic_models.soft7_entity import (
        ListPropertyType,
        PropertyType,
        SOFT7EntityProperty,
        UnshapedPropertyType,
    )

    class SOFT7InstanceDict(TypedDict):
        """A dictionary representation of a SOFT7 instance."""

        dimensions: Optional[dict[str, int]]
        properties: dict[str, Any]

    class GetDataOptionalMapping(TypedDict, total=False):
        """A dictionary of the various required OTEAPI strategy configurations needed
        for the _get_data() OTEAPI pipeline.
        This is a special case where the mapping is implicit, i.e., the mapping is
        expected to be 1:1 between the data resource and the entity.
        """

        mapping: HashableMappingConfig

    class GetDataConfigDict(GetDataOptionalMapping):
        """A dictionary of the various required OTEAPI strategy configurations needed
        for the _get_data() OTEAPI pipeline."""

        dataresource: HashableResourceConfig
        function: HashableFunctionConfig


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

        dimensions = self.dimensions.model_copy() if self.dimensions else {}
        properties = self.properties.model_copy()

        for property_name, shape in shaped_properties.items():
            property_value = getattr(properties, property_name)

            # Let us ignore None valued properties
            if property_value is None:
                continue

            # Retrieve the dimension values for dimensions in the shape
            try:
                literal_dimensions = [
                    getattr(dimensions, dimension_name) for dimension_name in shape
                ]
            except AttributeError as exc:
                raise ValueError(
                    f"Property {property_name!r} is shaped, but not all the dimensions "
                    "are defined"
                ) from exc

            if not all(isinstance(_, int) for _ in literal_dimensions):
                raise TypeError(
                    f"Property {property_name!r} is shaped, but not all the dimensions "
                    "are integers for its shape."
                )

            if TYPE_CHECKING:  # pragma: no cover
                literal_dimensions = cast(list[int], literal_dimensions)

            # Get the inner most (non-list) Python type/class
            property_type = properties.model_fields[property_name].annotation

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


def parse_input_entity(
    entity: Union[SOFT7Entity, dict[str, Any], Path, AnyUrl, str],
) -> SOFT7Entity:
    """Parse input to a function that expects a SOFT7 entity."""
    # Handle the case of the entity being a string or a URL
    if isinstance(entity, (AnyUrl, str)):
        # If it's a string or URL, we expect to either be:
        # - A path to a YAML file.
        # - A SOFT7 entity identity.

        # Check if it is a URL (i.e., a SOFT7 entity identity)
        try:
            s7_identity_uri(str(entity))
        except ValidationError as exc:
            if not isinstance(entity, str):
                raise TypeError("Expected entity to be a str at this point") from exc

            # If it's not a URL, check whether it is a path to an (existing) file.
            entity_path = Path(entity).resolve()

            if entity_path.exists():
                # If it's a path to an existing file, assume it's a JSON/YAML file.
                entity = yaml.safe_load(entity_path.read_text(encoding="utf8"))
            else:
                # If it's not a path to an existing file, assume it's a parseable
                # JSON/YAML
                entity = yaml.safe_load(entity)
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
    configs: Union[
        GetDataConfigDict,
        dict[str, Union[GenericConfig, dict[str, Any], Path, AnyUrl, str]],
        Path,
        AnyUrl,
        str,
    ],
    entity_instance: Optional[
        Union[type[SOFT7EntityInstance], S7IdentityUriType, str]
    ] = None,
) -> GetDataConfigDict:
    """Parse input to a function that expects a resource config."""
    name_to_config_type_mapping: dict[
        str,
        type[
            Union[HashableResourceConfig, HashableFunctionConfig, HashableMappingConfig]
        ],
    ] = {
        "dataresource": HashableResourceConfig,
        "mapping": HashableMappingConfig,
        "function": HashableFunctionConfig,
    }

    # Handle the case of configs being a string or URL.
    if isinstance(configs, (AnyUrl, str)):
        # Expect it to be either:
        # - A URL to a JSON/YAML resource online.
        # - A path to a JSON/YAML resource file.
        # - A JSON/YAML parseable string.

        # Check if the string is a URL
        try:
            AnyHttpUrl(str(configs))
        except ValidationError as exc:
            if not isinstance(configs, str):
                raise TypeError("Expected configs to be a str at this point") from exc

            # If it's not a URL, check whether it is a path to an (existing) file.
            configs_path = Path(configs).resolve()

            if configs_path.exists():
                # If it's a path to an existing file, assume it's a JSON/YAML file.
                configs = yaml.safe_load(configs_path.read_text(encoding="utf8"))
            else:
                # If it's not a path to an existing file, assume it's a parseable
                # JSON/YAML
                configs = yaml.safe_load(configs)
        else:
            # If it is a URL, assume it's a URL to a JSON/YAML resource online.
            with httpx.Client(follow_redirects=True) as client:
                response = client.get(
                    str(configs), headers={"Accept": "application/yaml"}
                )

            if not response.is_success:
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as error:
                    raise EntityNotFound(
                        f"Could not retrieve configurations online from {configs}"
                    ) from error

            # Using YAML parser, since _if_ the content is JSON, it's still valid YAML.
            # JSON is a subset of YAML.
            configs = yaml.safe_load(response.content)

    # Handle the case of configs being a path to a JSON/YAML file.
    if isinstance(configs, Path):
        configs_path = configs.resolve()

        if not configs_path.exists():
            raise ConfigsNotFound(
                f"Could not find a configs YAML file at {configs_path}"
            )

        configs = yaml.safe_load(configs_path.read_text(encoding="utf8"))

    # Expect configs to be a dictionary at this point.
    if not isinstance(configs, dict):
        raise TypeError(f"configs must be a 'dict', instead it was a {type(configs)}")

    for name, config in configs.items():
        if name and not isinstance(name, str):
            raise TypeError("The config name must be a string")

        if name not in name_to_config_type_mapping:
            raise ValueError(
                f"The config name {name!r} is not a valid config name. "
                f"Valid config names are: {', '.join(name_to_config_type_mapping)}"
            )

        if TYPE_CHECKING:  # pragma: no cover
            name = cast(Literal["dataresource", "mapping", "function"], name)

        # Handle the case of the config being a string or URL.
        if isinstance(config, (AnyUrl, str)):
            # Expect it to be either:
            # - A URL to a JSON/YAML config online.
            # - A path to a JSON/YAML config file.
            # - A JSON/YAML parseable string.

            # Check if the string is a URL
            try:
                AnyHttpUrl(str(config))
            except ValidationError as exc:
                if not isinstance(config, str):
                    raise TypeError(
                        "Expected config to be a str at this point"
                    ) from exc

                # If it's not a URL, check whether it is a path to an (existing)
                # file.
                config_path = Path(config).resolve()

                if config_path.exists():
                    # If it's a path to an existing file, assume it's a JSON/YAML
                    # file.
                    config = yaml.safe_load(  # noqa: PLW2901
                        config_path.read_text(encoding="utf8")
                    )
                else:
                    # If it's not a path to an existing file, assume it's a
                    # parseable JSON/YAML
                    config = yaml.safe_load(config)  # noqa: PLW2901
            else:
                # If it is a URL, assume it's a URL to a JSON/YAML resource online.
                with httpx.Client(follow_redirects=True) as client:
                    response = client.get(
                        str(config), headers={"Accept": "application/yaml"}
                    )

                if not response.is_success:
                    try:
                        response.raise_for_status()
                    except httpx.HTTPStatusError as error:
                        raise ConfigsNotFound(
                            f"Could not retrieve {name} config online from {config}"
                        ) from error

                # Using YAML parser, since _if_ the content is JSON, it's still
                # valid YAML. JSON is a subset of YAML.
                config = yaml.safe_load(response.content)  # noqa: PLW2901

        # Ensure all values are Hashable*Config instances if they are dictionaries
        # or Hashable*Config instances.
        if isinstance(config, (BaseModel, dict)):
            try:
                configs[name] = name_to_config_type_mapping[name](
                    **(config if isinstance(config, dict) else config.model_dump())
                )
            except ValidationError as exc:
                raise S7EntityError(
                    f"The {name!r} configuration provided could not be validated "
                    f"as a proper OTEAPI {name.capitalize()}Config"
                ) from exc

        # Allow function to be None, as it has a default value.
        # Otherwise, raise.
        elif name == "function" and config is None:
            if entity_instance is None:
                raise EntityNotFound(
                    "The entity must be provided if the function config is not "
                    "provided."
                )
            configs[name] = default_soft7_ote_function_config(entity=entity_instance)
        else:
            raise TypeError(
                f"The {name!r} configuration provided is not a valid OTEAPI "
                f"{name.capitalize()}Config. Got type {type(config)}"
            )

    # Ensure all required configs are present
    if "dataresource" not in configs:
        raise S7EntityError(
            "The configs provided must contain a Resource configuration"
        )

    # Set default values if necessary
    if "function" not in configs:
        if entity_instance is None:
            raise EntityNotFound(
                "The entity must be provided if the function config is not provided."
            )
        configs["function"] = default_soft7_ote_function_config(entity=entity_instance)

    if TYPE_CHECKING:  # pragma: no cover
        configs = cast(GetDataConfigDict, configs)

    return configs


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
        type[UnshapedPropertyType], S7IdentityUriType
    ] = map_soft_to_py_types.get(
        value.type, value.type  # type: ignore[arg-type]
    )

    if isinstance(property_type, AnyUrl):
        # If the property type is a s7_identity_uri, it means it should be a
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
        type[UnshapedPropertyType], S7IdentityUriType
    ] = map_soft_to_py_types.get(
        value.type, value.type  # type: ignore[arg-type]
    )

    if isinstance(value.type, AnyUrl):
        # If the property type is a s7_identity_uri, it means it should be another
        # SOFT7 entity instance.
        # We need to get the property type for the SOFT7 entity instance.
        property_type: type[SOFT7EntityInstance] = create_entity(value.type)  # type: ignore[no-redef]

    if value.shape:
        # For each dimension listed in shape, nest the property type in on itself.
        for _ in range(len(value.shape)):
            property_type: type[ListPropertyType] = list[property_type]  # type: ignore[valid-type,no-redef]

    return property_type  # type: ignore[return-value]
