"""The SOFT7 OTEAPI Function strategy."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated, Any, NamedTuple, cast

from oteapi.models import AttrDict
from pydantic import AnyUrl, Field, ValidationError
from pydantic.dataclasses import dataclass

# from pydantic.dataclasses import dataclass
from s7.exceptions import (
    InvalidMapping,
    SOFT7FunctionError,
)
from s7.factories import create_entity
from s7.oteapi_plugin.models import SOFT7FunctionConfig
from s7.pydantic_models.soft7_entity import (
    SOFT7IdentityURI,
    SOFT7IdentityURIType,
    parse_identity,
)
from s7.pydantic_models.soft7_instance import SOFT7EntityInstance

if TYPE_CHECKING:  # pragma: no cover
    import sys
    from typing import Optional, Union

    if sys.version_info < (3, 12):
        from typing_extensions import TypedDict
    else:
        from typing import TypedDict

    from oteapi.strategies.mapping.mapping import MappingStrategyConfig

    ParsedDataType = Any
    ListParsedDataType = list[Union["ListParsedDataType", ParsedDataType]]

    ParsedDataPropertyType = Union[ParsedDataType, ListParsedDataType]

    SOFT7IdentityURITypeOrStr = Union[SOFT7IdentityURIType, str]

    class RDFTriplePart(TypedDict):
        """A part of a RDF triple, i.e., either a subject, predicate or object."""

        namespace: SOFT7IdentityURITypeOrStr
        concept: str


class RDFTriple(NamedTuple):
    """A RDF triple."""

    subject: RDFTriplePart
    predicate: RDFTriplePart
    object: RDFTriplePart


LOGGER = logging.getLogger(__name__)


def entity_lookup(
    identity: Union[SOFT7IdentityURIType, str]
) -> type[SOFT7EntityInstance]:
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

    The strategy expects to be part of a pipeline like:

        DataResource >> Mapping >> SOFT7 Generator

    This means, it expects certain configuration settings to be set by the other
    strategies in the pipeline.

    The strategy will use the mapping triples to transform the parsed data into a SOFT7
    Entity instance.

    Since the SOFT7 Generator function strategy is a core part of retrieving data in a
    Data Source factory, it expects to parse the data into a single Entity instance.

    """

    function_config: Annotated[
        SOFT7FunctionConfig, Field(description=SOFT7FunctionConfig.__doc__)
    ]

    def initialize(self) -> AttrDict:
        """Initialize the SOFT7 Generator function strategy."""
        return AttrDict()

    def get(self) -> AttrDict:
        """Execute the SOFT7 Generator function strategy."""
        # Expect the mapping strategy "triples" to have run already.
        # Expect the parser strategy to have run already.
        if any(
            config_value is None
            for config_value in (
                # mapping
                self.function_config.configuration.prefixes,
                self.function_config.configuration.triples,
                # parsed data resource
                self.function_config.configuration.content,
            )
        ):
            raise SOFT7FunctionError(
                "The SOFT7 Generator function strategy expects the 'prefixes', "
                "'triples', and 'content' fields to be set in the "
                "SOFT7FunctionConfig.\n"
                "Hint: Ensure the Mapping strategy and a DataResource or a Parser "
                "strategies are run before the SOFT7 Generator strategy."
            )

        # Parse the mapping triples
        self._graph = self._parse_mapping()

        # Generate the reversed data dict to SOFT7 Entity mapping.
        # I.e., mapping for SOFT7 Entity to data dict for easier entity creation.
        # Expectation: The triple subject concept is a dot (.) separated path to the
        # data within the parsed data. The triple object concept is the dot (.)
        # separated path to the attribute/field within the SOFT7 Entity.
        # For example: "properties.name" -> "person.name"
        self._data_mapping = self._generate_data_mapping()

        # Create mapping of SOFT7 Identity URI to SOFT7 Entity Instance classes
        self._entities = self._generate_entities_mapping()

        # Validate data mapping
        self._validate_data_mapping()

        # Generate the SOFT7 Entity instance
        generated_entity_instance = self._generate_entity_instance(
            entity_cls=self.function_config.configuration.entity
        )

        # Generate and return the SOFT7 Entity instance
        return AttrDict(
            soft7_entity_data=generated_entity_instance.model_dump(),
        )

    @property
    def entities(self) -> dict[SOFT7IdentityURIType, type[SOFT7EntityInstance]]:
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
    def data_mapping(self) -> dict[SOFT7IdentityURIType, dict[str, str]]:
        """Return the reversed data dict to SOFT7 Entity mapping."""
        if not hasattr(self, "_data_mapping"):
            raise SOFT7FunctionError(
                "SOFT7Generator._data_mapping is not set. This values is set in the "
                "SOFT7Generator.get() method."
            )
        return self._data_mapping

    def _parse_mapping(self) -> list[RDFTriple]:
        """Parse the mapping.

        TODO: Rewrite this function to parse mapping using a graph.
        """
        return self._flatten_mapping(mapping=self.function_config.configuration)

    def _generate_data_mapping(self) -> dict[SOFT7IdentityURIType, dict[str, str]]:
        """Generate the reversed data dict to SOFT7 Entity mapping.

        I.e., mapping for SOFT7 Entity to data dict for easier entity creation.
        Expectation: The triple subject concept is a dot (.) separated path to the
        data within the parsed data. The triple object concept is the dot (.)
        separated path to the attribute/field within the SOFT7 Entity.

        For example: "properties.name" -> "person.name"

        TODO: This should be replaced by some graph work instead

        """
        data_mapping: dict[SOFT7IdentityURIType, dict[str, str]] = {}

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
    ) -> dict[SOFT7IdentityURIType, type[SOFT7EntityInstance]]:
        """Generate a mapping of SOFT7 Identity URI to SOFT7 Entity Instance classes.

        This is done by looking up the SOFT7 Entity Instance class from the generated
        classes module.

        If the SOFT7 Entity Instance class is not found, it is created.

        Parameters:
            identities: The SOFT7 Identity URIs to generate the mapping for.

        Returns:
            A mapping of SOFT7 Identity URI to SOFT7 Entity Instance classes.

        """
        mapping: dict[SOFT7IdentityURIType, type[SOFT7EntityInstance]] = {}

        for entity_identity in self.data_mapping:
            try:
                entity_cls = entity_lookup(identity=entity_identity)
            except ValueError:
                # Entity not found in generated classes module, create it
                entity_cls = create_entity(entity_identity)

            mapping[entity_identity] = entity_cls

        return mapping

    @staticmethod
    def _flatten_mapping(mapping: MappingStrategyConfig) -> list[RDFTriple]:
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
                            "namespace": SOFT7IdentityURI(mapping.prefixes[namespace]),
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
                        {"namespace": SOFT7IdentityURI(namespace), "concept": concept}
                    )

            flat_mapping.append(RDFTriple(*flat_triple))

        return flat_mapping

    def _validate_data_mapping(self) -> None:
        """Validate the data mapping.

        TODO: This should be possible in a different way using the graph, I suspect?
        """
        refs: set[SOFT7IdentityURIType] = set()
        for entity_identity, entity in self.entities.items():
            refs.update(
                self._validate_data_mapping_for_entity(
                    self.data_mapping[entity_identity], entity
                )
            )

        while refs:
            ref = refs.pop()  # noqa: F841

            # if ref not in self.entities:
            #     raise InsufficientData(
            #         f"SOFT7 Entity identity {ref} is missing from the data mapping."
            #     )

    def _validate_data_mapping_for_entity(
        self, data_mapping: dict[str, str], entity: type[SOFT7EntityInstance]
    ) -> set[SOFT7IdentityURIType]:
        """Validate the data mapping for a specific entity.

        Data mapping is reversed, i.e., mapping from SOFT7 Entity to parsed data dict.

        Ignore all refs, returning them instead as a set.

        ### Validation

        The dimensions are validated with the following rules:
        - Ensure there are no nested dimensions
        - Ensure all dimensions in the entity are present in the data mapping

        The properties are validated with the following rules:
        - Ensure there are no nested properties
        - Ensure all properties are present in the data mapping, foregoing entity types

        """
        refs: set[SOFT7IdentityURIType] = set()

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
            if isinstance(property_value.type, AnyUrl):
                refs.add(property_value.type)
                continue

            if f"properties.{property_name}" not in data_mapping:
                raise InvalidMapping(
                    f"Property {property_name!r} is missing from the data mapping. "
                    f"Got {list(data_mapping.keys())}. Entity: {entity.entity}."
                )

        return refs

    def _generate_entity_instance(
        self, entity_cls: type[SOFT7EntityInstance], data_path: Optional[str] = None
    ) -> SOFT7EntityInstance:
        """(Recursively) Generate the SOFT7 Entity instance.

        Note: If a dimension or property is not found in the data mapping, it will be
        skipped.

        Parameters:
            entity_cls: The SOFT7 Entity instance class to generate.

        Returns:
            The generated SOFT7 Entity instance.

        """
        data_mapping = self.data_mapping[entity_cls.entity.identity]

        if data_path:
            no_index_data_path = ".".join(data_path.split(".")[:-1])

        # Dimensions
        entity_dimensions: dict[str, int] = {}

        for dimension in entity_cls.entity.dimensions or {}:
            if f"dimensions.{dimension}" not in data_mapping:
                # Dimension is not in the data mapping, skip it
                continue

            indexed_data_path = (
                data_mapping[f"dimensions.{dimension}"].replace(
                    no_index_data_path, data_path
                )
                if data_path
                else data_mapping[f"dimensions.{dimension}"]
            )

            parsed_dimension_value = self._get_parsed_datum(
                indexed_data_path, dimension=True
            )
            if parsed_dimension_value is not None:
                entity_dimensions[dimension] = parsed_dimension_value

        # Properties
        entity_properties: dict[str, ParsedDataType] = {}

        for property_name, property_value in entity_cls.entity.properties.items():
            if f"properties.{property_name}" not in data_mapping:
                # Property is not in the data mapping, skip it
                continue

            if not isinstance(property_value.type, AnyUrl):
                # Non-entity instance properties

                # Use the data path if given, otherwise use the data mapping.
                # The data path here is only given if this is a shaped Entity instance
                # property. In which case this will be the data path to the entity
                # instance with an added list index.
                indexed_data_path = (
                    data_mapping[f"properties.{property_name}"].replace(
                        no_index_data_path, data_path
                    )
                    if data_path
                    else data_mapping[f"properties.{property_name}"]
                )

                parsed_property_value = self._get_parsed_datum(indexed_data_path)

            # Entity instance properties

            # There should be no list index in the mapping for these, so we need to
            # add them if this is a shaped property.

            # Shaped Entity instance property
            elif property_value.shape:
                # At this point we only accept a 1-dimensional list shape for Entity
                # instance properties.
                #
                # TODO: This should be fixed, most likely using NumPy arrays.
                if len(property_value.shape) != 1:
                    raise NotImplementedError(
                        "Only 1-dimensional list shape is supported for Entity "
                        "instance properties."
                    )

                parsed_property_value = []

                dimension_value = entity_dimensions[property_value.shape[0]]

                for list_index in range(dimension_value):
                    indexed_data_path = (
                        data_mapping[f"properties.{property_name}"].replace(
                            no_index_data_path, data_path
                        )
                        if data_path
                        else data_mapping[f"properties.{property_name}"]
                    )

                    indexed_data_path += f".{list_index}"

                    parsed_property_value.append(
                        self._generate_entity_instance(
                            self.entities[property_value.type],
                            data_path=indexed_data_path,
                        )
                    )

            # Non-shaped Entity instance property
            else:
                parsed_property_value = self._generate_entity_instance(
                    self.entities[property_value.type],
                    data_path=data_path,
                )

            if parsed_property_value is not None:
                entity_properties[property_name] = parsed_property_value

        # Create the SOFT7 Entity instance
        return entity_cls(dimensions=entity_dimensions, properties=entity_properties)

    def _get_parsed_datum(
        self, data_path: str, dimension: bool = False
    ) -> ParsedDataType:
        """Get the parsed data from the parsed data dict.

        Currently, we only expect the parsed data to come from the JSON or CSV parser,
        meaning, we only expect the types: dict, list, str, int, float, bool, None.
        """
        data_path_parts = data_path.split(".")

        def __recursively_get_parsed_datum(
            data: Union[ParsedDataPropertyType, dict[str, ParsedDataPropertyType]],
            depth: int = 0,
        ) -> Union[
            ParsedDataType, ParsedDataPropertyType, dict[str, ParsedDataPropertyType]
        ]:
            """Recursively get the parsed data from the parsed data dict."""
            try:
                next_part = data_path_parts[depth]
            except IndexError:
                # We have reached the end of the data path parts
                if isinstance(data, list) and dimension:
                    # If the current data is a list, and the data path is mapped to
                    # a dimension, then we expect the length of the list to be the
                    # value of the dimension
                    return len(data)

                return data

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

        datum = __recursively_get_parsed_datum(
            self.function_config.configuration.content
        )

        if TYPE_CHECKING:  # pragma: no cover
            datum = cast(ParsedDataType, datum)

        return datum
