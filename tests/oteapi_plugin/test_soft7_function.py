"""Test the soft7 OTEAPI function strategy."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any

    from pydantic import AnyUrl
    from pytest_httpx import HTTPXMock

    from s7.pydantic_models.soft7_entity import SOFT7Entity
    from s7.pydantic_models.soft7_instance import SOFT7EntityInstance


def test__flatten_mapping() -> None:
    """Test the `_flatten_mapping()` method."""
    from oteapi.strategies.mapping.mapping import MappingSessionUpdate, MappingStrategy
    from pydantic import AnyUrl

    from s7.oteapi_plugin.soft7_function import RDFTriple, SOFT7Generator
    from s7.pydantic_models.oteapi import default_soft7_ote_function_config

    # Test with a simple mapping
    mapping_strategy = MappingStrategy(
        mapping_config={
            "mappingType": "triples",
            "prefixes": {
                "optimade": "https://optimade.materialsproject.org/v1/structures/mp-1228448#",
                "soft7": "http://onto-ns.com/meta/1.0/OPTIMADEStructure#",
            },
            "triples": {
                ("optimade:data.id", "", "soft7:properties.id"),
                ("optimade:data.type", "", "soft7:properties.type"),
                ("optimade:data.attributes", "", "soft7:properties.attributes"),
            },
        }
    )
    generator = SOFT7Generator(
        function_config=default_soft7_ote_function_config(
            "http://onto-ns.com/meta/1.0/OPTIMADEStructure"
        ).model_dump()
    )

    # Mock run the pipeline: mapping_strategy >> generator
    # BUT run only up to the point before running `get()` on generator.
    session = generator.initialize(session={})
    session.update(mapping_strategy.initialize(session=session))
    session.update(mapping_strategy.get(session=session))

    # Parse into a MappingSessionUpdate
    session = MappingSessionUpdate(**session)

    # Test the `_flatten_mapping()` method
    flat_mapping = generator._flatten_mapping(session)

    assert isinstance(flat_mapping, list)
    assert len(flat_mapping) == len(mapping_strategy.mapping_config.triples)

    expected_flat_mapping = [
        RDFTriple(*_)
        for _ in [
            (
                {
                    "namespace": AnyUrl(
                        mapping_strategy.mapping_config.prefixes["optimade"].rstrip("#")
                    ),
                    "concept": "data.id",
                },
                {"namespace": "", "concept": ""},
                {
                    "namespace": AnyUrl(
                        mapping_strategy.mapping_config.prefixes["soft7"].rstrip("#")
                    ),
                    "concept": "properties.id",
                },
            ),
            (
                {
                    "namespace": AnyUrl(
                        mapping_strategy.mapping_config.prefixes["optimade"].rstrip("#")
                    ),
                    "concept": "data.type",
                },
                {"namespace": "", "concept": ""},
                {
                    "namespace": AnyUrl(
                        mapping_strategy.mapping_config.prefixes["soft7"].rstrip("#")
                    ),
                    "concept": "properties.type",
                },
            ),
            (
                {
                    "namespace": AnyUrl(
                        mapping_strategy.mapping_config.prefixes["optimade"].rstrip("#")
                    ),
                    "concept": "data.attributes",
                },
                {"namespace": "", "concept": ""},
                {
                    "namespace": AnyUrl(
                        mapping_strategy.mapping_config.prefixes["soft7"].rstrip("#")
                    ),
                    "concept": "properties.attributes",
                },
            ),
        ]
    ]

    for mapping in flat_mapping:
        assert mapping in expected_flat_mapping
        expected_flat_mapping.remove(mapping)

    assert not expected_flat_mapping


def _generate_entity_test_cases() -> tuple[
    list[str],
    list[
        str,
        AnyUrl,
        SOFT7Entity,
        str,
        dict[str, Any],
        Path,
        type[SOFT7EntityInstance],
    ],
]:
    """Generate test cases for the `test_dataclass_validation()` test."""
    import yaml
    from pydantic import AnyUrl

    from s7.factories.entity_factory import create_entity_instance
    from s7.pydantic_models.soft7_entity import SOFT7Entity
    from tests.conftest import static_folder

    test_data_entity_path = static_folder() / "soft_datasource_entity.yaml"
    test_data_entity = yaml.safe_load(test_data_entity_path.read_text(encoding="utf-8"))
    test_entity = SOFT7Entity(**test_data_entity)

    test_cases = [
        # identity as a string
        test_data_entity["identity"],
        # identity as a URL
        AnyUrl(test_data_entity["identity"]),
        # Entity as a SOFT7Entity instance
        test_entity,
        # Entity as a JSON-serialized string
        test_entity.model_dump_json(exclude_unset=True),
        # Entity as a dict
        test_data_entity,
        # Path to a YAML file containing the Entity
        test_data_entity_path,
        # Entity as a SOFT7EntityInstance class
        create_entity_instance(test_entity),
    ]
    return ["identity", "url", "instance", "json", "dict", "path", "class"], test_cases


@pytest.mark.parametrize("functionType", ["soft7", "SOFT7"])
@pytest.mark.parametrize(
    "entity", _generate_entity_test_cases()[1], ids=_generate_entity_test_cases()[0]
)
def test_dataclass_validation(
    functionType: str,
    entity: (
        str | type[SOFT7EntityInstance] | dict[str, Any] | Path | AnyUrl | SOFT7Entity
    ),
    httpx_mock: HTTPXMock,
    soft_entity_init: dict[str, str | dict],
) -> None:
    """Check the dataclass instantiates correctly (and validates) with different input
    types."""
    from pydantic import AnyUrl, ValidationError

    from s7.oteapi_plugin.soft7_function import SOFT7Generator
    from s7.pydantic_models.soft7_entity import SOFT7IdentityURI

    if isinstance(entity, (str, AnyUrl)):
        try:
            SOFT7IdentityURI(str(entity))
        except ValidationError:
            pass
        else:
            # This is a valid SOFT7IdentityURI.
            # Setup a mock URL response.
            httpx_mock.add_response(
                url=str(entity),
                method="GET",
                json=soft_entity_init,
            )

    # Instantiate the dataclass with the dynamically generated config
    SOFT7Generator(
        function_config={
            "functionType": functionType,
            "configuration": {
                "entity": entity,
            },
        }
    )
