"""Pydantic data models for SOFT7 entities/data models."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Optional,
    Union,
    get_args,
)

if sys.version_info >= (3, 10):
    from typing import Literal
else:
    from typing_extensions import Literal

from pydantic import (
    AliasChoices,
    AnyHttpUrl,
    BaseModel,
    Field,
    FileUrl,
    TypeAdapter,
    ValidationError,
)
from pydantic.functional_validators import (
    field_validator,
    model_validator,
)

from s7.exceptions import EntityNotFound
from s7.pydantic_models._utils import (
    get_dict_from_any_model_input,
    get_dict_from_url_path_or_raw,
)

if TYPE_CHECKING:  # pragma: no cover
    UnshapedPropertyType = Union[
        str, float, int, complex, dict, bool, bytes, bytearray, BaseModel
    ]
    ShapedPropertyType = tuple[Union["ShapedPropertyType", UnshapedPropertyType], ...]
    ShapedListPropertyType = list[Union["ShapedListPropertyType", UnshapedPropertyType]]

    PropertyType = Union[UnshapedPropertyType, ShapedPropertyType]
    ListPropertyType = Union[UnshapedPropertyType, ShapedListPropertyType]


SOFT7IdentityURIType = Union[AnyHttpUrl, FileUrl]


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
        return TypeAdapter(SOFT7IdentityURIType).validate_python(url)

    raise TypeError(f"Expected str, AnyHttpUrl, or FileUrl, got {type(url)}")


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


def parse_identity(
    identity: SOFT7IdentityURIType,
) -> tuple[SOFT7IdentityURIType, Optional[str], str]:
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

    return SOFT7IdentityURI(namespace), version or None, name


class SOFT7EntityProperty(BaseModel):
    """A SOFT7 Entity property."""

    type: Annotated[
        SOFT7EntityPropertyType,
        Field(description="The type of the described property, e.g., an integer."),
    ]

    description: Annotated[
        str, Field(description="A human-readable description of the property.")
    ]

    shape: Annotated[
        Optional[list[str]],
        Field(
            description=(
                "The dimension of multi-dimensional properties. This is a list of "
                "dimension expressions referring to the dimensions defined above. For "
                "instance, if an entity have dimensions with names `H`, `K`, and `L` "
                "and a property with shape `['K', 'H+1']`, the property of an instance "
                "of this entity with dimension values `H=2`, `K=2`, `L=6` will have "
                "shape `[2, 3]`."
            ),
            validation_alias=AliasChoices("dims", "shape"),
        ),
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
        try:
            data = get_dict_from_any_model_input(data)
        except ValueError:
            # If we cannot handle the data, we give up and let pydantic handle it.
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
            # Bad data. We can try to see if `ref` is present and assume it is equal
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
            # We will assume this is a mistake for the `type` field and use the `$ref`
            # value if it's valid.
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

            if isinstance(ref, get_args(SOFT7IdentityURIType)):
                new_type = ref
            elif isinstance(ref, str):
                try:
                    new_type = SOFT7IdentityURI(ref)
                except ValidationError as exc:
                    raise ValueError(
                        f"Invalid `type` field value {type_!r} and `$ref` value {ref!r}"
                    ) from exc
            else:
                try:
                    str(ref)
                except (TypeError, ValueError):
                    # If we cannot convert the ref to a string, we give up and let
                    # pydantic handle it.
                    return data

                raise ValueError(
                    f"Invalid `type` field value {type_!r} and `$ref` value "
                    f"{str(ref)!r}"
                )

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

    description: Annotated[
        str, Field(description="Human-readable description of the entity.")
    ] = ""

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
    def _validate_properties(
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
    def _shapes_and_dimensions(self) -> SOFT7Entity:
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

    @model_validator(mode="before")
    @classmethod
    def _handle_namespace_version_name(cls, data: Any) -> Any:
        """Handle the case of identity being a uri defined from namespace, version and
        name inputs.

        This will remove 'namespace', 'version' and 'name' from the data and replace
        them with 'identity' - even if 'identity' (or 'uri') is already present.
        If the 'identity'/'uri' is present, it must match the 'namespace', 'version' and
        'name' values - as well as each other (if both are present).

        Parameters:
            data: The raw input which is often a `dict[str, Any]` but could also be an
                instance of the model itself (e.g. if
                `UserModel.model_validate(UserModel.construct(...))` is called) or
                anything else since you can pass arbitrary objects into
                `model_validate`.

        """
        try:
            data = get_dict_from_any_model_input(data)
        except ValueError:
            # If we cannot handle the data, we give up and let pydantic handle it.
            return data

        # If either of 'namespace', 'version' or 'name' is included:
        # - Ensure they are all included
        # - Ensure if 'identity'/'uri' is included, it matches
        #   <namespace>/<version>/<name>
        # Finally, replace 'namespace', 'version' and 'name' with 'identity'.
        namespace = data.pop("namespace", None)
        version = data.pop("version", None)
        name = data.pop("name", None)

        if any((namespace, version, name)) and not all((namespace, version, name)):
            raise ValueError(
                "If 'namespace', 'version' or 'name' is included (at least one is), "
                "all must be (they are not)."
            )

        identity = data.pop("identity", None)
        uri = data.pop("uri", None)

        if identity and uri and identity != uri:
            raise ValueError(
                "Both 'identity' and 'uri' are included; they must match (they do "
                "not)."
            )

        # Ensure all are strings (or bytes/bytearray that can be decoded to strings).
        if name:
            if not all(
                isinstance(_, (str, bytes, bytearray))
                for _ in (namespace, version, name)
            ):
                raise ValueError("'namespace', 'version' and 'name' must be strings.")

            if isinstance(namespace, (bytes, bytearray)):
                try:
                    namespace = namespace.decode()
                except ValueError:
                    # If we cannot decode the bytes, we give up and let pydantic handle
                    # it.
                    return data

            if isinstance(version, (bytes, bytearray)):
                try:
                    version = version.decode()
                except ValueError:
                    # If we cannot decode the bytes, we give up and let pydantic handle
                    # it.
                    return data

            if isinstance(name, (bytes, bytearray)):
                try:
                    name = name.decode()
                except ValueError:
                    # If we cannot decode the bytes, we give up and let pydantic handle
                    # it.
                    return data

        if identity or uri:
            data["identity"] = identity or uri

            # Ensure 'identity'/'uri' is a string (or bytes/bytearray that can be
            # decoded).
            if isinstance(data["identity"], (bytes, bytearray)):
                try:
                    data["identity"] = data["identity"].decode()
                except ValueError:
                    # If we cannot decode the bytes, we give up and let pydantic handle
                    # it.
                    return data

            if name and data["identity"] != f"{namespace}/{version}/{name}":
                raise ValueError(
                    f"'identity'/'uri' must match '{namespace}/{version}/{name}' (it "
                    "does not)."
                )

        elif name:
            data["identity"] = f"{namespace}/{version}/{name}"

        # else: identity/uri is not present, and namespace, version and name are not
        # present, so we do nothing - let pydantic handle it (raising ValidationErrors).
        return data

    @model_validator(mode="before")
    @classmethod
    def _handle_soft5_inputs(cls, data: Any) -> Any:
        """Handle the case of data using SOFT5 syntax.

        This is centered around the type of the 'dimensions' and 'properties' fields,
        which are expected to be lists of dictionaries in SOFT5.
        This validator function will convert them to the SOFT7 format.

        Parameters:
            data: The raw input which is often a `dict[str, Any]` but could also be an
                instance of the model itself (e.g. if
                `UserModel.model_validate(UserModel.construct(...))` is called) or
                anything else since you can pass arbitrary objects into
                `model_validate`.

        """
        try:
            data = get_dict_from_any_model_input(data)
        except ValueError:
            # If we cannot handle the data, we give up and let pydantic handle it.
            return data

        # Check if the data is a (valid) SOFT5 entity.
        if ("dimensions" in data and "properties" in data) and type(
            data["dimensions"]
        ) is not type(data["properties"]):
            # Both 'dimensions' and 'properties' are present, but they are not the same
            # type, i.e., they are neither valid SOFT7 nor SOFT5 entities.
            # We will let pydantic handle it.
            return data

        # If the data is a SOFT5 entity, we convert it to a SOFT7 entity.
        if "dimensions" in data and isinstance(data["dimensions"], list):
            dimensions = data.pop("dimensions")

            if not all(isinstance(dimension, dict) for dimension in dimensions):
                raise ValueError("All dimensions must be dictionaries.")

            if not all(
                "name" in dimension and "description" in dimension
                for dimension in dimensions
            ):
                raise ValueError(
                    "All dimensions must have 'name' and 'description' keys."
                )

            data["dimensions"] = {
                dimension["name"]: dimension["description"] for dimension in dimensions
            }

        if "properties" in data and isinstance(data["properties"], list):
            properties = data.pop("properties")

            if not all(isinstance(property_, dict) for property_ in properties):
                raise ValueError("All properties must be dictionaries.")

            if (not all("name" in property_ for property_ in properties)) and (
                not all(
                    isinstance(property_["name"], (str, bytes, bytearray))
                    for property_ in properties
                )
            ):
                raise ValueError(
                    "All properties must have a 'name' key with a string value."
                )

            # Let pydantic handle any type/model casting.
            data["properties"] = {
                property_.pop("name"): property_ for property_ in properties
            }

        return data

    @model_validator(mode="before")
    @classmethod
    def _handle_meta_from_dlite(cls, data: Any) -> Any:
        """Handle the case of data using DLite syntax.

        For now, 'meta' is the only DLite-specific field that we are not already
        handling ('identity' is 'uri' in DLite, which is handled through aliasing).
        This validator function will validate 'meta' has the expected value and then
        discard it.

        Parameters:
            data: The raw input which is often a `dict[str, Any]` but could also be an
                instance of the model itself (e.g. if
                `UserModel.model_validate(UserModel.construct(...))` is called) or
                anything else since you can pass arbitrary objects into
                `model_validate`.

        """
        try:
            data = get_dict_from_any_model_input(data)
        except ValueError:
            # If we cannot handle the data, we give up and let pydantic handle it.
            return data

        if "meta" in data:
            meta = data.pop("meta")

            if isinstance(meta, (bytes, bytearray)):
                try:
                    meta = meta.decode()
                except ValueError:
                    # If we cannot decode the bytes, we give up and let pydantic handle
                    # it.
                    return data

            if not isinstance(meta, str):
                raise ValueError("'meta' is provided. Expected 'meta' to be a string.")

            if meta != "http://onto-ns.com/meta/0.3/EntitySchema":
                raise ValueError(
                    "'meta' is provided. Expected 'meta' to be "
                    f"'http://onto-ns.com/meta/0.3/EntitySchema', got {meta!r}."
                )

        return data


def parse_input_entity(
    entity: Union[
        SOFT7Entity, dict[str, Any], Path, SOFT7IdentityURIType, str, bytes, bytearray
    ],
) -> SOFT7Entity:
    """Parse input to a function that expects a SOFT7 entity."""
    if isinstance(entity, SOFT7Entity):
        return entity

    if isinstance(entity, dict):
        # Create and return the entity model
        return SOFT7Entity(**entity)

    # Get the entity as a dictionary
    entity = get_dict_from_url_path_or_raw(
        entity,
        exception_cls=EntityNotFound,
        parameter_name="entity",
        concept_name="SOFT7 entity",
    )

    # Create and return the entity model
    return SOFT7Entity(**entity)
