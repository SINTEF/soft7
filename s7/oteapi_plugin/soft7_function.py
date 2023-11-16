"""The SOFT7 OTEAPI Function strategy.

It expects mappings to be present in the session, and will use them to transform
the parsed data source into a SOFT7 Entity instance.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated, Any, NamedTuple, Union, cast

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
from s7.factories import create_entity_instance
from s7.oteapi_plugin.models import SOFT7FunctionConfig
from s7.pydantic_models.soft7_entity import SOFT7IdentityURI, parse_identity
from s7.pydantic_models.soft7_instance import SOFT7EntityInstance

if TYPE_CHECKING:  # pragma: no cover
    import sys

    if sys.version_info < (3, 12):
        from typing_extensions import TypedDict
    else:
        from typing import TypedDict

    ParsedDataType = Any
    ListParsedDataType = list[Union["ListParsedDataType", ParsedDataType]]

    ParsedDataPropertyType = Union[ParsedDataType, ListParsedDataType]

    class RDFTriplePart(TypedDict):
        """A part of a RDF triple, i.e., either a subject, predicate or object."""

        namespace: Union[AnyUrl, str]
        concept: str


class RDFTriple(NamedTuple):
    """A RDF triple."""

    subject: RDFTriplePart
    predicate: RDFTriplePart
    object: RDFTriplePart


LOGGER = logging.getLogger(__name__)


def entity_lookup(identity: SOFT7IdentityURI | str) -> type[SOFT7EntityInstance]:
    """Lookup and return a SOFT7 Entity Instance class."""
    import s7.factories.generated_classes as cls_module

    # Extract the name from the identity
    if not isinstance(identity, AnyUrl):
        try:
            identity = SOFT7IdentityURI(identity)
        except (ValidationError, TypeError) as exc:
            raise TypeError(
                f"identity must be a valid SOFT7 Identity URI. Got {identity!r} with "
                f"type {type(identity)}."
            ) from exc

    _, _, entity_name = parse_identity(identity)
    entity_name = entity_name.replace(" ", "")

    # Lookup the entity instance class
    try:
        cls = getattr(cls_module, entity_name)
    except AttributeError as exc:
        raise ValueError(
            f"Unable to find class with name {entity_name!r} in "
            f"{cls_module.__name__!r}."
        ) from exc

    if not isinstance(cls, type) and not issubclass(cls, SOFT7EntityInstance):
        error_message = (
            f"Class {entity_name!r} in {cls_module.__name__!r} is not a "
            f"{'subclass of ' if entity_name != 'SOFT7EntityInstance' else ''}"
            f"SOFT7EntityInstance."
        )
        raise ValueError(error_message)

    return cls


@dataclass
class SOFT7Generator:
    """SOFT7 Generator function strategy for OTEAPI.

    The strategy expects the following to be present in the session:
        - Mapping triples
        - Parsed data

    This means that it expects to be part of a pipeline like:

        DataResource >> Mapping >> SOFT7 Generator

    The strategy will use the mapping triples to transform the parsed data into a SOFT7
    Entity instance.

    Since the SOFT7 Generator function strategy is a core part of retrieving data in a
    Data Source factory, it expects to parse the data into a single Entity instance.

    """

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
        self._graph = self._parse_mapping(mapping_session)

        # Retrieve the parsed data
        self._parsed_data = self._retrieve_parsed_data(session)

        # Generate the reversed data dict to SOFT7 Entity mapping.
        # I.e., mapping for SOFT7 Entity to data dict for easier entity creation.
        # Expectation: The triple subject concept is a dot (.) separated path to the
        # data within the parsed data. The triple object concept is the dot (.)
        # separated path to the attribute/field within the SOFT7 Entity.
        # For example: "properties.name" -> "person.name"
        self._data_mapping = self._generate_data_mapping()
        print(self._data_mapping)

        # Create mapping of SOFT7 Identity URI to SOFT7 Entity Instance classes
        self._entities = self._generate_entities_mapping()
        print(self._entities)

        # Validate data mapping
        self._validate_data_mapping()

        # Generate the SOFT7 Entity instance
        generated_entity_instance = self._generate_entity_instance(
            entity_cls=self.function_config.configuration.entity
        )

        # Generate and return the SOFT7 Entity instance
        return SessionUpdate(
            soft7_entity_data=generated_entity_instance.model_dump(),
        )

    @property
    def entities(self) -> dict[SOFT7IdentityURI, type[SOFT7EntityInstance]]:
        """Return the mapping of SOFT7 Identity URI to SOFT7 Entity Instance classes."""
        if not hasattr(self, "_entities"):
            raise SOFT7FunctionError(
                "SOFT7Generator._entities is not set. This values is set in the "
                "SOFT7Generator.get() method."
            )
        return self._entities

    @property
    def graph(self) -> list[RDFTriple]:
        """Return the mapping triples."""
        if not hasattr(self, "_graph"):
            raise SOFT7FunctionError(
                "SOFT7Generator._graph is not set. This values is set in the "
                "SOFT7Generator.get() method."
            )
        return self._graph

    @property
    def parsed_data(self) -> dict[str, ParsedDataPropertyType]:
        """Return the parsed data."""
        if not hasattr(self, "_parsed_data"):
            raise SOFT7FunctionError(
                "SOFT7Generator._parsed_data is not set. This values is set in the "
                "SOFT7Generator.get() method."
            )
        return self._parsed_data

    @property
    def data_mapping(self) -> dict[SOFT7IdentityURI, dict[str, str]]:
        """Return the reversed data dict to SOFT7 Entity mapping."""
        if not hasattr(self, "_data_mapping"):
            raise SOFT7FunctionError(
                "SOFT7Generator._data_mapping is not set. This values is set in the "
                "SOFT7Generator.get() method."
            )
        return self._data_mapping

    def _parse_mapping(self, mapping_session: MappingSessionUpdate) -> list[RDFTriple]:
        """Parse the mapping session.

        TODO: Rewrite this function to parse mapping using a graph.
        """
        return self._flatten_mapping(mapping=mapping_session)

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

    def _generate_data_mapping(self) -> dict[SOFT7IdentityURI, dict[str, str]]:
        """Generate the reversed data dict to SOFT7 Entity mapping.

        I.e., mapping for SOFT7 Entity to data dict for easier entity creation.
        Expectation: The triple subject concept is a dot (.) separated path to the
        data within the parsed data. The triple object concept is the dot (.)
        separated path to the attribute/field within the SOFT7 Entity.

        For example: "properties.name" -> "person.name"

        TODO: This should be replaced by some graph work instead

        """
        data_mapping: dict[SOFT7IdentityURI, dict[str, str]] = {}

        for triple in self.graph:
            if not isinstance(triple.object["namespace"], AnyUrl):
                # Ignore non-URL namespaces - expecting all namespaces to be
                # SOFT7IdentityURIs
                continue

            data_mapping.setdefault(triple.object["namespace"], {})[
                triple.object["concept"]
            ] = triple.subject["concept"]

        return data_mapping

    def _generate_entities_mapping(
        self,
    ) -> dict[SOFT7IdentityURI, type[SOFT7EntityInstance]]:
        """Generate a mapping of SOFT7 Identity URI to SOFT7 Entity Instance classes.

        This is done by looking up the SOFT7 Entity Instance class from the generated
        classes module.

        If the SOFT7 Entity Instance class is not found, it is created.

        Parameters:
            identities: The SOFT7 Identity URIs to generate the mapping for.

        Returns:
            A mapping of SOFT7 Identity URI to SOFT7 Entity Instance classes.

        """
        mapping: dict[SOFT7IdentityURI, type[SOFT7EntityInstance]] = {}

        for entity_identity in self.data_mapping:
            try:
                entity_cls = entity_lookup(identity=entity_identity)
            except ValueError:
                # Entity not found in generated classes module, create it
                entity_cls = create_entity_instance(entity_identity)

            mapping[entity_identity] = entity_cls

        return mapping

    def _flatten_mapping(self, mapping: MappingSessionUpdate) -> list[RDFTriple]:
        """Flatten the mapping dictionary."""
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

    def _validate_data_mapping(self) -> None:
        """Validate the data mapping.

        TODO: This should be possible in a different way using the graph, I suspect?
        """
        refs: set[SOFT7IdentityURI] = set()
        for entity_identity, entity in self.entities.items():
            print("entity_identity", entity_identity)
            print("entity", entity)
            print("entity.entity", entity.entity)
            print(f"self.data_mapping[{entity_identity}]", self.data_mapping[entity_identity])
            refs.update(
                self._validate_data_mapping_for_entity(
                    self.data_mapping[entity_identity], entity
                )
            )

        # Create a list of entity identities without hashes (#)
        ref_equal_entities = [
            entity_identity.__class__(str(entity_identity).split("#", maxsplit=1)[0])
            for entity_identity in self.entities
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
                    f"Got {list(data_mapping.keys())}. Entity: {entity.entity}."
                )

        # Validate properties:
        #  - Ensure there are no nested dimensions
        #  - Ensure all properties are present in the data mapping, foregoing entity
        #    types

        # Properties - Ensure there are no nested properties
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
                    f"Property {property_name!r} is missing from the data mapping. "
                    f"Got {list(data_mapping.keys())}. Entity: {entity.entity}."
                )

        return refs

    def _generate_entity_instance(
        self, entity_cls: type[SOFT7EntityInstance]
    ) -> SOFT7EntityInstance:
        """(Recursively) Generate the SOFT7 Entity instance.

        Parameters:
            entity_cls: The SOFT7 Entity instance class to generate.

        Returns:
            The generated SOFT7 Entity instance.

        """
        data_mapping = self.data_mapping[entity_cls.entity.identity]

        # Dimensions
        entity_dimensions: dict[str, int | None] = {
            dimension: self._get_parsed_datum(
                data_mapping[f"dimensions.{dimension}"], dimension=True
            )
            for dimension in entity_cls.entity.dimensions or {}
        }

        # Non-entity instance properties
        entity_properties = {
            property_name: self._conform_to_shape(
                value=self._get_parsed_datum(
                    data_mapping[f"properties.{property_name}"]
                ),
                shape=property_value.shape,
                dimensions=entity_dimensions,
            )
            for property_name, property_value in entity_cls.entity.properties.items()
            if not isinstance(property_value.type_, AnyUrl)
        }

        # Entity instance properties
        entity_properties.update(
            {
                property_name: self._conform_to_shape(
                    value=self._generate_entity_instance(
                        self.entities[property_value.type_]
                    ),
                    shape=property_value.shape,
                    dimensions=entity_dimensions,
                    check_value_type=False,
                )
                for property_name, property_value in (
                    entity_cls.entity.properties.items()
                )
                if isinstance(property_value.type_, AnyUrl)
            }
        )

        # Create the SOFT7 Entity instance
        return entity_cls(dimensions=entity_dimensions, properties=entity_properties)

    def _conform_to_shape(
        self,
        value: Any,
        shape: list[str] | None,
        dimensions: dict[str, int | None],
        check_value_type: bool = True,
    ) -> Any | list[Any]:
        """Wrap a value in lists, conforming to a property shape.

        If shape is None, the value is returned as is.

        Parameters:
            valuey: The value to potentially wrap in lists.
            shape: The shape to conform to.
            dimensions: A mapping of shape dimensions to their int values.
            check_value_type: Whether to perform a sanity check on the type of the
                value before wrapping it. If this is False, the value is always wrapped.

        Returns:
            The potentially wrapped value.

        """
        if not shape:
            # No shape (empty list or None): return value as is
            return value

        if check_value_type and isinstance(value, list):
            # If the value is a list, we expect it to match with the shape already
            # and return it.
            #
            # TODO: Consider comparing with the specified property type here instead.
            #       A special case would need to be implemented if the property type
            #       is a list, since we would need to check the shape of the given value
            #       against the given shape.
            return value

        # Iterate over the shape in reverse order and wrap the value in lists
        # accordingly
        for dimension in reversed(shape):
            try:
                dimension_value = dimensions[dimension]
            except KeyError as exc:
                raise ValueError(
                    f"Dimension {dimension!r} is missing from the parsed dimensions."
                ) from exc

            if not isinstance(dimension_value, int):
                try:
                    dimension_value = int(dimension_value)  # type: ignore[call-overload]
                except (ValueError, TypeError) as exc:
                    raise TypeError(
                        f"Dimension {dimension!r} is not an integer. Got "
                        f"{dimension_value!r}."
                    ) from exc

            value = [value] * dimension_value

        return value

    def _get_parsed_datum(
        self, data_path: str, dimension: bool = False
    ) -> ParsedDataType:
        """Get the parsed data from the parsed data dict.

        Currently, we only expect the parsed data to come from the JSON or CSV parser,
        meaning, we only expect the types: dict, list, str, int, float, bool, None.
        """
        data_path_parts = data_path.split(".")

        def __recursively_get_parsed_datum(
            data: ParsedDataPropertyType | dict[str, ParsedDataPropertyType],
            depth: int = 0,
        ) -> (
            ParsedDataType | ParsedDataPropertyType | dict[str, ParsedDataPropertyType]
        ):
            """Recursively get the parsed data from the parsed data dict."""
            next_part = data_path_parts[depth]

            # Handle the case of the data being a list
            if isinstance(data, list):
                # TODO: Consider supporting other than list indexes, e.g., slices, etc.

                # Check if the data path part is a list index
                try:
                    next_part_as_index = int(next_part)
                except (ValueError, TypeError) as exc:
                    if dimension:
                        # If the current data is a list, and the data path is mapped to
                        # a dimension, then we expect the length of the list to be the
                        # value of the dimension

                        # First, we ensure this is the last level/data path part
                        if next_part != data_path_parts[-1]:
                            raise ValueError(
                                "Data path is mapped to a dimension, but the current "
                                "data path part is not the last level of the data "
                                "path. Hint: Possibly add a list index to the data "
                                "path."
                            ) from exc

                        return len(data)

                    raise ValueError(
                        f"Data path {data_path!r} is missing from the parsed "
                        "data. Got a list, but no list index was given in the data "
                        "path."
                    ) from exc

                # The current data path part _is_ a list index
                try:
                    return __recursively_get_parsed_datum(
                        data[next_part_as_index], depth=depth + 1
                    )
                except IndexError as exc:
                    raise ValueError(
                        f"Data path {data_path!r} is missing from the parsed "
                        f"data. Index {next_part_as_index} out of "
                        "range."
                    ) from exc

            elif isinstance(data, dict):
                if next_part not in data:
                    # The data path part cannot be found in current data dict.
                    previous_part = (
                        data_path_parts[depth - 1] if (depth - 1) >= 0 else "/"
                    )
                    raise ValueError(
                        f"Data path {data_path!r} is either invalid or missing from "
                        "the parsed data. Specifically, the data path part "
                        f"{next_part!r} could not be found in the "
                        f"{previous_part!r} dict."
                    )

                return __recursively_get_parsed_datum(data[next_part], depth=depth + 1)

            else:
                # We do not expect other container types than dict and list (for now),
                # so we raise an error - expecting the given data path to either be
                # invalid or missing from the parsed data.
                raise ValueError(
                    f"Data path {data_path!r} is either invalid or missing from the "
                    "parsed data."
                )

        datum = __recursively_get_parsed_datum(self.parsed_data)

        if TYPE_CHECKING:  # pragma: no cover
            datum = cast(ParsedDataType, datum)

        return datum
