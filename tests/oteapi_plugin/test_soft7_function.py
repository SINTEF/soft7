"""Test the soft7 OTEAPI function strategy."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any, Union

    from pydantic import AnyHttpUrl
    from pytest_httpx import HTTPXMock

    from s7.pydantic_models.soft7_entity import SOFT7Entity
    from s7.pydantic_models.soft7_instance import SOFT7EntityInstance

pytestmark = pytest.mark.httpx_mock(can_send_already_matched_responses=True)


def test__flatten_mapping(httpx_mock: HTTPXMock, static_folder: Path) -> None:
    """Test the `_flatten_mapping()` method."""
    import json

    from oteapi.models import AttrDict, MappingConfig
    from oteapi.strategies.mapping.mapping import MappingStrategy
    from pydantic import AnyHttpUrl

    from s7.oteapi_plugin.soft7_function import RDFTriple, SOFT7Generator
    from s7.pydantic_models.oteapi import default_soft7_ote_function_config

    # Mock the external URL calls
    # Data source
    # httpx_mock.add_response(
    #     url="https://optimade.materialsproject.org/v1/structures/mp-1228448",
    #     method="GET",
    #     json=json.loads(
    #         (static_folder / "optimade.materialsproject_mp-1228448.json").read_text()
    #     ),
    # )

    # Entities
    httpx_mock.add_response(
        url="http://onto-ns.com/meta/1.0/OPTIMADEStructure",
        method="GET",
        json=json.loads((static_folder / "onto-ns_OPTIMADEStructure.json").read_text()),
    )
    httpx_mock.add_response(
        url="http://onto-ns.com/meta/1.0/OPTIMADEStructureAttributes",
        method="GET",
        json=json.loads(
            (static_folder / "onto-ns_OPTIMADEStructureAttributes.json").read_text()
        ),
    )
    httpx_mock.add_response(
        url="http://onto-ns.com/meta/1.0/OPTIMADEStructureSpecies",
        method="GET",
        json=json.loads(
            (static_folder / "onto-ns_OPTIMADEStructureSpecies.json").read_text()
        ),
    )
    httpx_mock.add_response(
        url="http://onto-ns.com/meta/1.0/OPTIMADEStructureAssembly",
        method="GET",
        json=json.loads(
            (static_folder / "onto-ns_OPTIMADEStructureAssembly.json").read_text()
        ),
    )

    # Test with a simple mapping
    mapping_config = MappingConfig(
        mappingType="triples",
        prefixes={
            "optimade": "https://optimade.materialsproject.org/v1/structures/mp-1228448#",
            "soft7": "http://onto-ns.com/meta/1.0/OPTIMADEStructure#",
        },
        triples={
            ("optimade:data.id", "", "soft7:properties.id"),
            ("optimade:data.type", "", "soft7:properties.type"),
            ("optimade:data.attributes", "", "soft7:properties.attributes"),
        },
    )
    generator_config = default_soft7_ote_function_config(
        "http://onto-ns.com/meta/1.0/OPTIMADEStructure"
    )

    # Mock run the pipeline: mapping_strategy >> generator
    # BUT run only up to the point before running `get()` on generator.
    session = (
        SOFT7Generator(function_config=generator_config.model_dump()).initialize()
        or AttrDict()
    )
    session.update(
        MappingStrategy(
            mapping_config=mapping_config.model_copy(
                update={
                    "configuration": mapping_config.configuration.model_copy(
                        update=session
                    )
                },
                deep=True,
            )
        ).initialize()
    )
    session.update(
        MappingStrategy(
            mapping_config=mapping_config.model_copy(
                update={
                    "configuration": mapping_config.configuration.model_copy(
                        update=session
                    )
                },
                deep=True,
            )
        ).get()
    )

    # Instantiate the generator for test running the `get()` method
    generator = SOFT7Generator(
        function_config=generator_config.model_copy(
            update={
                "configuration": generator_config.configuration.model_copy(
                    update=session
                )
            },
            deep=True,
        ).model_dump()
    )

    # Test the `_flatten_mapping()` method
    flat_mapping = generator._flatten_mapping(session)

    assert isinstance(flat_mapping, list)
    assert len(flat_mapping) == len(mapping_config.triples)

    expected_flat_mapping = [
        RDFTriple(*_)
        for _ in [
            (
                {
                    "namespace": AnyHttpUrl(
                        mapping_config.prefixes["optimade"].rstrip("#")
                    ),
                    "concept": "data.id",
                },
                {"namespace": "", "concept": ""},
                {
                    "namespace": AnyHttpUrl(
                        mapping_config.prefixes["soft7"].rstrip("#")
                    ),
                    "concept": "properties.id",
                },
            ),
            (
                {
                    "namespace": AnyHttpUrl(
                        mapping_config.prefixes["optimade"].rstrip("#")
                    ),
                    "concept": "data.type",
                },
                {"namespace": "", "concept": ""},
                {
                    "namespace": AnyHttpUrl(
                        mapping_config.prefixes["soft7"].rstrip("#")
                    ),
                    "concept": "properties.type",
                },
            ),
            (
                {
                    "namespace": AnyHttpUrl(
                        mapping_config.prefixes["optimade"].rstrip("#")
                    ),
                    "concept": "data.attributes",
                },
                {"namespace": "", "concept": ""},
                {
                    "namespace": AnyHttpUrl(
                        mapping_config.prefixes["soft7"].rstrip("#")
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
        AnyHttpUrl,
        SOFT7Entity,
        str,
        dict[str, Any],
        Path,
        type[SOFT7EntityInstance],
    ],
]:
    """Generate test cases for the `test_dataclass_validation()` test."""
    from pathlib import Path

    import yaml
    from pydantic import AnyHttpUrl

    from s7.factories.entity_factory import create_entity
    from s7.pydantic_models.soft7_entity import SOFT7Entity

    static_folder = Path(__file__).parent.parent / "static"

    test_data_entity_path = static_folder / "soft_datasource_entity.yaml"
    test_data_entity = yaml.safe_load(test_data_entity_path.read_text(encoding="utf-8"))
    test_entity = SOFT7Entity(**test_data_entity)

    test_cases = [
        # identity as a string
        test_data_entity["identity"],
        # identity as a URL
        AnyHttpUrl(test_data_entity["identity"]),
        # Entity as a SOFT7Entity instance
        test_entity,
        # Entity as a JSON-serialized string
        test_entity.model_dump_json(exclude_unset=True),
        # Entity as a dict
        test_data_entity,
        # Path to a YAML file containing the Entity
        test_data_entity_path,
        # Entity as a SOFT7EntityInstance class
        create_entity(test_entity),
    ]
    return ["identity", "url", "instance", "json", "dict", "path", "class"], test_cases


@pytest.mark.parametrize("functionType", ["soft7", "SOFT7"])
@pytest.mark.parametrize(
    "entity", _generate_entity_test_cases()[1], ids=_generate_entity_test_cases()[0]
)
def test_dataclass_validation(
    functionType: str,
    entity: Union[
        str, type[SOFT7EntityInstance], dict[str, Any], Path, AnyHttpUrl, SOFT7Entity
    ],
    httpx_mock: HTTPXMock,
    soft_entity_init: dict[str, Union[str, dict]],
) -> None:
    """Check the dataclass instantiates correctly (and validates) with different input
    types."""
    from pydantic import AnyHttpUrl, ValidationError

    from s7.oteapi_plugin.soft7_function import SOFT7Generator
    from s7.pydantic_models.soft7_entity import SOFT7IdentityURI

    if isinstance(entity, (AnyHttpUrl, str)):
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
