"""The SOFT7 OTEAPI Function strategy.

It expects mappings to be present in the session, and will use them to transform
the parsed data source into a SOFT7 Entity instance.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated, Any, NamedTuple

from oteapi.models import SessionUpdate
from oteapi.strategies.mapping.mapping import MappingSessionUpdate
from pydantic import AnyUrl, BaseModel, Field, ValidationError
from pydantic.dataclasses import dataclass

# from pydantic.dataclasses import dataclass
from s7.exceptions import InvalidOrMissingSession
from s7.factories import create_entity
from s7.oteapi_plugin.models import SOFT7FunctionConfig

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Sequence
    from typing import TypedDict

    from pydantic.fields import FieldInfo

    from s7.pydantic_models.soft7_instance import SOFT7EntityInstance

    class RDFTriplePart(TypedDict):
        """A part of a RDF triple, i.e., either a subject, predicate or object."""

        namespace: AnyUrl
        concept: str


class RDFTriple(NamedTuple):
    """A RDF triple."""

    subject: RDFTriplePart
    predicate: RDFTriplePart
    object: RDFTriplePart


LOGGER = logging.getLogger(__name__)


@dataclass
class SOFT7Generator:
    """SOFT7 Generator function strategy for OTEAPI."""

    function_config: Annotated[
        SOFT7FunctionConfig, Field(description=SOFT7FunctionConfig.__doc__)
    ]

    def initialize(self, _: dict[str, Any] | None) -> SessionUpdate:
        """Initialize the SOFT7 Generator function strategy."""
        return SessionUpdate()

    def get(self, session: dict[str, Any] | None) -> SessionUpdate:
        """Execute the SOFT7 Generator function strategy."""
        if session is None:
            raise InvalidOrMissingSession("Session is missing.")

        # Expect the mapping strategy "triples" to have run already.
        try:
            mapping_session = MappingSessionUpdate(**session)
        except ValidationError as exc:
            error_message = "Session is missing required keys."
            LOGGER.error("%s\nsession: %r\nerror: %s", error_message, session, exc)
            raise InvalidOrMissingSession(error_message) from exc

        # Flatten the mapping triples
        flat_mapping = self._flatten_mapping(mapping_session)

        # Generate SOFT7 Entity pydantic model from the mapping
        entity_identity = flat_mapping[0].subject["namespace"]

        # For now, just expect a single entity to be required.
        # TODO: Update to support multiple entities.
        if not all(
            triple.subject["namespace"] == entity_identity for triple in flat_mapping
        ):
            raise NotImplementedError(
                "For now, the SOFT7 Generator function strategy only supports a single "
                "entity to be generated."
            )

        Entity = create_entity(entity_identity)

        # Retrieve the parsed data
        # TODO: Update this to be more flexible and "knowledge agnostic" - with this, I
        # mean, I only knew "content" would be in the session for the core JSON and CSV
        # parsers. There should be a "generic" or data model-strict way to get the
        # parsed data - and most likely not from the session.
        if "content" in session:
            parsed_data: dict = session["content"]
        else:
            raise NotImplementedError(
                "For now, the SOFT7 Generator function strategy only supports data "
                "parsed into the 'content' key of the session."
            )

        # Generate the reversed data dict to SOFT7 Entity mapping.
        # I.e., mapping for SOFT7 Entity to data dict for easier entity creation.
        # Expectation: The triple subject concept is a dot (.) separated path to the
        # data within the parsed data. The triple object concept is the dot (.)
        # separated path to the attribute/field within the SOFT7 Entity.
        # For example: "properties.name" -> "person.name"
        data_mapping = {
            triple.object["concept"]: triple.subject["concept"]
            for triple in flat_mapping
        }

        # Validate data mapping
        self._validate_data_mapping(data_mapping=data_mapping, entity=Entity)

        # Generate the SOFT7 Entity content
        # Dimensions
        entity_dimensions = {
            dimension[len("dimensions.") :]: self._get_parsed_datum(
                parsed_data, data_path
            )
            for dimension, data_path in data_mapping.items()
            if dimension.startswith("dimensions.")
        }

        # Top-level properties
        entity_properties = {
            property_name[len("properties.") :]: self._get_parsed_datum(
                parsed_data, data_path
            )
            for property_name, data_path in data_mapping.items()
            if property_name.startswith("properties.") and property_name.count(".") == 1
        }

        # Nested properties
        nested_properties = {
            property_name[len("properties.") :]
            for property_name in data_mapping
            if property_name.startswith("properties.") and property_name.count(".") > 1
        }
        while nested_properties:
            property_name = nested_properties.pop()
            property_name_parts = property_name.split(".")

            current_properties = entity_properties

            for depth in range(len(property_name_parts) - 1):
                current_properties[property_name_parts[depth]] = {}
                current_properties = current_properties[property_name_parts[depth]]

            current_properties[property_name_parts[-1]] = self._get_parsed_datum(
                parsed_data, data_mapping[f"properties.{property_name}"]
            )

        # Create the SOFT7 Entity instance
        entity = Entity(dimensions=entity_dimensions, properties=entity_properties)

        return SessionUpdate(soft7_entity_data=entity.model_dump())

    def _flatten_mapping(self, mapping: MappingSessionUpdate) -> list[RDFTriple]:
        """Flatten the mapping dictionary."""
        flat_mapping: list[RDFTriple] = []
        for triple in mapping.triples:
            flat_triple: list[RDFTriplePart] = []

            for part in triple:
                if any(part.startswith(namespace) for namespace in mapping.prefixes):
                    # Use namespace from mapping prefixes
                    namespace, concept = part.split(":", maxsplit=1)
                    flat_triple.append(
                        {
                            "namespace": AnyUrl(mapping.prefixes[namespace]),
                            "concept": concept,
                        }
                    )
                else:
                    # Deconstruct the part into namespace and concept
                    namespace, concept = part.split("#", maxsplit=1)
                    flat_triple.append(
                        {"namespace": AnyUrl(f"{namespace}#"), "concept": concept}
                    )

            flat_mapping.append(RDFTriple(*flat_triple))

        return flat_mapping

    def _validate_data_mapping(
        self, data_mapping: dict[str, str], entity: type[SOFT7EntityInstance]
    ) -> None:
        """Validate the data mapping."""
        # Validate dimensions:
        #  - Ensure there are no nested dimensions
        #  - Ensure all dimensions are present in the data mapping
        #  - Ensure the exact number of dimensions in the entity is present in the data
        #    mapping

        # Dimensions - Ensure there are no nested dimensions
        for dimension in data_mapping:
            if not dimension.startswith("dimensions."):
                # Not a dimension
                continue

            if dimension.count(".") > 1:
                raise ValueError("Nested dimensions are not supported.")

        # Dimensions - Ensure all dimensions are present in the data mapping
        for dimension in entity.model_fields["dimensions"].annotation.model_fields:  # type: ignore[union-attr]
            if f"dimensions.{dimension}" not in data_mapping:
                raise ValueError(
                    f"Dimension {dimension!r} is missing from the data mapping."
                )

        # Dimensions - Ensure the exact number of dimensions in the entity is present in
        # the data mapping
        if len(
            [
                dimension
                for dimension in data_mapping
                if dimension.startswith("dimensions.")
            ]
        ) != len(
            entity.model_fields["dimensions"].annotation.model_fields  # type: ignore[union-attr]
        ):
            raise ValueError(
                "The exact number of dimensions in the entity should be present in the "
                "data mapping."
            )

        # Validate properties:
        #  - Ensure all properties are present in the data mapping
        #  - Ensure the exact number of properties in the entity is present in the data
        #    mapping

        # Properties - Ensure all properties are present in the data mapping
        nested_properties = {
            property_name
            for property_name in data_mapping
            if property_name.startswith("properties.") and property_name.count(".") > 1
        }
        top_properties = set(data_mapping) - nested_properties

        for property_name in entity.model_fields["properties"].annotation.model_fields:  # type: ignore[union-attr]
            if f"properties.{property_name}" not in top_properties:
                raise ValueError(
                    f"Property {property_name!r} is missing from the data mapping."
                )

        nested_properties = {
            property_name[len("properties.") :] for property_name in nested_properties
        }
        while nested_properties:
            property_name = nested_properties.pop()
            property_name_parts = property_name.split(".")

            model_fields = entity.model_fields["properties"].annotation.model_fields  # type: ignore[union-attr]

            for depth in range(len(property_name_parts)):
                if property_name_parts[depth] not in model_fields:
                    raise ValueError(
                        f"Property {property_name!r} is missing from the data mapping."
                    )

                if not issubclass(
                    model_fields[property_name_parts[depth]].annotation, BaseModel
                ):
                    raise ValueError(
                        f"Property {property_name!r} is not a nested property according"
                        " to the entity."
                    )

                model_fields = (
                    model_fields[property_name_parts[depth]]
                    .annotation.model_fields["properties"]
                    .annotation.model_fields
                )  # type: ignore[union-attr]

        # Properties - Ensure the exact number of properties in the entity is present in
        # the data mapping
        total_number_of_properties = 0

        def _recursive_count_properties(model_field_infos: Sequence[FieldInfo]) -> None:
            nonlocal total_number_of_properties

            for property_value in model_field_infos:
                if property_value.annotation and issubclass(
                    property_value.annotation, SOFT7EntityInstance
                ):
                    _recursive_count_properties(
                        property_value.annotation.model_fields[  # type: ignore[union-attr]
                            "properties"
                        ].annotation.model_fields.values()
                    )
                else:
                    total_number_of_properties += 1

        _recursive_count_properties(
            entity.model_fields["properties"].annotation.model_fields.values()  # type: ignore[union-attr]
        )

        if (
            len(
                [
                    property_name
                    for property_name in data_mapping
                    if property_name.startswith("properties.")
                ]
            )
            != total_number_of_properties
        ):
            raise ValueError(
                "The exact number of properties in the entity should be present in the "
                "data mapping. This includes nested properties."
            )

    def _get_parsed_datum(self, parsed_data: dict, data_path: str) -> Any:
        """Get the parsed data from the parsed data dict."""
        data_path_parts = data_path.split(".")

        current_data = parsed_data

        for depth in range(len(data_path_parts)):
            if data_path_parts[depth] not in current_data:
                raise ValueError(
                    f"Data path {data_path!r} is missing from the parsed data."
                )

            current_data = current_data[data_path_parts[depth]]

        return current_data
