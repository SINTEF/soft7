"""Pydantic data models for SOFT7 entities/data models."""
from typing import Any, Annotated, Optional, TYPE_CHECKING, Literal

from pydantic import AnyUrl, BaseModel, ConfigDict, Field
from pydantic.functional_validators import model_validator, field_validator

if TYPE_CHECKING:  # pragma: no cover
    from typing import Union, Protocol

    UnshapedPropertyType = Union[str, float, int, complex, dict, bool, bytes, bytearray]

    class GetProperty(Protocol):
        """Protocol for getting a property."""

        def __call__(self, name: str) -> Any:
            ...


SOFT7EntityPropertyType = Literal[
    "string", "float", "int", "complex", "dict", "boolean", "bytes", "bytearray"
]
map_soft_to_py_types: "dict[str, type[UnshapedPropertyType]]" = {
    "string": str,
    "float": float,
    "int": int,
    "complex": complex,
    "dict": dict,
    "boolean": bool,
    "bytes": bytes,
    "bytearray": bytearray,
}


class SOFT7DataEntity(BaseModel):
    """Generic Data source entity"""

    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)

    def __getattribute__(self, name: str) -> Any:
        """Get an attribute.

        This function will _always_ be called whenever an attribute is accessed.
        """
        try:
            attr_value: "Union[Any, GetProperty]" = object.__getattribute__(self, name)

            if name in object.__getattribute__(self, "model_fields"):
                return attr_value(name)

            return attr_value
        except Exception as exc:
            raise AttributeError from exc


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
        AnyUrl, Field(description="The semantic reference for the entity.")
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
