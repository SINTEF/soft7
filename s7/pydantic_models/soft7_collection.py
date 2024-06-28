"""Pydantic data models for SOFT7 collections."""

from __future__ import annotations

from typing import (
    Annotated,
    Any,
    Optional,
    Union,
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)
from pydantic.functional_validators import (
    model_validator,
)
from .soft7_entity import SOFT7Entity, SOFT7EntityProperty


class SOFT7CollectionDimension(BaseModel):
    """A SOFT7 Entity Dimension specification"""

    description: Annotated[
        Optional[str], Field(description="A description of the dimension.")
    ] = None
    min_value: Annotated[
        Optional[int], Field(description="Minimum size of the dimension.")
    ] = None
    max_value: Annotated[
        Optional[int], Field(description="Maximal size of the dimension.")
    ] = None
    dimension_mapping: Annotated[
        Optional[dict[str, Any]],
        Field(description="Dimension mapping for aligning entities."),
    ] = None

    model_config = ConfigDict(extra="forbid", frozen=True)


class SOFT7CollectionProperty(SOFT7EntityProperty):
    """A SOFT7 Entity property."""

    type_: Annotated[
        Union[str, dict],
        Field(
            description="A valid property type.",
            alias="type",
        ),
    ]
    model_config = ConfigDict(extra="forbid", frozen=True)


class SOFT7Collection(SOFT7Entity):
    """A SOFT7 Collection."""

    dimensions: Annotated[  # type: ignore[assignment]
        dict[str, SOFT7CollectionDimension],
        Field(description="A dictionary of dimensions."),
    ]

    properties: Annotated[  # type: ignore[assignment]
        dict[str, SOFT7CollectionProperty],
        Field(description="A dictionary of properties."),
    ]

    schemas: Annotated[
        dict[str, dict], Field(description="User defined types", alias="$schemas")
    ] = {}

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
        frozen=True,
    )

    @model_validator(mode="after")
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
