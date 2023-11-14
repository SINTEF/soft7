"""Test the soft7 OTEAPI function strategy."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


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
        function_config=default_soft7_ote_function_config().model_dump()
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
                        mapping_strategy.mapping_config.prefixes["optimade"]
                    ),
                    "concept": "data.id",
                },
                {"namespace": "", "concept": ""},
                {
                    "namespace": AnyUrl(
                        mapping_strategy.mapping_config.prefixes["soft7"]
                    ),
                    "concept": "properties.id",
                },
            ),
            (
                {
                    "namespace": AnyUrl(
                        mapping_strategy.mapping_config.prefixes["optimade"]
                    ),
                    "concept": "data.type",
                },
                {"namespace": "", "concept": ""},
                {
                    "namespace": AnyUrl(
                        mapping_strategy.mapping_config.prefixes["soft7"]
                    ),
                    "concept": "properties.type",
                },
            ),
            (
                {
                    "namespace": AnyUrl(
                        mapping_strategy.mapping_config.prefixes["optimade"]
                    ),
                    "concept": "data.attributes",
                },
                {"namespace": "", "concept": ""},
                {
                    "namespace": AnyUrl(
                        mapping_strategy.mapping_config.prefixes["soft7"]
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
