"""Test the datasource factory."""
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from typing import Any, Union

    from requests_mock import Mocker


def test_create_datasource(
    soft_entity_init: "dict[str, Union[str, dict]]",
    soft_datasource_init: "dict[str, Any]",
    generic_resource_config: "dict[str, Union[str, dict]]",
    requests_mock: "Mocker",
) -> None:
    """Test a straight forward call to create_datasource()."""
    import json

    from otelib.settings import Settings

    from s7.factories.datasource_factory import create_datasource

    default_oteapi_url = "http://localhost:8080"
    rest_api_prefix = Settings().prefix

    oteapi_url = f"{default_oteapi_url}{rest_api_prefix}"

    # Creating the data resource
    requests_mock.post(
        f"{oteapi_url}/dataresource",
        json={"resource_id": "1234"},
    )

    # Getting the data resource
    # Create session
    requests_mock.post(
        f"{oteapi_url}/session",
        text=json.dumps({"session_id": "1234"}),
    )

    # Initialize
    requests_mock.post(
        f"{oteapi_url}/dataresource/1234/initialize",
        content=json.dumps({}).encode(encoding="utf-8"),
    )

    # Fetch
    requests_mock.get(
        f"{oteapi_url}/dataresource/1234",
        content=json.dumps(soft_datasource_init).encode(encoding="utf-8"),
    )

    create_datasource(entity=soft_entity_init, resource_config=generic_resource_config)


@pytest.mark.usefixtures("load_test_strategies")
def test_inspect_created_datasource(
    soft_entity_init: "dict[str, Union[str, dict]]",
    generic_resource_config: "dict[str, Union[str, dict]]",
    soft_datasource_init: "dict[str, Any]",
) -> None:
    """Test the generated data source contains the expected attributes and metadata."""
    from pydantic import AnyUrl, BaseModel

    from s7.factories.datasource_factory import create_datasource

    datasource = create_datasource(
        entity=soft_entity_init,
        resource_config=generic_resource_config,
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
        == """temperature

    A bare-bones entity for testing.

    SOFT7 Entity Metadata:
        Identity: https://onto-ns.com/s7/0.1.0/temperature

        Namespace: https://onto-ns.com/s7
        Version: 0.1.0
        Name: temperature

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

        assert (
            getattr(datasource, field_name)
            == soft_datasource_init["properties"][field_name]
        ), (
            f"{field_name} is not correctly resolved, it is "
            f"{getattr(datasource, field_name)} and should be "
            f"{soft_datasource_init['properties'][field_name]}."
        )

    ## Check the data source's metadata is correctly resolved
    checked_metadata_names = set()

    # identity, including the derived metadata: namespace, version, and name."
    assert (
        str(datasource.soft7___identity)
        == soft_entity_init["identity"]
        == "https://onto-ns.com/s7/0.1.0/temperature"
    )
    assert datasource.soft7___namespace == AnyUrl("https://onto-ns.com/s7")
    assert datasource.soft7___version == "0.1.0"
    assert datasource.soft7___name == "temperature"
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
        == """temperatureDimensions

    Dimensions for the temperature SOFT7 data source.

    SOFT7 Entity: https://onto-ns.com/s7/0.1.0/temperature

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


@pytest.mark.usefixtures("load_test_strategies")
def test_serialize_python_datasource(
    soft_entity_init: "dict[str, Union[str, dict]]",
    soft_datasource_init: "dict[str, Any]",
    generic_resource_config: "dict[str, Union[str, dict]]",
) -> None:
    """Check the data source contents when serialized to a Python dict."""
    from s7.factories.datasource_factory import create_datasource

    datasource = create_datasource(
        entity=soft_entity_init,
        resource_config=generic_resource_config,
        oteapi_url="python",
    )

    python_serialized = datasource.model_dump()

    assert python_serialized == soft_datasource_init["properties"]


@pytest.mark.usefixtures("load_test_strategies")
def test_serialize_json_datasource(
    soft_entity_init: "dict[str, Union[str, dict]]",
    soft_datasource_init: "dict[str, Any]",
    generic_resource_config: "dict[str, Union[str, dict]]",
) -> None:
    """Check the data source contents when serialized to JSON."""
    import json

    from s7.factories.datasource_factory import create_datasource

    datasource = create_datasource(
        entity=soft_entity_init,
        resource_config=generic_resource_config,
        oteapi_url="python",
    )

    json_serialized = datasource.model_dump_json()

    assert json_serialized == json.dumps(
        soft_datasource_init["properties"], separators=(",", ":"), indent=None
    )


@pytest.mark.usefixtures("load_test_strategies")
def test_datasource_json_schema(
    soft_entity_init: "dict[str, Union[str, dict]]",
    generic_resource_config: "dict[str, Union[str, dict]]",
) -> None:
    """Check the generated JSON Schema for the data source."""
    from s7.factories.datasource_factory import create_datasource

    datasource = create_datasource(
        entity=soft_entity_init,
        resource_config=generic_resource_config,
        oteapi_url="python",
    )

    json_schema = datasource.model_json_schema()

    assert json_schema == {
        "title": "temperature",
        "description": """temperature

A bare-bones entity for testing.

SOFT7 Entity Metadata:
    Identity: https://onto-ns.com/s7/0.1.0/temperature

    Namespace: https://onto-ns.com/s7
    Version: 0.1.0
    Name: temperature

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
                "allOf": [{"$ref": "#/$defs/temperatureDimensions"}],
                "default": {"N": 5},
            },
            "soft7___identity": {
                "title": "Soft7   Identity",
                "type": "string",
                "format": "uri",
                "minLength": 1,
                "default": "https://onto-ns.com/s7/0.1.0/temperature",
            },
            "soft7___namespace": {
                "title": "Soft7   Namespace",
                "type": "string",
                "format": "uri",
                "minLength": 1,
                "default": "https://onto-ns.com/s7",
            },
            "soft7___version": {
                "title": "Soft7   Version",
                "default": "0.1.0",
                "anyOf": [{"type": "string"}, {"type": "null"}],
            },
            "soft7___name": {
                "title": "Soft7   Name",
                "default": "temperature",
                "type": "string",
            },
        },
        "$defs": {
            "temperatureDimensions": {
                "title": "temperatureDimensions",
                "description": """temperatureDimensions

Dimensions for the temperature SOFT7 data source.

SOFT7 Entity: https://onto-ns.com/s7/0.1.0/temperature

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
