"""Pydantic data models for SOFT7 entities/data models."""
from typing import (
    Any,
    Annotated,
    Optional,
    TYPE_CHECKING,
    Literal,
    Protocol,
    runtime_checkable,
)

from pydantic import AnyUrl, BaseModel, ConfigDict, Field, TypeAdapter, AliasChoices
from pydantic.functional_validators import model_validator, field_validator
from pydantic.functional_serializers import model_serializer
from pydantic.networks import UrlConstraints
from pydantic_core import Url

if TYPE_CHECKING:  # pragma: no cover
    from typing import Union

    from pydantic import SerializerFunctionWrapHandler

    UnshapedPropertyType = Union[
        str, float, int, complex, dict, bool, bytes, bytearray, "SOFT7DataSource"
    ]
    ShapedPropertyType = tuple[Union["ShapedPropertyType", UnshapedPropertyType], ...]

    PropertyType = Union[UnshapedPropertyType, ShapedPropertyType]


SOFT7IdentityURI = Annotated[
    Url, UrlConstraints(allowed_schemes=["http", "https", "file"], host_required=True)
]


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


SOFT7EntityPropertyType = Literal[
    "string",
    "str",
    "float",
    "int",
    "complex",
    "dict",
    "boolean",
    "bytes",
    "bytearray",
    "ref",
]


def parse_identity(identity: AnyUrl) -> tuple[AnyUrl, "Union[str, None]", str]:
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
        try:
            attr_value: "Union[Any, GetData]" = object.__getattribute__(self, name)

            # SOFT7 metadata
            if name.startswith("soft7___"):
                return attr_value

            # SOFT7 property
            if name in object.__getattribute__(self, "model_fields"):
                resolved_attr_value = attr_value(soft7_property=name)

                # Use TypeAdapter to return and validate the value against the
                # generated type. This effectively validates the shape and
                # dimensionality of the value, as well as the inner most expected type.
                return TypeAdapter(
                    object.__getattribute__(self, "model_fields")[
                        name
                    ].rebuild_annotation()
                ).validate_python(resolved_attr_value)

            return attr_value
        except Exception as exc:
            raise AttributeError from exc

    @model_serializer(mode="wrap", when_used="always")
    def _serialize_callable_attributes(  # type: ignore[misc]
        self: "BaseModel", handler: "SerializerFunctionWrapHandler"
    ) -> "Any":
        """Serialize all "lazy" SOFT7 property values.

        If the value matches the GetData protocol, i.e., it's a callable function with
        the `name` parameter, call it with the property's name and the result will be
        used in a copy of the model. Otherwise, the value will be used as-is.

        The copy of the model is returned through the SerializerFunctionWrapHandler.
        """
        resolved_fields: "dict[str, PropertyType]" = {}

        # This iteration works, due to how BaseModel yields fields (from __dict__ +
        # __pydantic__extras__).
        for field_name, field_value in self:
            if isinstance(field_value, GetData):
                # Call the function via self.__getattribute__ to ensure proper type
                # validation and store the returned value for later use.
                resolved_fields[field_name] = getattr(self, field_name)

            # Else: The value is not a GetData, so use it as-is, i.e., no changes.

        return handler(self.model_copy(update=resolved_fields))


class SOFT7DataSource(BaseModel, CallableAttributesMixin):
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


map_soft_to_py_types: "dict[str, type[UnshapedPropertyType]]" = {
    "string": str,
    "str": str,
    "float": float,
    "int": int,
    "complex": complex,
    "dict": dict,
    "boolean": bool,
    "bytes": bytes,
    "bytearray": bytearray,
    "ref": SOFT7DataSource,
}


class SOFT7EntityProperty(BaseModel):
    """A SOFT7 Entity property."""

    type_: Annotated[
        SOFT7EntityPropertyType,
        Field(
            description="A valid property type.",
            alias="type",
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


class SOFT7Entity(BaseModel):
    """A SOFT7 Entity."""

    identity: Annotated[
        SOFT7IdentityURI,
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
    def shapes_and_dimensions(self) -> "SOFT7Entity":
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
