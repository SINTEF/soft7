"""The SOFT7 OTEAPI Function strategy.

It expects mappings to be present in the session, and will use them to transform
the parsed data source into a SOFT7 Entity instance.
"""
from __future__ import annotations

import logging
from copy import deepcopy
from typing import TYPE_CHECKING, Annotated, Any, NamedTuple

from oteapi.models import SessionUpdate
from oteapi.strategies.mapping.mapping import MappingSessionUpdate
from pydantic import AnyUrl, Field, ValidationError
from pydantic.dataclasses import dataclass

# from pydantic.dataclasses import dataclass
from s7.exceptions import (
    InsufficientData,
    InvalidMapping,
    InvalidOrMissingSession,
    SOFT7FunctionError,
)
from s7.factories import create_entity
from s7.oteapi_plugin.models import SOFT7FunctionConfig
from s7.pydantic_models.soft7_instance import SOFT7EntityInstance, SOFT7IdentityURI

if TYPE_CHECKING:  # pragma: no cover
    from typing import TypedDict, Union

    ParsedDataType = Any
    ListParsedDataType = list[Union["ListParsedDataType", ParsedDataType]]

    ParsedDataPropertyType = Union[ParsedDataType, ListParsedDataType]

    class RDFTriplePart(TypedDict):
        """A part of a RDF triple, i.e., either a subject, predicate or object."""

        namespace: AnyUrl | str
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

    def initialize(self, session: dict[str, Any] | None) -> SessionUpdate:
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

        # Parse the mapping triples
        graph = self._parse_mapping(mapping_session)

        # Retrieve mapping structure of identity to SOFT7 Entity class
        entities = self._retrieve_entities(graph)

        # Retrieve the parsed data
        parsed_data = self._retrieve_parsed_data(session)

        ##### TODO : Rejig code from here on to better handle nested properties #####

        # Generate the reversed data dict to SOFT7 Entity mapping.
        # I.e., mapping for SOFT7 Entity to data dict for easier entity creation.
        # Expectation: The triple subject concept is a dot (.) separated path to the
        # data within the parsed data. The triple object concept is the dot (.)
        # separated path to the attribute/field within the SOFT7 Entity.
        # For example: "properties.name" -> "person.name"
        #
        # TODO: This should be replaced by some graph work instead
        data_mapping = {
            entity_identity: {
                triple.object["concept"]: triple.subject["concept"]
                for triple in graph
                if triple.object["namespace"] == entity_identity
            }
            for entity_identity in entities
        }

        # Validate data mapping
        self._validate_data_mapping(data_mapping=data_mapping, entities=entities)

        # Determine generation order
        ordered_entities = self._determine_generation_order(entities=entities)

        # Generate the SOFT7 Entity instance
        generated_entity_instances = [
            self._generate_and_dump_entity_instance(
                parsed_data=parsed_data,
                data_mapping=data_mapping[entity.entity.identity],
                entity_cls=entity,
            )
            for entity in ordered_entities
        ]

        return SessionUpdate(
            soft7_entity_data=generated_entity_instances[0]
            if len(generated_entity_instances) == 1
            else generated_entity_instances
        )

    def _parse_mapping(self, mapping_session: MappingSessionUpdate) -> list[RDFTriple]:
        """Parse the mapping session.

        TODO: Rewrite this function to parse mapping using a graph.
        """
        return self._flatten_mapping(mapping=mapping_session)

    def _retrieve_entities(
        self, graph: list[RDFTriple]
    ) -> dict[AnyUrl, type[SOFT7EntityInstance]]:
        """Retrieve the entities from the graph.

        TODO: Rewrite this function to perform a proper RDF query to retrieve all
            entity identities.
        """
        graph = deepcopy(graph)

        entities = {
            triple.object["namespace"]
            for triple in graph
            if isinstance(triple.object["namespace"], AnyUrl)
        }

        return {
            entity_identity: create_entity(entity_identity)
            for entity_identity in entities
        }

    def _retrieve_parsed_data(self, session: dict[str, Any]) -> dict:
        """Retrieve the parsed data from the session.

        TODO: Update this to be more flexible and "knowledge agnostic" - with this, I
            mean, I only knew "content" would be in the session for the core JSON and
            CSV parsers. There should be a "generic" or data model-strict way to get the
            parsed data - and most likely not from the session.
        """
        if "content" in session:
            parsed_data: dict = session["content"]
        else:
            raise NotImplementedError(
                "For now, the SOFT7 Generator function strategy only supports data "
                "parsed into the 'content' key of the session."
            )

        return parsed_data

    def _flatten_mapping(self, mapping: MappingSessionUpdate) -> list[RDFTriple]:
        """Flatten the mapping dictionary."""
        mapping = deepcopy(mapping)

        flat_mapping: list[RDFTriple] = []
        for triple in mapping.triples:
            flat_triple: list[RDFTriplePart] = []

            for part in triple:
                if not part:
                    flat_triple.append({"namespace": "", "concept": ""})
                    continue

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
                    try:
                        # Deconstruct the part into namespace and concept
                        namespace, concept = part.split("#", maxsplit=1)
                    except ValueError as exc:
                        raise SOFT7FunctionError(
                            f"Invalid triple part ({part!r}). Namespace not found in "
                            "mapping configuration, and cannot split namespace and "
                            "concept on hash (#)."
                        ) from exc

                    flat_triple.append(
                        {"namespace": AnyUrl(f"{namespace}#"), "concept": concept}
                    )

            flat_mapping.append(RDFTriple(*flat_triple))

        return flat_mapping

    def _validate_data_mapping(
        self,
        data_mapping: dict[AnyUrl, dict[str, str]],
        entities: dict[AnyUrl, type[SOFT7EntityInstance]],
    ) -> None:
        """Validate the data mapping.

        TODO: This should be possible in a different way using the graph, I suspect?
        """
        data_mapping = deepcopy(data_mapping)
        entities = deepcopy(entities)

        refs: set[SOFT7IdentityURI] = set()
        for entity_identity, entity in entities.items():
            refs.update(
                self._validate_data_mapping_for_entity(
                    data_mapping[entity_identity], entity
                )
            )

        # Create a list of entity identities without hashes (#)
        ref_equal_entities = [
            entity_identity.__class__(str(entity_identity).split("#", maxsplit=1)[0])
            for entity_identity in entities
        ]

        while refs:
            ref = refs.pop()

            # Ignore any hashes (#)
            # This should already be the case, but it does not have to be,
            # so we do it anyway.
            ref = ref.__class__(str(ref).split("#", maxsplit=1)[0])

            if ref not in ref_equal_entities:
                raise InsufficientData(
                    f"SOFT7 Entity identity {ref} is missing from the data mapping."
                )

    def _validate_data_mapping_for_entity(
        self, data_mapping: dict[str, str], entity: type[SOFT7EntityInstance]
    ) -> set[SOFT7IdentityURI]:
        """Validate the data mapping for a specific entity.

        Data mapping is reversed, i.e., mapping from SOFT7 Entity to parsed data dict.

        Ignore all refs, returning them instead as a set.
        """
        data_mapping = deepcopy(data_mapping)
        entity = deepcopy(entity)

        refs: set[SOFT7IdentityURI] = set()

        # Validate dimensions:
        #  - Ensure there are no nested dimensions
        #  - Ensure all dimensions in the entity are present in the data mapping

        # Dimensions - Ensure there are no nested dimensions
        for dimension_name in data_mapping:
            if not dimension_name.startswith("dimensions."):
                # Not a dimension
                continue

            if dimension_name.count(".") > 1:
                raise InvalidMapping("Nested dimensions are not supported.")

        # Dimensions - Ensure all dimensions are present in the data mapping
        for dimension_name in entity.entity.dimensions or {}:
            if f"dimensions.{dimension_name}" not in data_mapping:
                raise InvalidMapping(
                    f"Dimension {dimension_name!r} is missing from the data mapping. "
                    f"Got {data_mapping.keys()}. Entity: {entity.entity}."
                )

        # Validate properties:
        #  - Ensure there are no nested dimensions
        #  - Ensure all properties are present in the data mapping, foregoing entity
        #    types

        # Dimensions - Ensure there are no nested dimensions
        for property_name in data_mapping:
            if not property_name.startswith("properties."):
                # Not a property
                continue

            if property_name.count(".") > 1:
                raise InvalidMapping("Nested properties are not supported.")

        # Properties - Ensure all properties are present in the data mapping, foregoing
        # entity types
        for property_name, property_value in entity.entity.properties.items():
            if isinstance(property_value.type_, AnyUrl):
                refs.add(property_value.type_)
                continue

            if f"properties.{property_name}" not in data_mapping:
                raise InvalidMapping(
                    f"Property {property_name!r} is missing from the data mapping."
                    f"Got {data_mapping.keys()}. Entity: {entity.entity}."
                )

        return refs

    def _determine_generation_order(
        self, entities: dict[AnyUrl, type[SOFT7EntityInstance]]
    ) -> list[type[SOFT7EntityInstance]]:
        """Determine the generation order of the entities.

        TODO: This should be replaced with a graph traversal for "isPartOf" relations
            or similar.
        """
        entities = deepcopy(entities)

        ordered_entities = []
        handled_entities = set()
        all_entities = set(entities.values())

        for entity in entities.values():
            if not any(
                isinstance(property_value.type_, AnyUrl)
                for property_value in entity.entity.properties.values()
            ):
                # No references, add to ordered entities
                ordered_entities.append(entity)

                # Deal with in-memory references
                handled_entities.add(entity.entity.identity)
                all_entities.remove(entity)

        while all_entities:
            prior_number_of_handled_entities = len(handled_entities)

            for entity in all_entities.copy():
                if all(
                    isinstance(property_value.type_, AnyUrl)
                    and property_value.type_ in handled_entities
                    for property_value in entity.entity.properties.values()
                ):
                    # All references are in ordered and handled entities, add to
                    # ordered entities
                    ordered_entities.append(entity)

                    # Deal with in-memory references
                    handled_entities.add(entity.entity.identity)
                    all_entities.remove(entity)

            post_number_of_handled_entities = len(handled_entities)

            # Ensure we don't end up in an infinite loop
            # This could happen if there are entities without its references in the
            # entities dict
            if prior_number_of_handled_entities == post_number_of_handled_entities:
                raise SOFT7FunctionError(
                    "Unable to determine generation order of entities. This is likely "
                    "due to an entity missing from the data mapping."
                )

        return ordered_entities

    def _generate_and_dump_entity_instance(
        self,
        parsed_data: dict,
        data_mapping: dict[str, str],
        entity_cls: type[SOFT7EntityInstance],
    ) -> dict[str, Any]:
        """Generate and dump a SOFT7 Entity instance."""
        parsed_data = deepcopy(parsed_data)
        data_mapping = deepcopy(data_mapping)
        entity_cls = deepcopy(entity_cls)

        # Dimensions
        entity_dimensions = {
            dimension[len("dimensions.") :]: self._get_parsed_datum(
                parsed_data, data_path, dimension=True
            )
            for dimension, data_path in data_mapping.items()
            if dimension.startswith("dimensions.")
        }

        # Properties
        entity_properties = {
            property_name[len("properties.") :]: self._get_parsed_datum(
                parsed_data, data_path
            )
            for property_name, data_path in data_mapping.items()
            if property_name.startswith("properties.")
        }

        # Create the SOFT7 Entity instance
        entity = entity_cls(dimensions=entity_dimensions, properties=entity_properties)

        # Dump the SOFT7 Entity instance to a dict
        return entity.model_dump()

    def _get_parsed_datum(
        self, parsed_data: dict, data_path: str, dimension: bool = False
    ) -> Any:
        """Get the parsed data from the parsed data dict."""
        data_path_parts = data_path.split(".")

        current_data = deepcopy(parsed_data)

        for depth in range(len(data_path_parts)):
            if data_path_parts[depth] not in current_data:
                # Check if the data path is a list index
                try:
                    int(data_path_parts[depth])
                except (ValueError, TypeError):
                    pass
                else:
                    if isinstance(current_data, list):
                        try:
                            current_data = current_data[int(data_path_parts[depth])]
                        except IndexError as exc:
                            raise ValueError(
                                f"Data path {data_path!r} is missing from the parsed "
                                f"data. Index {int(data_path_parts[depth])} out of "
                                "range."
                            ) from exc
                        else:
                            continue
                    else:
                        raise ValueError(
                            f"Data path {data_path!r} is missing from the parsed "
                            "data. Got a list index, but the current data is not a "
                            "list."
                        )

                # Check if the current data is a list, and if so, if it contains a dict
                # with the data path as a key
                if isinstance(current_data, list):
                    if dimension:
                        # If the current data is a list, and the data path is mapped to
                        # a dimension, then we expect the length of the list to be the
                        # value of the dimension
                        return len(current_data)

                    try:
                        # Use index 0 always
                        current_data = current_data[0][data_path_parts[depth]]
                    except (IndexError, KeyError) as exc:
                        raise ValueError(
                            f"Data path {data_path!r} is missing from the parsed data. "
                            "Got a list, but the current data does not contain a dict "
                            "with the data path as a key."
                        ) from exc
                    else:
                        continue

                raise ValueError(
                    f"Data path {data_path!r} is missing from the parsed data."
                )

            current_data = current_data[data_path_parts[depth]]

        return current_data
