"""Pydantic data models for SOFT7 entities/data models."""

from __future__ import annotations

import json
import logging
import sys
import traceback
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Optional,
    Protocol,
    Union,
    runtime_checkable,
)

if sys.version_info >= (3, 10):
    from typing import Literal
else:
    from typing_extensions import Literal

from pydantic import (
    AliasChoices,
    AnyUrl,
    BaseModel,
    Field,
    TypeAdapter,
    ValidationError,
)
from pydantic.functional_serializers import model_serializer
from pydantic.functional_validators import (
    field_validator,
    model_validator,
)
from pydantic.networks import UrlConstraints
from pydantic_core import Url

if TYPE_CHECKING:  # pragma: no cover
    from pydantic import SerializerFunctionWrapHandler
    from pydantic.fields import FieldInfo

    UnshapedPropertyType = Union[
        str, float, int, complex, dict, bool, bytes, bytearray, BaseModel
    ]
    ShapedPropertyType = tuple[Union["ShapedPropertyType", UnshapedPropertyType], ...]
    ShapedListPropertyType = list[Union["ShapedListPropertyType", UnshapedPropertyType]]

    PropertyType = Union[UnshapedPropertyType, ShapedPropertyType]
    ListPropertyType = Union[UnshapedPropertyType, ShapedListPropertyType]


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


class CallableAttributesMixin:
    """Mixin to call and resolve attributes if they are SOFT7 properties."""

    _resolved_fields: dict[str, PropertyType] = {}  # noqa: RUF012

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
            attr_value: Union[Any, GetData] = object.__getattribute__(self, name)

            # SOFT7 metadata
            if name.startswith("soft7___"):
                return attr_value

            ## SOFT7 property
            # Retrieve from "cache"
            if name in object.__getattribute__(self, "_resolved_fields"):
                # If the field has already been resolved, use the resolved value.
                return object.__getattribute__(self, "_resolved_fields")[name]

            # Retrieve from data source
            if name in object.__getattribute__(self, "model_fields"):
                resolved_attr_value = attr_value(soft7_property=name)

                # Use TypeAdapter to return and validate the value against the
                # generated type. This effectively validates the shape and
                # dimensionality of the value, as well as the inner most expected type.
                field_info: FieldInfo = object.__getattribute__(self, "model_fields")[
                    name
                ]
                self._resolved_fields[name] = TypeAdapter(
                    field_info.rebuild_annotation()
                ).validate_python(resolved_attr_value)

                return self._resolved_fields[name]

            # Non-SOFT7 attribute
            return attr_value

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

        except Exception as exc:  # noqa: BLE001
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
