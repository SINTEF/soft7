"""Pydantic data models for SOFT7 entities/data models."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Optional,
    Union,
)

if sys.version_info >= (3, 10):
    from typing import Literal
else:
    from typing_extensions import Literal

import httpx
from pydantic import (
    AliasChoices,
    AnyUrl,
    BaseModel,
    Field,
    ValidationError,
)
from pydantic.functional_validators import (
    field_validator,
    model_validator,
)
from pydantic.networks import UrlConstraints
from pydantic_core import Url

from s7.exceptions import EntityNotFound
from s7.pydantic_models._utils import is_valid_url, try_load_from_json_yaml

if TYPE_CHECKING:  # pragma: no cover
    from typing import TypedDict

    UnshapedPropertyType = Union[
        str, float, int, complex, dict, bool, bytes, bytearray, BaseModel
    ]
    ShapedPropertyType = tuple[Union["ShapedPropertyType", UnshapedPropertyType], ...]
    ShapedListPropertyType = list[Union["ShapedListPropertyType", UnshapedPropertyType]]

    PropertyType = Union[UnshapedPropertyType, ShapedPropertyType]
    ListPropertyType = Union[UnshapedPropertyType, ShapedListPropertyType]

    class LoadFromJsonYamlErrorDict(TypedDict):
        exception_cls: type[EntityNotFound]
        exception_msg: str


SOFT7IdentityURIType = Annotated[
    Url, UrlConstraints(allowed_schemes=["http", "https", "file"], host_required=True)
]


LOGGER = logging.getLogger(__name__)


def SOFT7IdentityURI(url: str) -> SOFT7IdentityURIType:
    """SOFT7 Identity URI.

    This is a URL with the following constraints:
    - The scheme must be either `http`, `https` or `file`.
    - The host must be present.

    Parameters:
        url: The URL to validate.

    Returns:
        The validated URL.

    Raises:
        ValidationError: If the URL does not meet the constraints.

    """
    if isinstance(url, str):
        url = url.split("#", maxsplit=1)[0].split("?", maxsplit=1)[0]
        return SOFT7IdentityURIType(url)

    raise TypeError(f"Expected str or Url, got {type(url)}")


SOFT7EntityPropertyType = Union[
    SOFT7IdentityURIType,
    Literal[
        "string",
        "str",
        "float",
        "int",
        "complex",
        "dict",
        "boolean",
        "bytes",
        "bytearray",
    ],
]
map_soft_to_py_types: dict[str, type[UnshapedPropertyType]] = {
    "string": str,
    "str": str,
    "float": float,
    "int": int,
    "complex": complex,
    "dict": dict,
    "boolean": bool,
    "bytes": bytes,
    "bytearray": bytearray,
}
"""Use this with a fallback default of returning the lookup value."""


def parse_identity(identity: AnyUrl) -> tuple[AnyUrl, Optional[str], str]:
    """Parse the identity into a tuple of (namespace, version, name).

    The identity is a URI of the form: `<namespace>/<version>/<name>`.
    Where `namespace` is a URL, `version` is a string and `name` is a string.
    Both `version` and `name` are part of the URI path.

    For example: `https://soft7.org/0.1.0/temperature`. The `namespace` is
    `https://soft7.org`, the `version` is `0.1.0` and the `name` is `temperature`.

    Note:
        Query parameters and fragments are not part of the identity and will be removed
        silently.

    Parameters:
        identity: The SOFT7 entity identity to parse.

    Returns:
        A tuple of (namespace, version, name).

    """
    if not identity.path:
        raise ValueError("identity as a URL must have a path part.")

    if not identity.host:
        raise ValueError("identity as a URL must have a host part.")

    # Parse the last two parts of the path as version and name.
    # Ensure trailing slash is removed before splitting.
    # For example: `https://soft7.org/0.1.0/temperature/` -> `0.1.0` and `temperature`.
    version, name = identity.path.rstrip("/").split("/")[-2:]

    if not name:
        raise ValueError("identity must have a name part.")

    # Create namespace from URL parts.
    namespace = f"{identity.scheme}://"

    if identity.username:
        namespace += f"{identity.username}"

    if identity.password:
        namespace += f":{identity.password}"

    if identity.username or identity.password:
        namespace += "@"

    namespace += identity.host

    if identity.port:
        # Do not include default ports for http(s) schemes.
        if (identity.scheme, identity.port) in (("http", 80), ("https", 443)):
            pass
        else:
            namespace += f":{identity.port}"

    # Remove version and name from path, including the 2 associated preceding slashes.
    namespace += identity.path.rstrip("/")[: -len(version) - len(name) - 2]

    return AnyUrl(namespace), version or None, name


class SOFT7EntityProperty(BaseModel):
    """A SOFT7 Entity property."""

    type: Annotated[
        SOFT7EntityPropertyType,
        Field(
            description="A valid property type.",
        ),
    ]

    shape: Annotated[
        Optional[list[str]],
        Field(description="List of dimensions making up the shape of the property."),
    ] = None

    description: Annotated[
        Optional[str], Field(description="A human description of the property.")
    ] = None

    unit: Annotated[
        Optional[str],
        Field(
            description=(
                "The unit of the property. Would typically refer to other ontologies, "
                "like EMMO, QUDT or OM, or simply be a conventional symbol for the "
                "unit (e.g. 'km/h'). In future releases unit may be changed to a class."
            ),
        ),
    ] = None

    @model_validator(mode="before")
    @classmethod
    def _handle_ref_type_from_dlite(cls, data: Any) -> Any:
        """Handle the `type` field being a reference type.

        This is a quirk of DLite, which adds a special `$ref` field if `type` is "ref".
        The value of `$ref` is then an Entity URI, which is what we want to use as the
        type.

        Parameters:
            data: The raw input which is often a `dict[str, Any]` but could also be an
                instance of the model itself (e.g. if
                `UserModel.model_validate(UserModel.construct(...))` is called) or
                anything else since you can pass arbitrary objects into
                `model_validate`.

        """
        if isinstance(data, (bytes, bytearray)):
            try:
                data = data.decode()
            except ValueError:
                # If we cannot decode the bytes, we give up and let pydantic handle it.
                return data

        if isinstance(data, str):
            # Expect the string to be a JSON string, since this is pydantic, supporting
            # either Python or JSON validation/serialization.
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                # If we cannot decode the string, we give up and let pydantic handle it.
                return data

        if isinstance(data, cls):
            # If we get an instance of the model itself, we dump it as minimalistically
            # as possible.
            data = data.model_dump(exclude_defaults=True, exclude_unset=True)

        # At this point, we expect the data to be a dict.
        # If it is not, we give up and let pydantic handle it.
        if not isinstance(data, dict):
            return data

        # If the `type` field is not "ref" or `$ref` is not present, we return the data
        # as is to let pydantic do its thing.
        # Note, while `$ref` should technically only ever be present if `type` is "ref",
        # we will not assume this is the case and will deal with both cases.
        type_ = data.get("type", None)

        if isinstance(type_, (bytes, bytearray)):
            try:
                type_ = type_.decode()
            except ValueError:
                # If we cannot decode the bytes, we give up and let pydantic handle it.
                return data

        if not isinstance(type_, str):
            # If `type` is not a string, we give up and let pydantic handle it.
            return data

        if type_ != "ref" and "$ref" not in data:
            # Seemingly standard data - let pydantic handle it.
            return data

        if type_ == "ref" and "$ref" not in data:
            # Bad data. We can try to see if `ref` is present and assume that is equal
            # to `$ref`. If it is, we will use it as the type.
            # Otherwise, we will assume this is a mistake for the `type` field and let
            # pydantic handle it.
            if "ref" in data:
                # Update data and handle it in the next if-block.
                data["$ref"] = data.pop("ref")
            else:
                return data

        if (type_ != "ref" and "$ref" in data) or (type_ == "ref" and "$ref" in data):
            # If `type` is not "ref" but `$ref` is present, this is not standard DLite
            # data, but it is not a reference type either.
            # We will assume this is a mistake for the `type` field use the `$ref` value
            # if it's valid.
            # Otherwise, if `type` is "ref" and `$ref` is present, this is standard
            # DLite data, and we will use the `$ref` value as the type.
            ref = data.pop("$ref")

            if isinstance(ref, (bytes, bytearray)):
                try:
                    ref = ref.decode()
                except ValueError:
                    # If we cannot decode the bytes, we give up and let pydantic handle
                    # it.
                    return data

            if isinstance(ref, AnyUrl):
                new_type = ref
            elif isinstance(ref, str):
                try:
                    new_type = SOFT7IdentityURI(ref)
                except ValidationError as exc:
                    raise ValueError(
                        f"Invalid `type` field value '{type_}' and `$ref` value '{ref}'"
                    ) from exc
            else:
                raise ValueError(
                    f"Invalid `type` field value '{type_}' and `$ref` value '{ref}'"
                )

            if "type" in data:
                data["type"] = new_type

        # If we get here, we have either succeeded or failed.
        # If we failed, we have no idea what is going on, so we let pydantic handle it.
        # In any case, the result is the same:
        return data


class SOFT7Entity(BaseModel):
    """A SOFT7 Entity."""

    identity: Annotated[
        SOFT7IdentityURIType,
        Field(
            description="The semantic reference for the entity.",
            validation_alias=AliasChoices("identity", "uri"),
        ),
    ]

    description: Annotated[str, Field(description="A description of the entity.")] = ""

    dimensions: Annotated[
        Optional[dict[str, str]],
        Field(
            description=(
                "A dictionary or model of dimension names (key) and descriptions "
                "(value)."
            ),
        ),
    ] = None

    properties: Annotated[
        dict[str, SOFT7EntityProperty], Field(description="A dictionary of properties.")
    ]

    @field_validator("properties", mode="after")
    @classmethod
    def validate_properties(
        cls, properties: dict[str, SOFT7EntityProperty]
    ) -> dict[str, SOFT7EntityProperty]:
        """Validate properties

        1. `properties` cannot be an empty dict.
        2. Ensure there are no "private" properties, i.e., property names starting with
           an underscore (`_`).

        """
        if not properties:
            raise ValueError("properties must not be empty.")

        if any(property_name.startswith("_") for property_name in properties):
            raise ValueError(
                "property names may not be 'private', i.e., start with an underscore "
                "(_)"
            )

        return properties

    @model_validator(mode="after")
    def shapes_and_dimensions(self) -> SOFT7Entity:
        """Ensure the shape values are dimensions keys."""
        errors: list[tuple[str, str]] = []

        if self.dimensions:
            for property_name, property_value in self.properties.items():
                if property_value.shape and not all(
                    dimension in self.dimensions for dimension in property_value.shape
                ):
                    wrong_dimensions = [
                        dimension
                        for dimension in property_value.shape
                        if dimension not in self.dimensions
                    ]
                    errors.append(
                        (
                            property_name,
                            "Contains shape dimensions that are not defined in "
                            f"'dimensions': {wrong_dimensions}",
                        )
                    )
        else:
            for property_name, property_value in self.properties.items():
                if property_value.shape:
                    errors.append(
                        (
                            property_name,
                            "Cannot have shape; no dimensions are defined.",
                        )
                    )

        if errors:
            raise ValueError(
                "Property shape(s) and dimensions do not match.\n"
                + "\n".join(f"  {name}\n    {msg}" for name, msg in errors)
            )

        return self


def parse_input_entity(
    entity: Union[SOFT7Entity, dict[str, Any], Path, AnyUrl, str],
) -> SOFT7Entity:
    """Parse input to a function that expects a SOFT7 entity."""

    load_from_json_yaml_error: LoadFromJsonYamlErrorDict = {
        "exception_cls": EntityNotFound,
        "exception_msg": (
            "Could not parse the entity string as a SOFT7 entity (YAML/JSON format)."
        ),
    }

    # Handle the case of the entity being a string or a URL
    if isinstance(entity, (AnyUrl, str)):
        # If it's a string or URL, we expect to either be:
        # - A path to a YAML file.
        # - A SOFT7 entity identity.
        # - A parseable JSON/YAML string.

        # Check if it is a URL
        if is_valid_url(str(entity)):
            # If it is a URL, assume it's a SOFT7 entity identity.
            # Or at least that the response is a SOFT7 entity as JSON/YAML.
            with httpx.Client(follow_redirects=True) as client:
                try:
                    response = client.get(
                        str(entity),
                        headers={"Accept": "application/yaml, application/json"},
                    ).raise_for_status()
                except (httpx.HTTPStatusError, httpx.HTTPError) as error:
                    raise EntityNotFound(
                        f"Could not retrieve SOFT7 entity online from {entity}"
                    ) from error

            # Using YAML parser, since _if_ the content is JSON, it's still valid
            # YAML. JSON is a subset of YAML.
            entity = try_load_from_json_yaml(response.text, **load_from_json_yaml_error)
        else:
            if not isinstance(entity, str):  # pragma: no cover
                raise TypeError("Expected entity to be a str at this point")

            # If it's not a URL, check whether it is a path to an (existing) file.
            entity_path = Path(entity).resolve()

            if entity_path.exists():
                # If it's a path to an existing file, assume it's a JSON/YAML file.
                entity = try_load_from_json_yaml(
                    entity_path.read_text(encoding="utf8"), **load_from_json_yaml_error
                )
            else:
                # If it's not a path to an existing file, assume it's a parseable
                # JSON/YAML
                entity = try_load_from_json_yaml(entity, **load_from_json_yaml_error)

                if not isinstance(entity, dict):
                    # The entity is not a dictionary, so it's not a valid entity
                    # Assume it was a "string as a Path", but to a non-existing file.
                    raise EntityNotFound(
                        f"Could not find an entity JSON/YAML file at {entity_path}"
                    )

    # Handle the case of the entity being a path to a YAML file
    if isinstance(entity, Path):
        entity_path = entity.resolve()

        if not entity_path.exists():
            raise EntityNotFound(
                f"Could not find an entity JSON/YAML file at {entity_path}"
            )

        entity = try_load_from_json_yaml(
            entity_path.read_text(encoding="utf8"), **load_from_json_yaml_error
        )

    # Now the entity is either a SOFT7Entity instance or a dictionary, ready to be
    # used to create the SOFT7Entity instance.
    if isinstance(entity, dict):
        entity = SOFT7Entity(**entity)

    if not isinstance(entity, SOFT7Entity):
        raise TypeError(
            f"entity must be a 'SOFT7Entity', instead it was a {type(entity)}"
        )

    return entity
