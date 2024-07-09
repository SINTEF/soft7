"""Tests for `s7.pydantic_models.datasource`."""

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

    from s7.pydantic_models.datasource import GetDataConfigDict
    from s7.pydantic_models.oteapi import (
        HashableFunctionConfig,
        HashableMappingConfig,
        HashableParserConfig,
        HashableResourceConfig,
    )


@pytest.mark.parametrize(
    "configs_type",
    [
        "GetDataConfigDict",
        "dict_GenericConfig",
        "dict_dict",
        "dict_Path",
        "dict_AnyUrl",
        "dict_str_url",
        "dict_str_path",
        "dict_str_json_dump",
        "dict_str_yaml_dump",
        "dict_None",
        "Path",
        "AnyUrl",
        "str_url",
        "str_path",
        "str_json_dump",
        "str_yaml_dump",
    ],
)
@pytest.mark.parametrize(
    "entity_instance_type",
    [
        "None",
        "SOFT7EntityInstance",
        "SOFT7IdentityURIType",
        "str",
    ],
)
def test_parse_input_configs(
    soft_datasource_configs: dict[str, dict[str, Any]],
    name_to_config_type_mapping: dict[
        Literal["dataresource", "function", "mapping", "parser"],
        type[
            HashableFunctionConfig
            | HashableMappingConfig
            | HashableParserConfig
            | HashableResourceConfig
        ],
    ],
    soft_entity_init: dict[str, str | dict[str, Any]],
    configs_type: Literal[
        "GetDataConfigDict",
        "dict_GenericConfig",
        "dict_dict",
        "dict_Path",
        "dict_AnyUrl",
        "dict_str_url",
        "dict_str_path",
        "dict_str_json_dump",
        "dict_str_yaml_dump",
        "dict_None",
        "Path",
        "AnyUrl",
        "str_url",
        "str_path",
        "str_json_dump",
        "str_yaml_dump",
    ],
    entity_instance_type: Literal[
        "None",
        "SOFT7EntityInstance",
        "SOFT7IdentityURIType",
        "str",
    ],
    httpx_mock: HTTPXMock,
    tmp_path: Path,
) -> None:
    """Ensure the `parse_input_configs` function instantiates a GetDataConfigDict as
    intended."""
    import json
    import re
    from copy import deepcopy

    import yaml
    from pydantic import AnyUrl

    from s7.factories.entity_factory import create_entity
    from s7.pydantic_models.datasource import parse_input_configs
    from s7.pydantic_models.soft7_entity import SOFT7IdentityURI

    soft_datasource_configs_raw = deepcopy(soft_datasource_configs)

    expected_configs: GetDataConfigDict = {
        key: name_to_config_type_mapping[key](**value)
        for key, value in soft_datasource_configs_raw.items()
    }

    # Determine the `configs` input parameter
    if configs_type == "GetDataConfigDict":
        configs = expected_configs

    elif configs_type == "dict_GenericConfig":
        # Effectively the same as for `GetDataConfigDict`
        configs = dict(expected_configs)

    elif configs_type == "dict_dict":
        configs = {key: value.model_dump() for key, value in expected_configs.items()}

    elif configs_type == "dict_Path":
        configs = {}
        for index, (key, value) in enumerate(expected_configs.items()):
            # There are four entries in expected_configs, so this should give a 50/50
            # file format split, testing both JSON and YAML.
            file_format = "json" if index % 2 == 0 else "yaml"

            configs[key] = tmp_path / f"{key}.{file_format}"
            configs[key].write_text(
                (
                    json.dumps(value.model_dump(mode="json"))
                    if file_format == "json"
                    else yaml.safe_dump(value.model_dump(mode="json"))
                ),
                encoding="utf-8",
            )

    elif configs_type == "dict_AnyUrl":
        # Create URLs for each config
        configs = {}
        for key, value in expected_configs.items():
            configs[key] = AnyUrl(f"http://example.org/{key}")

            # Mock HTTP GET call to retrieve the configs online
            httpx_mock.add_response(
                url=re.compile(rf"^http://example\.org/{key}.*"),
                method="GET",
                json=value.model_dump(mode="json"),
            )

    elif configs_type == "dict_str_url":
        # Case of the configuration values being a URL, i.e., same as for
        # configs_type == "dict_AnyUrl"

        # Create URLs for each config
        configs = {}
        for key, value in expected_configs.items():
            configs[key] = f"http://example.org/{key}"

            # Mock HTTP GET call to retrieve the configs online
            httpx_mock.add_response(
                url=re.compile(rf"^http://example\.org/{key}.*"),
                method="GET",
                json=value.model_dump(mode="json"),
            )

    elif configs_type == "dict_str_path":
        # Case of the configuration values being a path, i.e., same as for
        # configs_type == "dict_Path"
        configs = {}
        for index, (key, value) in enumerate(expected_configs.items()):
            # There are four entries in expected_configs, so this should give a 50/50
            # file format split, testing both JSON and YAML.
            file_format = "json" if index % 2 == 0 else "yaml"

            configs[key] = tmp_path / f"{key}.{file_format}"
            configs[key].write_text(
                (
                    json.dumps(value.model_dump(mode="json"))
                    if file_format == "json"
                    else yaml.safe_dump(value.model_dump(mode="json"))
                ),
                encoding="utf-8",
            )
            configs = {key: str(value.resolve()) for key, value in configs.items()}

    elif configs_type == "dict_str_json_dump":
        # A raw JSON dump of the configs
        configs = {
            key: json.dumps(value) for key, value in soft_datasource_configs_raw.items()
        }

    elif configs_type == "dict_str_yaml_dump":
        # A raw YAML dump of the configs
        configs = {
            key: yaml.safe_dump(value)
            for key, value in soft_datasource_configs_raw.items()
        }

    elif configs_type == "dict_None":
        # `None` is only allowed for the "function" configuration
        configs = soft_datasource_configs_raw
        configs["function"] = None

    elif configs_type == "Path":
        configs = tmp_path / "configs.yaml"
        configs.write_text(
            yaml.safe_dump(soft_datasource_configs_raw),
            encoding="utf-8",
        )

    elif configs_type == "AnyUrl":
        # Mock HTTP GET call to retrieve the configs online
        httpx_mock.add_response(
            url=re.compile(r"^http://example\.org/configs.*"),
            method="GET",
            json=soft_datasource_configs_raw,
        )

        configs = AnyUrl("http://example.org/configs")

    elif configs_type == "str_url":
        # Case of it being a URL, i.e., same as for configs_type == "AnyUrl"
        httpx_mock.add_response(
            url=re.compile(r"^http://example\.org/configs.*"),
            method="GET",
            json=soft_datasource_configs_raw,
        )

        configs = "http://example.org/configs"

    elif configs_type == "str_path":
        # Case of it being a path, i.e., same as for configs_type == "Path"
        configs = tmp_path / "configs.yaml"
        configs.write_text(
            yaml.safe_dump(soft_datasource_configs_raw),
            encoding="utf-8",
        )

        configs = str(configs.resolve())

    elif configs_type == "str_json_dump":
        # A raw JSON dump of the configs
        configs = json.dumps(soft_datasource_configs_raw)

    elif configs_type == "str_yaml_dump":
        # A raw YAML dump of the configs
        configs = yaml.safe_dump(soft_datasource_configs_raw)

    else:
        pytest.fail(f"Unexpected configs type: {configs_type}")

    # Determine the `entity_instance` input parameter
    if entity_instance_type == "None":
        entity_instance = None

        # `None` is only allowed if "function" is already defined
        if isinstance(configs, dict) and configs.get("function", None) is None:
            pytest.skip(
                "Skipping test as 'function' is not defined in the configs "
                "and entity_instance is requested to be `None`."
            )

    elif entity_instance_type == "SOFT7EntityInstance":
        entity_instance = create_entity(soft_entity_init)

    elif entity_instance_type == "SOFT7IdentityURIType":
        entity_instance = SOFT7IdentityURI(str(soft_entity_init["identity"]))

    elif entity_instance_type == "str":
        entity_instance = str(soft_entity_init["identity"])

    else:
        pytest.fail(f"Unexpected entity instance type: {entity_instance_type}")

    # Run `parse_input_configs()`
    parsed_input_configs = parse_input_configs(
        configs=configs, entity_instance=entity_instance
    )

    assert {key: expected_configs[key] for key in sorted(expected_configs)} == {
        key: parsed_input_configs[key] for key in sorted(parsed_input_configs)
    }


# @pytest.mark.parametrize("raw_format", ["json", "yaml"])
# @pytest.mark.parametrize(
#     "entity_type",
#     [
#         "Path",
#         "AnyUrl",
#         "str_url",
#         "str_path",
#         "str_dump",
#     ],
# )
# def test_parse_input_configs_yaml_errors(
#     entity_type: Literal["Path", "AnyUrl", "str_url", "str_path", "str_dump"],
#     raw_format: Literal["json", "yaml"],
#     httpx_mock: HTTPXMock,
#     tmp_path: Path,
# ) -> None:
#     """Ensure a proper error message occurs if a YAML/JSON parsing fails."""
#     import re
#     from pathlib import Path

#     import yaml
#     from pydantic import AnyUrl

#     from s7.exceptions import EntityNotFound
#     from s7.pydantic_models.soft7_entity import parse_input_configs

#     bad_inputs = {
#         "json": "{'description'::'test'}",
#         "yaml": "description::\ntest",
#     }

#     # Make sure the bad input data is... bad
#     with pytest.raises(yaml.YAMLError):
#         yaml.safe_load(bad_inputs[raw_format])

#     # Prepare input according to entity_type
#     if entity_type == "Path":
#         test_entity_input = tmp_path / f"bad_entity.{raw_format}"
#         test_entity_input.write_text(bad_inputs[raw_format], encoding="utf-8")

#         assert isinstance(test_entity_input, Path)

#     elif entity_type == "AnyUrl":
#         # Mock HTTP GET call to retrieve the entity online
#         httpx_mock.add_response(
#             url=re.compile(r"^http://example\.org.*"),
#             method="GET",
#             text=bad_inputs[raw_format],
#         )

#         test_entity_input = AnyUrl("http://example.org")

#     elif entity_type == "str_url":
#         # Case of it being a URL, i.e., same as for entity_type == "AnyUrl"
#         httpx_mock.add_response(
#             url=re.compile(r"^http://example\.org.*"),
#             method="GET",
#             text=bad_inputs[raw_format],
#         )

#         test_entity_input = "http://example.org"

#     elif entity_type == "str_path":
#         # Case of it being a path, i.e., same as for entity_type == "Path"
#         test_entity_input = tmp_path / f"bad_entity.{raw_format}"
#         test_entity_input.write_text(bad_inputs[raw_format], encoding="utf-8")

#         test_entity_input = str(test_entity_input.resolve())

#     elif entity_type == "str_dump":
#         # A raw JSON/YAML dump of the entity
#         test_entity_input = bad_inputs[raw_format]

#     else:
#         pytest.fail(f"Unexpected entity type: {entity_type}")

#     with pytest.raises(
#         EntityNotFound,
#         match=(
#             r"^Could not parse the entity string as a SOFT7 entity "
#             r"\(YAML/JSON format\)\.$"
#         ),
#     ):
#         parse_input_configs(test_entity_input)


# def test_parse_input_configs_http_error(httpx_mock: HTTPXMock) -> None:
#     """Ensure a proper error message occurs if an HTTP error occurs."""
#     import re

#     from httpx import HTTPError

#     from s7.exceptions import EntityNotFound
#     from s7.pydantic_models.soft7_entity import parse_input_configs

#     bad_url = "http://example.org"

#     # Mock HTTP GET call to retrieve the entity online
#     httpx_mock.add_exception(
#         HTTPError("404 Not Found"),
#         url=re.compile(r"^http://example\.org.*"),
#         method="Get",
#     )

#     with pytest.raises(
#         EntityNotFound,
#         match=rf"^Could not retrieve SOFT7 entity online from {re.escape(bad_url)}$",
#     ):
#         parse_input_configs("http://example.org")


# def test_parse_input_configs_path_not_found(tmp_path: Path) -> None:
#     """Ensure a proper error message occurs if a file is not found."""
#     import re

#     from s7.exceptions import EntityNotFound
#     from s7.pydantic_models.soft7_entity import parse_input_configs

#     bad_entity_path = tmp_path / "bad_entity.json"

#     assert not bad_entity_path.exists()

#     with pytest.raises(
#         EntityNotFound,
#         match=(
#             r"^Could not find an entity JSON/YAML file at "
#             rf"{re.escape(str(bad_entity_path))}$"
#         ),
#     ):
#         parse_input_configs(bad_entity_path)


# def test_parse_input_configs_bad_type() -> None:
#     """Ensure a proper error message occurs if a bad type is given."""
#     from s7.pydantic_models.soft7_entity import parse_input_configs

#     bad_input = ["http://example.org"]

#     with pytest.raises(
#         TypeError,
#         match=rf"^entity must be a 'SOFT7Entity', instead it was a {type(bad_input)}$",
#     ):
#         parse_input_configs(bad_input)
