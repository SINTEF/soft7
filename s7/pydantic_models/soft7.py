"""Pydantic data models for SOFT7 entities/data models."""

from __future__ import annotations
from typing import Any, Dict, Annotated, Optional, TYPE_CHECKING, Literal, Union
from pydantic.functional_validators import model_validator, field_validator
from pydantic import AnyUrl, BaseModel, ConfigDict, Field
from datetime import datetime

if TYPE_CHECKING:  # pragma: no cover
    from s7.factories.datasource_factory import GetProperty


SOFT7EntityPropertyType = Literal[
    "string",
    "float",
    "int",
    "complex",
    "dict",
    "boolean",
    "bytes",
    "bytearray",
    "datetime",
]
map_soft_to_py_types: dict[str, type] = {
    "string": str,
    "float": float,
    "int": int,
    "complex": complex,
    "dict": dict,
    "boolean": bool,
    "bytes": bytes,
    "bytearray": bytearray,
    "datetime": datetime,
}


class SOFT7DataEntity(BaseModel):
    """Generic Data source entity"""

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

    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=False)


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

    @field_validator("type_", mode="before")
    @classmethod
    def validate_type(cls, v):
        if v not in map_soft_to_py_types:
            raise ValueError(
                f"Invalid type: {v}. Must be one of {list(map_soft_to_py_types.keys())}"
            )
        return v

    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=False)


class SOFT7Entity(BaseModel):
    """A SOFT7 Entity."""

    identity: Annotated[
        AnyUrl, Field(description="The semantic reference for the entity.")
    ]
    description: Annotated[str, Field(description="A description of the entity.")] = ""
    dimensions: Annotated[
        Optional[Dict[str, str]],
        Field(
            description=(
                "A dictionary or model of dimension names (key) and descriptions "
                "(value)."
            ),
        ),
    ] = None
    properties: Annotated[
        Dict[str, SOFT7EntityProperty], Field(description="A dictionary of properties.")
    ]

    @field_validator("properties", mode="after")
    @classmethod
    def validate_properties(
        cls, properties: Dict[str, SOFT7EntityProperty]
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

    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=False)


class SOFT7CollectionDimension(BaseModel):
    """A SOFT7 Entity Dimension specification"""

    description: Annotated[
        Optional[str], Field(description="A description of the dimension.")
    ] = None
    minValue: Annotated[
        Optional[int], Field(description="Minimum size of the dimension.")
    ] = None
    maxValue: Annotated[
        Optional[int], Field(description="Maximal size of the dimension.")
    ] = None
    dimensionMapping: Annotated[
        Optional[Dict[str, Any]],
        Field(description="Dimension mapping for aligning entities."),
    ] = None

    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=False)


class SOFT7CollectionProperty(BaseModel):
    """A SOFT7 Entity property."""

    type_: Annotated[
        Union[str, dict],
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
            description=("The unit of the property."),
        ),
    ] = None

    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=False)


class SOFT7Collection(SOFT7Entity):
    """A SOFT7 Collection."""

    dimensions: Annotated[
        Dict[str, SOFT7CollectionDimension],
        Field(description="A dictionary of dimensions."),
    ]

    properties: Annotated[
        Dict[str, SOFT7CollectionProperty],
        Field(description="A dictionary of properties."),
    ]

    schemas: Annotated[
        Dict[str, dict], Field(description="User defined types", alias="$schemas")
    ] = {}

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_default=False,
    )

    @model_validator(mode="before")
    @classmethod
    def validate_refs(cls, values):
        """Check if all defined references are valid"""
        schemas = values.get("$schemas", {})
        properties = values.get("properties", {})

        def check_ref(ref, path):
            if not ref.startswith("#/schemas/"):
                raise ValueError(f"Invalid $ref format at {path}: {ref}")
            parts = ref.split("/")
            if len(parts) != 4 or parts[1] != "schemas":
                raise ValueError(f"Invalid $ref format at {path}: {ref}")
            schema_type, schema_name = parts[2], parts[3]
            if schema_type not in schemas or schema_name not in schemas[schema_type]:
                raise ValueError(f"Unresolved $ref at {path}: {ref}")

        for prop_name, prop in properties.items():
            if isinstance(prop["type"], dict) and "$ref" in prop["type"]:
                check_ref(prop["type"]["$ref"], f"properties.{prop_name}.type.$ref")

        for schema_type, schema_dict in schemas.items():
            for schema_name, schema in schema_dict.items():
                for prop_name, prop in schema.get("properties", {}).items():
                    if isinstance(prop["type"], dict) and "$ref" in prop["type"]:
                        check_ref(
                            prop["type"]["$ref"],
                            f"$schemas.{schema_type}.{schema_name}.properties.{prop_name}.type.$ref",
                        )
        return values

    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=False)
