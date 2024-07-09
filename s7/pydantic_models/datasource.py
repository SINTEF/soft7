"""Everything to do with the special SOFT model Data Source."""

from __future__ import annotations

import logging
import traceback
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Protocol, cast, runtime_checkable

import httpx
import yaml
from pydantic import (
    AnyHttpUrl,
    AnyUrl,
    BaseModel,
    ConfigDict,
    TypeAdapter,
    ValidationError,
)
from pydantic.functional_serializers import model_serializer

from s7.exceptions import ConfigsNotFound, EntityNotFound, S7EntityError
from s7.pydantic_models.oteapi import (
    HashableFunctionConfig,
    HashableMappingConfig,
    HashableParserConfig,
    HashableResourceConfig,
    default_soft7_ote_function_config,
)

if TYPE_CHECKING:  # pragma: no cover
    import sys
    from typing import TypedDict, Union

    if sys.version_info >= (3, 10):
        from typing import Literal
    else:
        from typing_extensions import Literal

    from oteapi.models import GenericConfig
    from pydantic import SerializerFunctionWrapHandler
    from pydantic.fields import FieldInfo

    from s7.pydantic_models.soft7_entity import PropertyType, SOFT7IdentityURIType
    from s7.pydantic_models.soft7_instance import SOFT7EntityInstance

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
        parser: HashableParserConfig


LOGGER = logging.getLogger(__name__)


@runtime_checkable
class GetData(Protocol):
    """Get a named datum (property or dimension) from the data resource.

    Properties:
        soft7_property: The name of a datum to get, i.e., the SOFT7 data resource
            property (or dimension).

    Returns:
        The value of the SOFT7 data resource property (or dimension).

    """

    def __call__(self, soft7_property: str) -> Any:  # pragma: no cover
        ...


class CallableAttributesBaseModel(BaseModel):
    """Call, resolve, and cache attributes if they are SOFT7 properties."""

    _resolved_fields: dict[str, PropertyType] = {}

    def __getattribute__(self, name: str) -> Any:
        """Get an attribute.

        This function will _always_ be called whenever an attribute is accessed.

        Having this function allows us to intercept the attribute access and if the
        attribute is a SOFT7 property, we can retrieve the value from the underlying
        data source, i.e., call the `__get_data()` function that the attribute value
        currently is.

        Before calling the `__get_data()` function, we need to ensure the attribute
        is not a SOFT7 metadata attribute, i.e., starts with `soft7___`.

        """
        resolved_attr_value = "NOT SET"

        try:
            if (
                # If dunder method, return as-is.
                # or is a SOFT7 metadata field
                name.startswith(("__", "soft7___"))
                # Or otherwise a non-SOFT7 attribute
                or name
                not in (model_fields := object.__getattribute__(self, "model_fields"))
                # Or if private attributes are not set (not yet properly initialized)
                or not (
                    private_attrs := object.__getattribute__(
                        self, "__pydantic_private__"
                    )
                )
            ):
                return object.__getattribute__(self, name)

            # Check "cache"
            # Retrieve from "cache"
            if name in (resolved_fields := private_attrs.get("_resolved_fields", {})):
                LOGGER.debug("Using cached value for %s", name)
                # If the field has already been resolved, use the resolved value.
                return resolved_fields[name]

            # Retrieve from data source
            LOGGER.debug("Resolving value for %s", name)
            resolved_attr_value = object.__getattribute__(self, name)(
                soft7_property=name
            )

            # Use TypeAdapter to return and validate the value against the
            # generated type. This effectively validates the shape and
            # dimensionality of the value, as well as the inner most expected type.
            field_info: FieldInfo = model_fields[name]
            resolved_fields[name] = TypeAdapter(
                field_info.rebuild_annotation()
            ).validate_python(resolved_attr_value)

            BaseModel.__setattr__(self, "_resolved_fields", resolved_fields)

            return resolved_fields[name]

        except ValidationError as exc:
            LOGGER.error(
                "Attribute: %s. Data: %r\n%s: %s\nTraceback:\n%s",
                name,
                resolved_attr_value,
                exc.__class__.__name__,
                exc,
                "".join(traceback.format_tb(exc.__traceback__)),
            )
            raise AttributeError(
                f"Could not type and shape validate attribute {name!r} from the data "
                "source."
            ) from exc

        except Exception as exc:
            LOGGER.error(
                "An error occurred during attribute resolution:\n%s: %s\n"
                "Traceback:\n%s",
                exc.__class__.__name__,
                exc,
                "".join(traceback.format_tb(exc.__traceback__)),
            )
            raise AttributeError(f"Could not retrieve attribute {name!r}.") from exc

    @model_serializer(mode="wrap", when_used="always")
    def _serialize_callable_attributes(
        self, handler: SerializerFunctionWrapHandler
    ) -> Any:
        """Serialize all "lazy" SOFT7 property values.

        If the value matches the GetData protocol, i.e., it's a callable function with
        the `name` parameter, call it with the property's name and the result will be
        used in a copy of the model. Otherwise, the value will be used as-is.

        The copy of the model is returned through the SerializerFunctionWrapHandler.
        """
        if not isinstance(self, BaseModel):
            raise TypeError(
                "This mixin class may only be used with pydantic.BaseModel subclasses."
            )

        # This iteration works, due to how BaseModel yields fields (from __dict__ +
        # __pydantic__extras__).
        for field_name, field_value in self:
            if field_name in self._resolved_fields:
                # If the field has already been resolved, use the resolved value.
                continue

            if isinstance(field_value, GetData):
                # Call the function via self.__getattribute__ to ensure proper type
                # validation and store the returned value for later use.
                self._resolved_fields[field_name] = getattr(self, field_name)

            # Else: The value is not a GetData, so use it as-is, i.e., no changes.

        return handler(self.model_copy(update=self._resolved_fields))


class SOFT7DataSource(CallableAttributesBaseModel):
    """Generic SOFT7 data source

    This doc-string should be replaced with the specific data source's `description`.

    The configuration options:
    - `extra="forbid"`: Ensures an exception is raised if the instantiated data source
      tries to specify undefined properties.
    - `frozen=True`: Ensures an exception is raised if the instantiated data source
      tries to modify any properties, i.e., manually set an attribute value.
    - `validate_default=False`: Set explicitly (`False` is the default) to avoid a
      ValidationError when instantiating the data source. This is due to the properties
      being lazily retrieved from the data source.

    Note:
        The defined `soft7___*` fields will be overwritten by `pydantic.create_model()`,
        but they are defined here to help with understanding what the SOFT7 metadata
        attributes are.

        They act as a "contract" between the factory function and the SOFT7DataSource
        model, i.e., the factory function must return a dictionary that at least defines
        the metadata attributes, since otherwise a ValidationError will be raised upon
        instantiation.

    """

    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=False)

    soft7___dimensions: BaseModel
    soft7___identity: AnyUrl

    soft7___namespace: str
    soft7___version: Optional[str]
    soft7___name: str


class DataSourceDimensions(CallableAttributesBaseModel):
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


def parse_input_configs(
    configs: Union[
        GetDataConfigDict,
        dict[str, Union[GenericConfig, dict[str, Any], Path, AnyUrl, str]],
        Path,
        AnyUrl,
        str,
    ],
    entity_instance: Optional[
        Union[type[SOFT7EntityInstance], SOFT7IdentityURIType, str]
    ] = None,
) -> GetDataConfigDict:
    """Parse input to a function that expects a resource config."""
    name_to_config_type_mapping: dict[
        str,
        type[
            Union[
                HashableFunctionConfig,
                HashableMappingConfig,
                HashableParserConfig,
                HashableResourceConfig,
            ],
        ],
    ] = {
        "dataresource": HashableResourceConfig,
        "function": HashableFunctionConfig,
        "mapping": HashableMappingConfig,
        "parser": HashableParserConfig,
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
                try:
                    configs = yaml.safe_load(configs)
                except yaml.YAMLError as error:
                    raise ConfigsNotFound(
                        "Could not parse the configurations as a YAML/JSON formatted "
                        "string."
                    ) from error
        else:
            # If it is a URL, assume it's a URL to a JSON/YAML resource online.
            with httpx.Client(follow_redirects=True) as client:
                response = client.get(
                    str(configs),
                    headers={"Accept": "application/yaml, application/json"},
                )

            if not response.is_success:
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as error:
                    raise ConfigsNotFound(
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
            name = cast(Literal["dataresource", "function", "mapping", "parser"], name)

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
                    try:
                        config = yaml.safe_load(config)  # noqa: PLW2901
                    except yaml.YAMLError as error:
                        raise ConfigsNotFound(
                            f"Could not parse the {name} config as a YAML/JSON "
                            "formatted string."
                        ) from error
            else:
                # If it is a URL, assume it's a URL to a JSON/YAML resource online.
                with httpx.Client(follow_redirects=True) as client:
                    response = client.get(
                        str(config),
                        headers={"Accept": "application/yaml, application/json"},
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
    if any(required_key not in configs for required_key in ["dataresource", "parser"]):
        error_message = "The configs provided must contain a "

        if "dataresource" not in configs:
            error_message += "Data Resource configuration"

        if "parser" not in configs:
            error_message += (
                " and a Parser configuration"
                if "dataresource" not in configs
                else "Parser configuration"
            )

        raise S7EntityError(error_message)

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
