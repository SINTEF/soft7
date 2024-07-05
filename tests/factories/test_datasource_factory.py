"""Test the datasource factory."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any

    from pytest_httpx import HTTPXMock
    from requests_mock import Mocker


def test_create_datasource(
    soft_entity_init: dict[str, str | dict],
    soft_datasource_init: dict[str, Any],
    soft_datasource_entity_mapping_init: dict[
        str, dict[str, str] | list[tuple[str, str, str]]
    ],
    requests_mock: Mocker,
    httpx_mock: HTTPXMock,
    static_folder: Path,
) -> None:
    """Test a straight forward call to create_datasource()."""
    import json

    from otelib.settings import Settings

    from s7.factories.datasource_factory import create_datasource
    from s7.oteapi_plugin.soft7_function import SOFT7Generator

    default_oteapi_url = "http://localhost:8080"
    rest_api_prefix = Settings().prefix

    oteapi_url = f"{default_oteapi_url}{rest_api_prefix}"

    # Mock SOFT7Entity identity URL
    httpx_mock.add_response(
        method="GET",
        url=soft_entity_init["identity"],
        json=soft_entity_init,
    )

    # Run SOFT7Generator
    # Mock the session data content for the
    # pipeline = dataresource >> mapping >> function
    session_data = {}
    session_data.update(soft_datasource_entity_mapping_init)
    session_data.update({"content": soft_datasource_init})
    generator_configuration = {"entity": soft_entity_init["identity"]}
    function_get_content = SOFT7Generator(
        function_config={
            "functionType": "SOFT7",
            "configuration": {**session_data, **generator_configuration},
        }
    ).get()

    # Creating strategies
    # The data resource
    requests_mock.post(
        f"{oteapi_url}/dataresource",
        json={"resource_id": "1234"},
    )

    # The parser resource
    requests_mock.post(
        f"{oteapi_url}/parser",
        json={"parser_id": "1234"},
    )

    # The mapping
    requests_mock.post(
        f"{oteapi_url}/mapping",
        json={"mapping_id": "1234"},
    )

    # The function
    requests_mock.post(
        f"{oteapi_url}/function",
        json={"function_id": "1234"},
    )

    # Getting the OTE pipeline = dataresource >> mapping >> function
    # Create session
    requests_mock.post(
        f"{oteapi_url}/session",
        text=json.dumps({"session_id": "1234"}),
    )

    # Initialize
    requests_mock.post(
        f"{oteapi_url}/function/1234/initialize",
        content=json.dumps({}).encode(encoding="utf-8"),
    )
    requests_mock.post(
        f"{oteapi_url}/mapping/1234/initialize",
        content=json.dumps(soft_datasource_entity_mapping_init).encode(
            encoding="utf-8"
        ),
    )
    requests_mock.post(
        f"{oteapi_url}/parser/1234/initialize",
        content=json.dumps({}).encode(encoding="utf-8"),
    )
    requests_mock.post(
        f"{oteapi_url}/dataresource/1234/initialize",
        content=json.dumps({}).encode(encoding="utf-8"),
    )

    # Fetch
    requests_mock.get(
        f"{oteapi_url}/dataresource/1234",
        content=json.dumps({"key": "test"}).encode(encoding="utf-8"),
    )
    requests_mock.get(
        f"{oteapi_url}/parser/1234",
        content=json.dumps({"content": soft_datasource_init}).encode(encoding="utf-8"),
    )
    requests_mock.get(
        f"{oteapi_url}/mapping/1234",
        content=json.dumps({}).encode(encoding="utf-8"),
    )
    requests_mock.get(
        f"{oteapi_url}/function/1234",
        content=function_get_content.model_dump_json().encode(encoding="utf-8"),
    )

    create_datasource(
        entity=soft_entity_init["identity"],
        configs={
            "dataresource": {
                "resourceType": "resource/url",
                "downloadUrl": (
                    static_folder / "soft_datasource_content.yaml"
                ).as_uri(),
                "mediaType": "application/yaml",
            },
            "parser": {
                "parserType": "parser/yaml",
                "entity": soft_entity_init["identity"],
            },
            "mapping": {
                "mappingType": "triples",
                **soft_datasource_entity_mapping_init,
            },
        },
    )


def test_inspect_created_datasource(
    soft_entity_init: dict[str, str | dict],
    static_folder: Path,
    soft_datasource_init: dict[str, Any],
    soft_datasource_entity_mapping_init: dict[
        str, dict[str, str] | list[tuple[str, str, str]]
    ],
    httpx_mock: HTTPXMock,
) -> None:
    """Test the generated data source contains the expected attributes and metadata."""
    from pydantic import AnyUrl, BaseModel

    from s7.factories.datasource_factory import create_datasource

    # Mock SOFT7Entity identity URL
    httpx_mock.add_response(
        method="GET",
        url=soft_entity_init["identity"],
        json=soft_entity_init,
    )

    datasource = create_datasource(
        entity=soft_entity_init,
        configs={
            "dataresource": {
                "resourceType": "resource/url",
                "downloadUrl": (
                    static_folder / "soft_datasource_content.yaml"
                ).as_uri(),
                "mediaType": "application/yaml",
            },
            "parser": {
                "parserType": "parser/yaml",
                "entity": soft_entity_init["identity"],
            },
            "mapping": {
                "mappingType": "triples",
                **soft_datasource_entity_mapping_init,
            },
        },
        oteapi_url="python",
    )

    ## Check the special attributes set on the class are what we expect
    # doc-string
    # Checked against the `soft_entity_init`'s values - check the fixture for
    # confirmation that the content here matches the fixture.
    # The type of the properties are derived from the `soft_datasource_init` fixture,
    # in the sense of dimensionality.
    assert (
        datasource.__doc__
        == """MolecularSpecies

    A bare-bones entity for testing.

    SOFT7 Entity Metadata:
        Identity: http://onto-ns.com/s7/0.1.0/MolecularSpecies

        Namespace: http://onto-ns.com/s7
        Version: 0.1.0
        Name: MolecularSpecies

    Dimensions:
        N (int): Number of elements.

    Attributes:
        atom (tuple[str, str, str, str, str]): An atom.
        electrons (tuple[int, int, int, int, int]): Number of electrons.
        mass (tuple[float, float, float, float, float]): Atomic mass.
        radius (tuple[float, float, float, float, float]): Atomic radius.

    """
    )

    ## Check the data source's attribute values are currently (lambda) functions
    # Get the data source's representation
    datasource_repr = repr(datasource)

    # Remove the class name and the surrounding parentheses
    datasource_repr_fields = datasource_repr[
        len(datasource.__class__.__name__) + 1 : -1
    ]

    for field in datasource_repr_fields.split(", "):
        field_name, field_value = field.split("=", maxsplit=1)
        assert field_value.startswith("<function _get_data.<locals>.__get_data at"), (
            f"{field_name} is not a lambda function of "
            "`s7.factories.datasource_factory._get_data` and its inner function "
            f"`__get_data`, it is a {field_value}."
        )

    ## Check the data source's data is correctly resolved
    for field_name in datasource.model_fields:
        if field_name.startswith("soft7___"):
            # Avoid checking metadata
            continue

        datasource_value = getattr(datasource, field_name)

        assert datasource_value == soft_datasource_init["properties"][field_name], (
            f"{field_name} is not correctly resolved, it is {datasource_value} and "
            f"should be {soft_datasource_init['properties'][field_name]}."
        )

    ## Check the data source's metadata is correctly resolved
    checked_metadata_names = set()

    # identity, including the derived metadata: namespace, version, and name."
    assert (
        str(datasource.soft7___identity)
        == soft_entity_init["identity"]
        == "http://onto-ns.com/s7/0.1.0/MolecularSpecies"
    )
    assert datasource.soft7___namespace == AnyUrl("http://onto-ns.com/s7")
    assert datasource.soft7___version == "0.1.0"
    assert datasource.soft7___name == "MolecularSpecies"
    checked_metadata_names.update({"identity", "namespace", "version", "name"})

    # dimensions
    assert isinstance(datasource.soft7___dimensions, BaseModel)

    dimensions_metadata = datasource.soft7___dimensions

    # doc-string
    # Checked against the `soft_entity_init`'s values - check the fixture for
    # confirmation that the content here matches the fixture.
    # The type of the dimensions is always `int`.
    assert (
        dimensions_metadata.__doc__
        == """MolecularSpeciesDimensions

    Dimensions for the MolecularSpecies SOFT7 data source.

    SOFT7 Entity: http://onto-ns.com/s7/0.1.0/MolecularSpecies

    Attributes:
        N (int): Number of elements.

    """
    )
    # Check the dimensions values are currently (lambda) functions
    # Get the dimensions' representation
    dimensions_repr = repr(dimensions_metadata)

    # Remove the class name and the surrounding parentheses
    dimensions_repr_fields = dimensions_repr[
        len(dimensions_metadata.__class__.__name__) + 1 : -1
    ]

    for field in dimensions_repr_fields.split(", "):
        dimension_name, dimension_value = field.split("=", maxsplit=1)
        assert dimension_value.startswith(
            "<function _get_data.<locals>.__get_data at"
        ), (
            f"{dimension_name} is not a lambda function of "
            "`s7.factories.datasource_factory._get_data` and its inner function "
            f"`__get_data`, it is a {dimension_value}."
        )

    # Check there are no excluded fields
    assert len(dimensions_repr_fields.split(", ")) == len(
        dimensions_metadata.model_fields
    )

    # Check the dimensions are correctly resolved
    for dimension_name in dimensions_metadata.model_fields:
        assert (
            getattr(dimensions_metadata, dimension_name)
            == soft_datasource_init["dimensions"][dimension_name]
        ), (
            f"{dimension_name} is not correctly resolved, it is "
            f"{getattr(dimensions_metadata, dimension_name)} and should be "
            f"{soft_datasource_init['dimensions'][dimension_name]}."
        )


def test_serialize_python_datasource(
    soft_entity_init: dict[str, str | dict],
    soft_datasource_init: dict[str, Any],
    soft_datasource_entity_mapping_init: dict[
        str, dict[str, str] | list[tuple[str, str, str]]
    ],
    static_folder: Path,
) -> None:
    """Check the data source contents when serialized to a Python dict."""
    from s7.factories.datasource_factory import create_datasource

    datasource = create_datasource(
        entity=soft_entity_init,
        configs={
            "dataresource": {
                "resourceType": "resource/url",
                "downloadUrl": (
                    static_folder / "soft_datasource_content.yaml"
                ).as_uri(),
                "mediaType": "application/yaml",
            },
            "parser": {
                "parserType": "parser/yaml",
                "entity": soft_entity_init["identity"],
            },
            "mapping": {
                "mappingType": "triples",
                **soft_datasource_entity_mapping_init,
            },
        },
        oteapi_url="python",
    )

    python_serialized = datasource.model_dump()

    assert python_serialized == soft_datasource_init["properties"]


def test_serialize_json_datasource(
    soft_entity_init: dict[str, str | dict],
    soft_datasource_init: dict[str, Any],
    soft_datasource_entity_mapping_init: dict[
        str, dict[str, str] | list[tuple[str, str, str]]
    ],
    static_folder: Path,
) -> None:
    """Check the data source contents when serialized to JSON."""
    import json

    from s7.factories.datasource_factory import create_datasource

    datasource = create_datasource(
        entity=soft_entity_init,
        configs={
            "dataresource": {
                "resourceType": "resource/url",
                "downloadUrl": (
                    static_folder / "soft_datasource_content.yaml"
                ).as_uri(),
                "mediaType": "application/yaml",
            },
            "parser": {
                "parserType": "parser/yaml",
                "entity": soft_entity_init["identity"],
            },
            "mapping": {
                "mappingType": "triples",
                **soft_datasource_entity_mapping_init,
            },
        },
        oteapi_url="python",
    )

    json_serialized = datasource.model_dump_json()

    assert json_serialized == json.dumps(
        soft_datasource_init["properties"], separators=(",", ":"), indent=None
    )


def test_datasource_json_schema(
    soft_entity_init: dict[str, str | dict],
    soft_datasource_entity_mapping_init: dict[
        str, dict[str, str] | list[tuple[str, str, str]]
    ],
    static_folder: Path,
) -> None:
    """Check the generated JSON Schema for the data source."""
    from s7.factories.datasource_factory import create_datasource

    datasource = create_datasource(
        entity=soft_entity_init,
        configs={
            "dataresource": {
                "resourceType": "resource/url",
                "downloadUrl": (
                    static_folder / "soft_datasource_content.yaml"
                ).as_uri(),
                "mediaType": "application/yaml",
            },
            "parser": {
                "parserType": "parser/yaml",
                "entity": soft_entity_init["identity"],
            },
            "mapping": {
                "mappingType": "triples",
                **soft_datasource_entity_mapping_init,
            },
        },
        oteapi_url="python",
    )

    json_schema = datasource.model_json_schema()

    assert json_schema == {
        "title": "MolecularSpeciesDataSource",
        "description": """MolecularSpecies

A bare-bones entity for testing.

SOFT7 Entity Metadata:
    Identity: http://onto-ns.com/s7/0.1.0/MolecularSpecies

    Namespace: http://onto-ns.com/s7
    Version: 0.1.0
    Name: MolecularSpecies

Dimensions:
    N (int): Number of elements.

Attributes:
    atom (tuple[str, str, str, str, str]): An atom.
    electrons (tuple[int, int, int, int, int]): Number of electrons.
    mass (tuple[float, float, float, float, float]): Atomic mass.
    radius (tuple[float, float, float, float, float]): Atomic radius.""",
        "type": "object",
        "properties": {
            "atom": {
                "title": "atom",
                "type": "array",
                "minItems": 5,
                "maxItems": 5,
                "prefixItems": [
                    {"type": "string"},
                    {"type": "string"},
                    {"type": "string"},
                    {"type": "string"},
                    {"type": "string"},
                ],
                "description": "An atom.",
                "x-soft7-shape": ["N"],
            },
            "electrons": {
                "title": "electrons",
                "type": "array",
                "minItems": 5,
                "maxItems": 5,
                "prefixItems": [
                    {"type": "integer"},
                    {"type": "integer"},
                    {"type": "integer"},
                    {"type": "integer"},
                    {"type": "integer"},
                ],
                "description": "Number of electrons.",
                "x-soft7-shape": ["N"],
            },
            "mass": {
                "title": "mass",
                "type": "array",
                "minItems": 5,
                "maxItems": 5,
                "prefixItems": [
                    {"type": "number"},
                    {"type": "number"},
                    {"type": "number"},
                    {"type": "number"},
                    {"type": "number"},
                ],
                "description": "Atomic mass.",
                "x-soft7-shape": ["N"],
                "x-soft7-unit": "amu",
            },
            "radius": {
                "title": "radius",
                "type": "array",
                "minItems": 5,
                "maxItems": 5,
                "prefixItems": [
                    {"type": "number"},
                    {"type": "number"},
                    {"type": "number"},
                    {"type": "number"},
                    {"type": "number"},
                ],
                "description": "Atomic radius.",
                "x-soft7-shape": ["N"],
                "x-soft7-unit": "Å",
            },
            "soft7___dimensions": {
                "allOf": [{"$ref": "#/$defs/MolecularSpeciesDataSourceDimensions"}],
                "default": {"N": 5},
            },
            "soft7___identity": {
                "title": "Soft7   Identity",
                "type": "string",
                "format": "uri",
                "minLength": 1,
                "default": "http://onto-ns.com/s7/0.1.0/MolecularSpecies",
            },
            "soft7___namespace": {
                "title": "Soft7   Namespace",
                "type": "string",
                "format": "uri",
                "minLength": 1,
                "default": "http://onto-ns.com/s7",
            },
            "soft7___version": {
                "title": "Soft7   Version",
                "default": "0.1.0",
                "anyOf": [{"type": "string"}, {"type": "null"}],
            },
            "soft7___name": {
                "title": "Soft7   Name",
                "default": "MolecularSpecies",
                "type": "string",
            },
        },
        "$defs": {
            "MolecularSpeciesDataSourceDimensions": {
                "title": "MolecularSpeciesDataSourceDimensions",
                "description": """MolecularSpeciesDimensions

Dimensions for the MolecularSpecies SOFT7 data source.

SOFT7 Entity: http://onto-ns.com/s7/0.1.0/MolecularSpecies

Attributes:
    N (int): Number of elements.""",
                "type": "object",
                "properties": {
                    "N": {
                        "title": "N",
                        "description": "Number of elements.",
                        "type": "integer",
                    }
                },
                "additionalProperties": False,
            }
        },
        "additionalProperties": False,
    }


def test_cacheing_pipeline_results(
    soft_entity_init: dict[str, str | dict],
    static_folder: Path,
    soft_datasource_entity_mapping_init: dict[
        str, dict[str, str] | list[tuple[str, str, str]]
    ],
    httpx_mock: HTTPXMock,
) -> None:
    """Test the OTEAPI pipeline results are cached."""
    from copy import deepcopy

    from s7.factories.datasource_factory import CACHE, create_datasource

    # Mock SOFT7Entity identity URL
    httpx_mock.add_response(
        method="GET",
        url=soft_entity_init["identity"],
        json=soft_entity_init,
    )

    datasource = create_datasource(
        entity=soft_entity_init,
        configs={
            "dataresource": {
                "resourceType": "resource/url",
                "downloadUrl": (
                    static_folder / "soft_datasource_content.yaml"
                ).as_uri(),
                "mediaType": "application/yaml",
            },
            "parser": {
                "parserType": "parser/yaml",
                "entity": soft_entity_init["identity"],
            },
            "mapping": {
                "mappingType": "triples",
                **soft_datasource_entity_mapping_init,
            },
        },
        oteapi_url="python",
    )

    # Check the cache is currently empty
    assert len(CACHE) == 1
    org_CACHE = deepcopy(CACHE)
    pipeline_cache_key = next(iter(org_CACHE))

    # Get one of the datasource's attributes and check the cache
    assert len(datasource.model_fields) > 1
    for attribute_name in datasource.model_fields:
        if attribute_name.startswith("soft7___"):
            continue
        break
    else:
        pytest.fail("No 'proper' property could be found for datasource example.")

    attribute_value = getattr(datasource, attribute_name)
    # Everything will be tuple's in the datasource model (if there are multiple values)
    # The type stored in the CACHE will be lists, as this will come from a JSON/YAML
    # source (ideally)
    if isinstance(attribute_value, tuple):
        attribute_value = list(attribute_value)

    assert org_CACHE == CACHE
    assert len(CACHE) == 1
    assert next(iter(CACHE)) == pipeline_cache_key
    assert (
        next(iter(CACHE.values()))["soft7_entity_data"]["properties"][attribute_name]
        == attribute_value
    )
    for attribute_name in next(iter(CACHE.values()))["soft7_entity_data"]["properties"]:
        assert not attribute_name.startswith("soft7___")
