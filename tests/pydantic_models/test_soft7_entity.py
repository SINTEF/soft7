"""Tests for `s7.pydantic_models.soft7_entity`."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    import sys
    from pathlib import Path
    from typing import Any, Union

    if sys.version_info >= (3, 10):
        from typing import Literal
    else:
        from typing_extensions import Literal

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
        "AnyHttpUrl",
        "str_url",
        "str_path",
        "str_json_dump",
        "str_yaml_dump",
    ],
)
def test_parse_input_entity(
    soft_entity_init: dict[str, Union[str, dict[str, Any]]],
    soft_entity_init_source: Path,
    entity_type: Literal[
        "SOFT7Entity",
        "dict",
        "Path",
        "AnyHttpUrl",
        "str_url",
        "str_path",
        "str_json_dump",
        "str_yaml_dump",
    ],
    httpx_mock: HTTPXMock,
) -> None:
    """Ensure the `parse_input_entity` function instantiates a SOFT7Entity as
    intended."""
    import json
    from copy import deepcopy
    from pathlib import Path

    import yaml
    from pydantic import AnyHttpUrl

    from s7.pydantic_models.soft7_entity import SOFT7Entity, parse_input_entity

    soft_entity_raw = deepcopy(soft_entity_init)

    expected_entity = SOFT7Entity(**soft_entity_raw)

    if entity_type == "SOFT7Entity":
        entity = parse_input_entity(expected_entity)

    elif entity_type == "dict":
        entity = parse_input_entity(soft_entity_raw)

    elif entity_type == "Path":
        assert isinstance(soft_entity_init_source, Path)
        entity = parse_input_entity(soft_entity_init_source)

    elif entity_type == "AnyHttpUrl":
        # Mock HTTP GET call to retrieve the entity online
        httpx_mock.add_response(
            url=str(expected_entity.identity),
            method="GET",
            json=soft_entity_raw,
        )

        entity = parse_input_entity(AnyHttpUrl(str(expected_entity.identity)))

    elif entity_type == "str_url":
        # Case of it being a URL, i.e., same as for entity_type == "AnyHttpUrl"
        httpx_mock.add_response(
            url=str(expected_entity.identity),
            method="GET",
            json=soft_entity_raw,
        )

        entity = parse_input_entity(str(expected_entity.identity))

    elif entity_type == "str_path":
        # Case of it being a path, i.e., same as for entity_type == "Path"
        entity = parse_input_entity(str(soft_entity_init_source.resolve()))

    elif entity_type == "str_json_dump":
        # A raw JSON dump of the entity
        entity = parse_input_entity(json.dumps(soft_entity_raw))

    elif entity_type == "str_yaml_dump":
        # A raw YAML dump of the entity
        entity = parse_input_entity(yaml.safe_dump(soft_entity_raw))

    else:
        pytest.fail(f"Unexpected entity type: {entity_type}")

    assert entity == expected_entity


@pytest.mark.parametrize("raw_format", ["json", "yaml"])
@pytest.mark.parametrize(
    "entity_type",
    [
        "Path",
        "AnyHttpUrl",
        "str_url",
        "str_path",
        "str_dump",
    ],
)
def test_parse_input_entity_yaml_errors(
    entity_type: Literal["Path", "AnyHttpUrl", "str_url", "str_path", "str_dump"],
    raw_format: Literal["json", "yaml"],
    httpx_mock: HTTPXMock,
    tmp_path: Path,
) -> None:
    """Ensure a proper error message occurs if a YAML/JSON parsing fails."""
    import re
    from pathlib import Path

    import yaml
    from pydantic import AnyHttpUrl

    from s7.exceptions import EntityNotFound
    from s7.pydantic_models.soft7_entity import parse_input_entity

    bad_inputs = {
        "json": "{'description'::'test'}",
        "yaml": "description::\ntest",
    }

    # Make sure the bad input data is... bad
    with pytest.raises(yaml.YAMLError):
        yaml.safe_load(bad_inputs[raw_format])

    # Prepare input according to entity_type
    if entity_type in ("Path", "str_path"):
        test_entity_input = (tmp_path / f"bad_entity.{raw_format}").resolve()
        test_entity_input.write_text(bad_inputs[raw_format], encoding="utf-8")

        if entity_type == "str_path":
            test_entity_input = str(test_entity_input)

        error_msg = (
            r"^Could not parse the entity (string )?as SOFT7 entity from "
            rf"{re.escape(str(Path(test_entity_input).resolve()))} "
            r"\(expecting a JSON/YAML format\)\.$"
        )

    elif entity_type in ("AnyHttpUrl", "str_url"):
        # Mock HTTP GET call to retrieve the entity online
        httpx_mock.add_response(
            url=re.compile(r"^http://example\.org.*"),
            method="GET",
            text=bad_inputs[raw_format],
        )

        test_entity_input = (
            AnyHttpUrl("http://example.org")
            if entity_type == "AnyHttpUrl"
            else "http://example.org"
        )

        # This will be the default error message from `try_load_from_json_yaml()`.
        error_msg = r"^Could not parse the string\. Expecting a YAML/JSON format\.$"

    elif entity_type == "str_dump":
        # A raw JSON/YAML dump of the entity
        test_entity_input = bad_inputs[raw_format]

        error_msg = (
            r"^Could not parse the entity string as SOFT7 entity "
            r"\(expecting a JSON/YAML format\)\.$"
        )

    else:
        pytest.fail(f"Unexpected entity type: {entity_type}")

    with pytest.raises(EntityNotFound, match=error_msg):
        parse_input_entity(test_entity_input)


def test_parse_input_entity_http_error(httpx_mock: HTTPXMock) -> None:
    """Ensure a proper error message occurs if an HTTP error occurs."""
    import re

    from httpx import HTTPError

    from s7.exceptions import EntityNotFound
    from s7.pydantic_models.soft7_entity import parse_input_entity

    bad_url = "http://example.org"

    # Mock HTTP GET call to retrieve the entity online
    httpx_mock.add_exception(
        HTTPError("404 Not Found"),
        url=re.compile(r"^http://example\.org.*"),
        method="Get",
    )

    with pytest.raises(
        EntityNotFound,
        match=rf"^Could not retrieve SOFT7 entity online from {re.escape(bad_url)}$",
    ):
        parse_input_entity("http://example.org")


@pytest.mark.parametrize(
    "entity_type",
    [
        "Path",
        "str_path",
    ],
)
def test_parse_input_entity_path_not_found(
    entity_type: Literal["Path", "str_path"], tmp_path: Path
) -> None:
    """Ensure a proper error message occurs if a file is not found."""
    import re
    from pathlib import Path

    from s7.exceptions import EntityNotFound
    from s7.pydantic_models.soft7_entity import parse_input_entity

    bad_entity_path = tmp_path / "bad_entity.json"

    if entity_type == "Path":
        entity = bad_entity_path

        assert not entity.exists()

    elif entity_type == "str_path":
        entity = str(bad_entity_path)

        assert not Path(entity).exists()
        assert isinstance(entity, str)

    else:
        pytest.fail(f"Unexpected entity type: {entity_type}")

    with pytest.raises(
        EntityNotFound,
        match=(
            r"^Could not find SOFT7 entity JSON/YAML file at "
            rf"{re.escape(str(bad_entity_path))}$"
        ),
    ):
        parse_input_entity(entity)


def test_parse_input_entity_bad_type() -> None:
    """Ensure a proper error message occurs if a bad type is given."""
    from s7.pydantic_models.soft7_entity import parse_input_entity

    bad_input = ["http://example.org"]

    with pytest.raises(
        TypeError,
        match=rf"^Expected entity to be a str at this point, instead got {list}\.$",
    ):
        parse_input_entity(bad_input)
