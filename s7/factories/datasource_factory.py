"""Generate SOFT7 entity instances based on basic information:

1. Data source (DB, File, Webpage, ...).
2. Generic data source parser.
3. Data source parser configuration.
4. SOFT7 entity (data model).

Parts 2 and 3 are together considered to produce the "specific parser".
Parts 1 through 3 are provided through a single dictionary based on the
`ResourceConfig` from `oteapi.models`.

"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from otelib import OTEClient
from pydantic import AnyUrl, Field, FileUrl, create_model

from s7.pydantic_models.datasource import (
    DataSourceDimensions,
    SOFT7DataSource,
    parse_input_configs,
)
from s7.pydantic_models.soft7_entity import (
    SOFT7Entity,
    SOFT7IdentityURIType,
    parse_identity,
    parse_input_entity,
)
from s7.pydantic_models.soft7_instance import (
    generate_dimensions_docstring,
    generate_model_docstring,
    generate_property_type,
)

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, TypedDict

    from oteapi.models import GenericConfig

    from s7.pydantic_models.datasource import (
        GetData,
        GetDataConfigDict,
    )
    from s7.pydantic_models.soft7_entity import PropertyType

    class SOFT7InstanceDict(TypedDict):
        """A dictionary representation of a SOFT7 instance."""

        dimensions: Optional[dict[str, int]]
        properties: dict[str, Any]


DEFAULT_OTEAPI_SERVICES_BASE_URL = "http://localhost:8080"

LOGGER = logging.getLogger(__name__)

CACHE: dict[int, dict[str, Any]] = {}
"""A cache of the OTEAPI pipeline results."""


def create_pipeline_id(configs: GetDataConfigDict, url: str) -> int:
    """Hash given inputs and return it."""
    return hash((*((key, configs[key]) for key in sorted(configs)), url))  # type: ignore[literal-required]


def _get_data(
    config: GetDataConfigDict,
    *,
    url: str | None = None,
) -> GetData:
    """Get a datum via an OTEAPI pipeline.

    The OTEAPI pipeline will look like:

        DataResource -> Parser -> Mapping -> Function

    It may be that the Mapping strategy is left out.

    Everything in the __get_data() function will not be called until the first time
    the attribute `name` is accessed.

    To do something "lazy", it should be moved to the __get_data() function.
    To instead pre-cache something, it should be moved outside of the __get_data()
    function.

    Parameters:
        config: Mapping for all necessary OTEAPI strategy configuration.
        url: The base URL of the OTEAPI service instance to use.

    Returns:
        A function that will return the value of a named dimension or property.

    """
    # OTEAPI pipeline configuration
    client = OTEClient(url or DEFAULT_OTEAPI_SERVICES_BASE_URL)

    ote_data_resource = client.create_dataresource(
        **config["dataresource"].model_dump()
    )
    ote_function = client.create_function(**config["function"].model_dump())
    ote_parser = client.create_parser(**config["parser"].model_dump())

    if "mapping" in config:
        ote_mapping = client.create_mapping(**config["mapping"].model_dump())  # type: ignore[typeddict-item]

        ote_pipeline = ote_data_resource >> ote_parser >> ote_mapping >> ote_function
    else:
        raise NotImplementedError(
            "Only OTEAPI pipelines with a mapping are supported for now, i.e., "
            "implicit 1:1 mapping is currently not supported."
        )
        # ote_pipeline = ote_data_resource >> ote_parser >> ote_function

    # Remove unused variables from memory
    del client

    pipeline_id = create_pipeline_id(config, url or DEFAULT_OTEAPI_SERVICES_BASE_URL)

    def __get_data(soft7_property: str) -> Any:
        """Get a named datum (property or dimension) from the data resource.

        Properties:
            soft7_property: The name of a datum to get, i.e., the SOFT7 data resource
                (property or dimension).

        Returns:
            The value of the SOFT7 data resource (property or dimension).

        """
        LOGGER.debug("soft7_property: %r", soft7_property)

        if pipeline_id not in CACHE:
            LOGGER.debug(
                "Running OTEAPI pipeline: %r (id: %r)", ote_pipeline, pipeline_id
            )
            # Should only run once per pipeline - after that we retrieve from the cache
            pipeline_result: dict[str, Any] = json.loads(ote_pipeline.get())
            CACHE[pipeline_id] = pipeline_result
        else:
            pipeline_result = CACHE[pipeline_id]

        LOGGER.debug("Pipeline result: %r", pipeline_result)

        # TODO: Use variable from SOFT7 OTEAPI Function configuration instead of
        # 'soft7_entity_data'. Maybe even consider parsing `pipeline_result` into the
        # eventual Session model to thereby validate the desired keys are present.
        if "soft7_entity_data" not in pipeline_result:
            error_message = (
                "The OTEAPI pipeline did not return the expected data structure."
            )
            LOGGER.error(
                "%s\nsoft7_property: %r\npipeline_result: %r",
                error_message,
                soft7_property,
                pipeline_result,
            )
            raise ValueError(error_message)

        data: SOFT7InstanceDict = pipeline_result["soft7_entity_data"]

        if soft7_property in data["properties"]:
            LOGGER.debug(
                "Returning property: %r = %r",
                soft7_property,
                data["properties"][soft7_property],
            )
            return data["properties"][soft7_property]

        if (
            "dimensions" in data
            and data["dimensions"]
            and soft7_property in data["dimensions"]
        ):
            LOGGER.debug(
                "Returning dimension: %r = %r",
                soft7_property,
                data["dimensions"][soft7_property],
            )
            return data["dimensions"][soft7_property]

        error_message = f"{soft7_property!r} could not be determined for the resource."
        LOGGER.error(
            "%s\nsoft7_property: %r\ndata: %r",
            error_message,
            soft7_property,
            data,
        )
        raise AttributeError(error_message)

    return __get_data


def create_datasource(
    entity: SOFT7Entity | dict[str, Any] | Path | SOFT7IdentityURIType | str,
    configs: (
        GetDataConfigDict
        | dict[str, GenericConfig | dict[str, Any] | Path | AnyUrl | FileUrl | str]
        | Path
        | AnyUrl
        | FileUrl
        | str
    ),
    oteapi_url: str | None = None,
) -> SOFT7DataSource:
    """Create and return an instance of a SOFT7 Data Source wrapped as a pydantic model.

    TODO: Utilize the `generated_classes` module and check whether we can return an
        already created model based on the inputs given here.

    TODO: Determine what to do with regards to differing inputs, but similar names.

    Parameters:
        entity: A SOFT7 entity (data model). It can be supplied as a URL reference,
            path or as a raw JSON/YAML string or Python `dict`.
        configs: A dictionary of the various required OTEAPI strategy configurations
            needed for the underlying OTEAPI pipeline. It can be supplied as a URL
            reference, path or as a raw JSON/YAML string or Python `dict`.
        oteapi_url: The base URL of the OTEAPI service to use.

    Returns:
        An instance of a SOFT7 Data Source wrapped as a pydantic data model.

    """
    import s7.factories.generated_classes as module_namespace

    entity = parse_input_entity(entity)
    configs = parse_input_configs(configs, entity_instance=entity.identity)

    # Split the identity into its parts
    namespace, version, name = parse_identity(entity.identity)

    # Setup the OTEAPI pipeline configuration
    get_piped_data = lambda: _get_data(configs, url=oteapi_url)  # noqa: E731

    # Create the dimensions model
    dimensions: dict[str, tuple[type[int], GetData]] = (
        # Value must be a (<type>, <default>) or (<type>, <FieldInfo>) tuple
        # Note, Field() returns a FieldInfo instance (but is set to return an Any type).
        {
            dimension_name: (
                int,
                Field(
                    default_factory=get_piped_data,
                    description=dimension_description,
                ),
            )
            for dimension_name, dimension_description in entity.dimensions.items()
        }
        if entity.dimensions
        else {}
    )

    DataSourceDimensionsModel = create_model(
        f"{name.replace(' ', '')}DataSourceDimensions",
        __config__=None,
        __doc__=generate_dimensions_docstring(entity),
        __base__=DataSourceDimensions,
        __module__=module_namespace.__name__,
        __validators__=None,
        __cls_kwargs__=None,
        **dimensions,
    )

    data_source_dimensions = DataSourceDimensionsModel()

    # Create the SOFT7 metadata fields for the data source model
    # All of these fields will be excluded from the data source model representation as
    # well as the serialized JSON schema or Python dictionary.
    soft7_metadata: dict[str, tuple[type | object, Any]] = {
        # Value must be a (<type>, <default>) or (<type>, <FieldInfo>) tuple
        # Note, Field() returns a FieldInfo instance (but is set to return an Any type).
        "dimensions": (
            DataSourceDimensionsModel,
            Field(data_source_dimensions, repr=False, exclude=True),
        ),
        "identity": (
            entity.model_fields["identity"].rebuild_annotation(),
            Field(entity.identity, repr=False, exclude=True),
        ),
        "namespace": (AnyUrl, Field(namespace, repr=False, exclude=True)),
        "version": (Optional[str], Field(version, repr=False, exclude=True)),
        "name": (str, Field(name, repr=False, exclude=True)),
    }

    # Pre-calculate property types
    property_types: dict[str, type[PropertyType]] = {
        property_name: generate_property_type(property_value, data_source_dimensions)
        for property_name, property_value in entity.properties.items()
    }

    # Create the data source model's properties
    properties: dict[str, tuple[type[PropertyType], GetData]] = {
        # Value must be a (<type>, <default>) or (<type>, <FieldInfo>) tuple
        # Note, Field() returns a FieldInfo instance (but is set to return an Any type).
        property_name: (
            property_types[property_name],
            Field(
                default_factory=get_piped_data,
                description=property_value.description or "",
                title=property_name.replace(" ", "_"),
                json_schema_extra={
                    f"x-soft7-{field}": getattr(property_value, field)
                    for field in property_value.model_fields
                    if (
                        field not in ("description", "type")
                        and getattr(property_value, field)
                    )
                },
            ),
        )
        for property_name, property_value in entity.properties.items()
    }

    # Ensure there is no overlap between the SOFT7 metadata fields and the data source
    # model properties and the data source model properties are not trying to hack the
    # attribute retrieval mechanism.
    if any(field.startswith("soft7___") for field in properties):
        raise ValueError(
            "The data model properties are not allowed to overwrite or mock SOFT7 "
            "metadata fields."
        )

    DataSourceModel = create_model(
        f"{name.replace(' ', '')}DataSource",
        __config__=None,
        __doc__=generate_model_docstring(entity, property_types),
        __base__=SOFT7DataSource,
        __module__=module_namespace.__name__,
        __validators__=None,
        __cls_kwargs__=None,
        **{
            # SOFT7 metadata fields
            **{f"soft7___{name}": value for name, value in soft7_metadata.items()},
            # Data source properties
            **properties,
        },
    )

    # Register the classes with the generated_classes globals
    module_namespace.register_class(DataSourceDimensionsModel)
    module_namespace.register_class(DataSourceModel)

    return DataSourceModel()  # type: ignore[call-arg]
