"""Tests for `s7.pydantic_models.soft7_entity`."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any, Literal, Union

    from pytest_httpx import HTTPXMock


def test_entity_shapes_and_dimensions(
    soft_entity_init: dict[str, Union[str, dict[str, Any]]],
) -> None:
    """Ensure the validator `shapes_and_dimensions` enforces the desired rules."""
    from s7.pydantic_models.soft7_entity import SOFT7Entity

    additional_dimensions = {
        "nsites": "Number of sites.",
        "cartesian": "Cartesian coordinates.",
    }
    additional_properties = {
        "radius": {
            "type": "float",
            "shape": ["N"],
            "description": "Atomic radius.",
            "unit": "Å",
        },
        "positions": {
            "type": "float",
            "shape": ["nsites", "cartesian"],
            "description": "Atomic positions.",
            "unit": "Å",
        },
    }

    assert soft_entity_init["dimensions"]
    assert isinstance(soft_entity_init["dimensions"], dict)

    assert soft_entity_init["properties"]
    assert isinstance(soft_entity_init["properties"], dict)

    soft_entity_init["dimensions"].update(additional_dimensions)
    soft_entity_init["properties"].update(additional_properties)

    SOFT7Entity(**soft_entity_init)


@pytest.mark.parametrize(
    "entity_type",
    [
        "SOFT7Entity",
        "dict",
        "Path",
        "AnyUrl",
        "str_url",
        "str_path",
        "str_json_dump",
        "str_yaml_dump",
    ],
)
def test_parse_input_entity(
    soft_entity_init: dict[str, Union[str, dict[str, Any]]],
    soft_entity_init_source: Path,
    entity_type: Literal["SOFT7Entity", "dict", "Path", "AnyUrl", "str"],
    httpx_mock: HTTPXMock,
) -> None:
    """Ensure the `parse_input_entity` function instantiates a SOFT7Entity as
    intended."""
    import json
    from copy import deepcopy
    from pathlib import Path

    import yaml
    from pydantic import AnyUrl

    from s7.pydantic_models.soft7_entity import SOFT7Entity, parse_input_entity

    soft_entity_raw = deepcopy(soft_entity_init)

    expected_entity = SOFT7Entity(**soft_entity_raw)

    if entity_type == "SOFT7Entity":
        entity = parse_input_entity(expected_entity)
        assert entity == expected_entity

    elif entity_type == "dict":
        entity = parse_input_entity(soft_entity_raw)
        assert entity == expected_entity

    elif entity_type == "Path":
        assert isinstance(soft_entity_init_source, Path)
        entity = parse_input_entity(soft_entity_init_source)
        assert entity == expected_entity

    elif entity_type == "AnyUrl":
        # Mock HTTP GERT call to rwetrieve the entity online
        httpx_mock.add_response(
            url=str(expected_entity.identity),
            method="GET",
            json=soft_entity_raw,
        )

        entity = parse_input_entity(AnyUrl(str(expected_entity.identity)))
        assert entity == expected_entity

    elif entity_type == "str_url":
        # Case of it being a URL, i.e., same as for entity_type == "AnyUrl"
        httpx_mock.add_response(
            url=str(expected_entity.identity),
            method="GET",
            json=soft_entity_raw,
        )

        entity = parse_input_entity(str(expected_entity.identity))
        assert entity == expected_entity

    elif entity_type == "str_path":
        # Case of it being a path, i.e., same as for entity_type == "Path"
        entity = parse_input_entity(str(soft_entity_init_source.resolve()))
        assert entity == expected_entity

    elif entity_type == "str_json_dump":
        # A raw JSON dump of the entity
        entity = parse_input_entity(json.dumps(soft_entity_raw))
        assert entity == expected_entity

    elif entity_type == "str_yaml_dump":
        # A raw YAML dump of the entity
        entity = parse_input_entity(yaml.safe_dump(soft_entity_raw))
        assert entity == expected_entity

    else:
        pytest.fail(f"Unexpected entity type: {entity_type}")
