"""Test the datasource factory."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    import sys
    from pathlib import Path
    from typing import Any

    if sys.version_info >= (3, 10):
        from typing import Literal
    else:
        from typing_extensions import Literal

    from pytest_httpx import HTTPXMock
    from requests_mock import Mocker


pytestmark = pytest.mark.httpx_mock(can_send_already_matched_responses=True)


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
    from pydantic import AnyHttpUrl, BaseModel

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
    # identity, including the derived metadata: namespace, version, and name."
    assert (
        str(datasource.soft7___identity)
        == soft_entity_init["identity"]
        == "http://onto-ns.com/s7/0.1.0/MolecularSpecies"
    )
    assert datasource.soft7___namespace == AnyHttpUrl("http://onto-ns.com/s7")
    assert datasource.soft7___version == "0.1.0"
    assert datasource.soft7___name == "MolecularSpecies"

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
    httpx_mock: HTTPXMock,
    static_folder: Path,
) -> None:
    """Check the data source contents when serialized to a Python dict."""
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

    python_serialized = datasource.model_dump()

    assert python_serialized == soft_datasource_init["properties"]


def test_serialize_json_datasource(
    soft_entity_init: dict[str, str | dict],
    soft_datasource_init: dict[str, Any],
    soft_datasource_entity_mapping_init: dict[
        str, dict[str, str] | list[tuple[str, str, str]]
    ],
    httpx_mock: HTTPXMock,
    static_folder: Path,
) -> None:
    """Check the data source contents when serialized to JSON."""
    import json

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

    json_serialized = datasource.model_dump_json()

    assert json_serialized == json.dumps(
        soft_datasource_init["properties"], separators=(",", ":"), indent=None
    )


def test_datasource_json_schema(
    soft_entity_init: dict[str, str | dict],
    soft_datasource_entity_mapping_init: dict[
        str, dict[str, str] | list[tuple[str, str, str]]
    ],
    httpx_mock: HTTPXMock,
    static_folder: Path,
) -> None:
    """Check the generated JSON Schema for the data source."""
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
                "$ref": "#/$defs/MolecularSpeciesDataSourceDimensions",
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


def test_cacheing_model_attribute_results(
    soft_entity_init: dict[str, str | dict],
    static_folder: Path,
    soft_datasource_entity_mapping_init: dict[
        str, dict[str, str] | list[tuple[str, str, str]]
    ],
    httpx_mock: HTTPXMock,
) -> None:
    """Test the DataSource attribute results are cached in the model."""
    import json

    from s7.factories.datasource_factory import create_datasource

    # Mock SOFT7Entity identity URL
    httpx_mock.add_response(
        method="GET",
        url=soft_entity_init["identity"],
        json=soft_entity_init,
    )

    # Create the data source
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

    # Assert internal model cache is empty
    assert hasattr(datasource, "_resolved_fields")
    assert datasource._resolved_fields == {}, json.dumps(
        datasource._resolved_fields, indent=2
    )

    # Get one of the datasource's attributes and check the cache
    assert len(datasource.model_fields) > 1
    for attribute_name in datasource.model_fields:
        if attribute_name.startswith("soft7___"):
            continue
        break
    else:
        pytest.fail("No 'proper' property could be found for datasource example.")

    attribute_value = getattr(datasource, attribute_name)

    # Check the internal model cache has been populated with the attribute
    assert datasource._resolved_fields
    assert len(datasource._resolved_fields) == 1
    assert attribute_name in datasource._resolved_fields
    assert datasource._resolved_fields[attribute_name] == attribute_value


def test_pipeline_cache(
    soft_entity_init: dict[str, str | dict],
    static_folder: Path,
    soft_datasource_entity_mapping_init: dict[
        str, dict[str, str] | list[tuple[str, str, str]]
    ],
    httpx_mock: HTTPXMock,
) -> None:
    """Test the pipeline cache functions as intended."""
    import json

    from s7.factories.datasource_factory import CACHE, create_datasource

    assert CACHE == {}, json.dumps(CACHE, indent=2)

    # Mock SOFT7Entity identity URL
    httpx_mock.add_response(
        method="GET",
        url=soft_entity_init["identity"],
        json=soft_entity_init,
    )

    # Create the data source
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

    assert CACHE, json.dumps(CACHE, indent=2)
    assert len(CACHE) == 1, json.dumps(CACHE, indent=2)

    # Check the cache is working as intended
    # Get the data source from the cache
    cached_datasource = next(iter(CACHE.values()))
    assert isinstance(cached_datasource, dict)
    assert "soft7_entity_data" in cached_datasource

    # properties
    assert "properties" in cached_datasource["soft7_entity_data"]
    assert isinstance(cached_datasource["soft7_entity_data"]["properties"], dict)
    for name, value in cached_datasource["soft7_entity_data"]["properties"].items():
        assert hasattr(datasource, name)
        datasource_attribute_value = getattr(datasource, name)

        # The datasource's values will be tuple if it has a shape
        if isinstance(datasource_attribute_value, tuple):
            assert list(datasource_attribute_value) == value
        else:
            assert datasource_attribute_value == value

    # dimensions
    assert "dimensions" in cached_datasource["soft7_entity_data"]
    assert isinstance(cached_datasource["soft7_entity_data"]["dimensions"], dict)
    for name, value in cached_datasource["soft7_entity_data"]["dimensions"].items():
        assert hasattr(datasource.soft7___dimensions, name)
        datasource_dimensions_value = getattr(datasource.soft7___dimensions, name)

        assert datasource_dimensions_value == value

    # Create a new data source with the exact same configurations
    new_datasource = create_datasource(
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

    assert CACHE, json.dumps(CACHE, indent=2)
    assert len(CACHE) == 1, json.dumps(CACHE, indent=2)

    # While the pipeline data is the same, the data source instances are different
    assert new_datasource != datasource
    assert new_datasource.soft7___identity == datasource.soft7___identity

    # Create yet another new data source, but mix up the inputs, while keeping it
    # semantically the same.
    # The configs have been supplieed as a URL.
    # The URL returns the same content as for the configs above, but mixed up a bit so
    # that the key/value-pairs are mixed up a bit.

    # Mock configs
    httpx_mock.add_response(
        method="GET",
        url="http://example.org/soft7_configs",
        json={
            "dataresource": {
                "mediaType": "application/yaml",
                "downloadUrl": (
                    static_folder / "soft_datasource_content.yaml"
                ).as_uri(),
                "resourceType": "resource/url",
            },
            "mapping": {
                **soft_datasource_entity_mapping_init,
                "mappingType": "triples",
            },
            "parser": {
                "entity": soft_entity_init["identity"],
                "parserType": "parser/yaml",
            },
        },
    )

    new_new_datasource = create_datasource(
        entity=soft_entity_init,
        configs="http://example.org/soft7_configs",
        oteapi_url="python",
    )

    assert CACHE, json.dumps(CACHE, indent=2)
    assert len(CACHE) == 1, json.dumps(CACHE, indent=2)

    # While the pipeline data is the same, the data source instances are different
    assert new_new_datasource != new_datasource != datasource
    assert (
        new_new_datasource.soft7___identity
        == new_datasource.soft7___identity
        == datasource.soft7___identity
    )


def test_no_mapping_config(soft_entity_init: dict[str, str | dict]) -> None:
    """Not passing a mapping config is currently not implemented."""
    from s7.factories.datasource_factory import create_datasource

    # Create the data source
    with pytest.raises(
        NotImplementedError,
        match=r"^Only OTEAPI pipelines with a mapping are supported for now.*$",
    ):
        create_datasource(
            entity=soft_entity_init,
            configs={
                "dataresource": {
                    "resourceType": "resource/url",
                    "downloadUrl": "http://example.org/soft_datasource_content.yaml",
                    "mediaType": "application/yaml",
                },
                "parser": {
                    "parserType": "parser/yaml",
                    "entity": soft_entity_init["identity"],
                },
            },
            oteapi_url="python",
        )


def test_bad_pipeline_response(
    soft_entity_init: dict[str, str | dict],
    soft_datasource_init: dict[str, Any],
    soft_datasource_entity_mapping_init: dict[
        str, dict[str, str] | list[tuple[str, str, str]]
    ],
    requests_mock: Mocker,
    httpx_mock: HTTPXMock,
    static_folder: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test an error is raised if the pipeline response is not as expected.

    Need to go the route of mocking an OTEAPI Service, not using `python`, as this
    is the easiest way to mock a bad pipeline response.
    """
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

    # Change the key of the 'function_get_content' to simulate a bad response
    assert "soft7_entity_data" in function_get_content
    function_get_content["wrong_key"] = function_get_content.pop("soft7_entity_data")
    assert "soft7_entity_data" not in function_get_content

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

    # Create the data source
    # As it is now, the pipeline will be run to retrieve the dimensions for property
    # creation.
    # Hence, the error will be raised already during creation in the
    # `generate_property_type()` function. Here, the error will be caught and re-raised
    # as another ValueError.
    # Note, there is only one dimension (`N`).
    with pytest.raises(
        ValueError,
        match=(
            r"^.*Dimension 'N' is not defined in the data model or cannot be "
            r"resolved\.$"
        ),
    ):
        create_datasource(
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
        )

    # This is the "original" error, reported in the log through the custom
    # `__getattribute__()` method as well as through the "internal" `_get_data()`
    # method.
    original_error_message = (
        "The OTEAPI pipeline did not return the expected data structure."
    )
    assert original_error_message in caplog.text
    assert caplog.text.count(original_error_message) == 2
    assert f"ValueError: {original_error_message}" in caplog.text
    assert "An error occurred during attribute resolution:" in caplog.text


def test_get_nonexisting_property(
    soft_entity_init: dict[str, str | dict],
    static_folder: Path,
    soft_datasource_init: dict[str, Any],
    soft_datasource_entity_mapping_init: dict[
        str, dict[str, str] | list[tuple[str, str, str]]
    ],
    requests_mock: Mocker,
    httpx_mock: HTTPXMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test an error is raised when trying to get a non-existing property.

    Test an error is raised when trying to get a property that cannot be resolved.
    """
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

    # Change the content, removing a property to simulate a bad response
    missing_property = function_get_content["soft7_entity_data"]["properties"].popitem()
    # Ensure there are still properties
    assert function_get_content["soft7_entity_data"]["properties"]

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

    # Create the data source
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
    )

    # Try to get a non-existing property
    assert "non_existing_property" not in datasource.model_fields
    with pytest.raises(
        AttributeError,
        match=(
            rf"^{datasource.__class__.__name__!r} object has no attribute "
            r"'non_existing_property'$"
        ),
    ):
        datasource.non_existing_property

    # Try getting a "bad" property that cannot be resolved.
    with pytest.raises(
        AttributeError,
        match=(
            rf"^{datasource.__class__.__name__!r} object has no attribute "
            rf"{missing_property[0]!r}$"
        ),
    ):
        getattr(datasource, missing_property[0])

    # Check the error is logged
    # This is the "original" error, reported in the log through the custom
    # `__getattribute__()` method as well as through the "internal" `_get_data()`
    # method.
    original_error_message = (
        f"{missing_property[0]!r} could not be determined for the resource."
    )
    assert original_error_message in caplog.text
    assert caplog.text.count(original_error_message) == 2
    assert f"AttributeError: {original_error_message}" in caplog.text
    assert "An error occurred during attribute resolution:" in caplog.text


@pytest.mark.parametrize(
    "metadata_field",
    ["soft7___non_existing", "soft7___name"],
    ids=["non_existing", "overwrite"],
)
def test_try_to_overwrite_metadata_fields(
    soft_entity_init: dict[str, str | dict],
    static_folder: Path,
    soft_datasource_entity_mapping_init: dict[
        str, dict[str, str] | list[tuple[str, str, str]]
    ],
    httpx_mock: HTTPXMock,
    tmp_path: Path,
    metadata_field: Literal["soft7___non_existing", "soft7___name"],
) -> None:
    """Ensure an error is raised if the entity contains special metadata fields used
    for the DataSource model generation."""
    import yaml

    from s7.factories.datasource_factory import create_datasource

    # Add a metadata field to the entity
    soft_entity_init["properties"][metadata_field] = {
        "type": "string",
        "description": (
            "Metadata field that should not be overwritten."
            if metadata_field == "soft7___non_existing"
            else "Metadata field that intends to overwrite an existing metadata field."
        ),
    }
    # Extend mapping
    soft_datasource_entity_mapping_init["triples"].append(
        (
            f"data_source:properties.{metadata_field}",
            "",
            f"s7_entity:properties.{metadata_field}",
        )
    )
    # Extend data source content
    soft_datasource_content: dict[str, Any] = yaml.safe_load(
        (static_folder / "soft_datasource_content.yaml").read_text()
    )
    assert "properties" in soft_datasource_content
    soft_datasource_content["properties"][metadata_field] = "test"

    # Write the modified data source content to a temporary file
    modified_datasource_content_path = tmp_path / "soft_datasource_content.yaml"
    modified_datasource_content_path.write_text(yaml.safe_dump(soft_datasource_content))

    # Mock SOFT7Entity identity URL
    httpx_mock.add_response(
        method="GET",
        url=soft_entity_init["identity"],
        json=soft_entity_init,
    )

    # Create the data source
    with pytest.raises(
        ValueError,
        match=(
            r"^The data model properties are not allowed to overwrite or mock SOFT7 "
            r"metadata fields\.$"
        ),
    ):
        create_datasource(
            entity=soft_entity_init,
            configs={
                "dataresource": {
                    "resourceType": "resource/url",
                    "downloadUrl": modified_datasource_content_path.as_uri(),
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
