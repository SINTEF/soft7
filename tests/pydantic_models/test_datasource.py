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
        "dict_AnyHttpUrl",
        "dict_str_url",
        "dict_str_path",
        "dict_str_json_dump",
        "dict_str_yaml_dump",
        "dict_None",
        "Path",
        "AnyHttpUrl",
        "str_url",
        "str_path",
        "str_json_dump",
        "str_yaml_dump",
    ],
    ids=[
        "configs:GetDataConfigDict",
        "configs:dict_GenericConfig",
        "configs:dict_dict",
        "configs:dict_Path",
        "configs:dict_AnyHttpUrl",
        "configs:dict_str_url",
        "configs:dict_str_path",
        "configs:dict_str_json_dump",
        "configs:dict_str_yaml_dump",
        "configs:dict_None",
        "configs:Path",
        "configs:AnyHttpUrl",
        "configs:str_url",
        "configs:str_path",
        "configs:str_json_dump",
        "configs:str_yaml_dump",
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
    ids=[
        "entity_instance:None",
        "entity_instance:SOFT7EntityInstance",
        "entity_instance:SOFT7IdentityURIType",
        "entity_instance:str",
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
        "dict_AnyHttpUrl",
        "dict_str_url",
        "dict_str_path",
        "dict_str_json_dump",
        "dict_str_yaml_dump",
        "dict_None",
        "Path",
        "AnyHttpUrl",
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
    from pathlib import Path

    import yaml
    from pydantic import AnyHttpUrl

    from s7.exceptions import EntityNotFound
    from s7.factories.entity_factory import create_entity
    from s7.pydantic_models.datasource import parse_input_configs
    from s7.pydantic_models.soft7_entity import SOFT7IdentityURI

    should_raise: tuple[type[Exception], str] | None = None

    soft_datasource_configs_raw = deepcopy(soft_datasource_configs)

    expected_configs: GetDataConfigDict = {
        key: name_to_config_type_mapping[key](**value)
        for key, value in soft_datasource_configs_raw.items()
    }

    # Set the `configs` input parameter
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
        assert all(isinstance(value, Path) for value in configs.values())

    elif configs_type == "dict_AnyHttpUrl":
        # Create URLs for each config
        configs = {}
        for key, value in expected_configs.items():
            configs[key] = AnyHttpUrl(f"http://example.org/{key}")

            # Mock HTTP GET call to retrieve the configs online
            httpx_mock.add_response(
                url=re.compile(rf"^http://example\.org/{key}.*"),
                method="GET",
                json=value.model_dump(mode="json"),
            )

    elif configs_type == "dict_str_url":
        # Case of the configuration values being a URL, i.e., same as for
        # configs_type == "dict_AnyHttpUrl"

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
        assert all(isinstance(value, str) for value in configs.values())

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

    elif configs_type == "AnyHttpUrl":
        # Mock HTTP GET call to retrieve the configs online
        httpx_mock.add_response(
            url=re.compile(r"^http://example\.org/configs.*"),
            method="GET",
            json=soft_datasource_configs_raw,
        )

        configs = AnyHttpUrl("http://example.org/configs")

    elif configs_type == "str_url":
        # Case of it being a URL, i.e., same as for configs_type == "AnyHttpUrl"
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

    # Set the `entity_instance` input parameter
    if entity_instance_type == "None":
        entity_instance = None
    elif entity_instance_type == "SOFT7EntityInstance":
        entity_instance = create_entity(soft_entity_init)
    elif entity_instance_type == "SOFT7IdentityURIType":
        entity_instance = SOFT7IdentityURI(str(soft_entity_init["identity"]))
    elif entity_instance_type == "str":
        entity_instance = str(soft_entity_init["identity"])
    else:
        pytest.fail(f"Unexpected entity instance type: {entity_instance_type}")

    # Determine and adjust the expected consequence based on the `entity_instance`
    # value.
    # The expected output will change IF the 'function' value is `None`,
    # since this will generate inputs using the given entity instance.
    if isinstance(configs, dict) and configs.get("function", None) is None:
        expected_configs["function"].configuration.entity = (
            entity_instance
            if not isinstance(entity_instance, str)
            else SOFT7IdentityURI(entity_instance)
        )

        if entity_instance is None:
            # `None` is only allowed if "function" is already defined
            should_raise = (
                EntityNotFound,
                r"^The entity must be provided if the function config is not "
                r"provided\.$",
            )

    # Run `parse_input_configs()`
    if should_raise is not None:
        with pytest.raises(should_raise[0], match=should_raise[1]):
            parse_input_configs(configs=configs, entity_instance=entity_instance)
    else:
        parsed_input_configs = parse_input_configs(
            configs=configs, entity_instance=entity_instance
        )

        assert {key: expected_configs[key] for key in sorted(expected_configs)} == {
            key: parsed_input_configs[key] for key in sorted(parsed_input_configs)
        }


@pytest.mark.parametrize("raw_format", ["json", "yaml"])
@pytest.mark.parametrize(
    "configs_type",
    [
        "dict_Path",
        "dict_AnyHttpUrl",
        "dict_str_url",
        "dict_str_path",
        "dict_str_dump",
        "Path",
        "AnyHttpUrl",
        "str_url",
        "str_path",
        "str_dump",
    ],
    ids=[
        "configs:dict_Path",
        "configs:dict_AnyHttpUrl",
        "configs:dict_str_url",
        "configs:dict_str_path",
        "configs:dict_str_dump",
        "configs:Path",
        "configs:AnyHttpUrl",
        "configs:str_url",
        "configs:str_path",
        "configs:str_dump",
    ],
)
def test_parse_input_configs_yaml_errors(
    configs_type: Literal[
        "dict_Path",
        "dict_AnyHttpUrl",
        "dict_str_url",
        "dict_str_path",
        "dict_str_dump",
        "Path",
        "AnyHttpUrl",
        "str_url",
        "str_path",
        "str_dump",
    ],
    raw_format: Literal["json", "yaml"],
    httpx_mock: HTTPXMock,
    tmp_path: Path,
) -> None:
    """Ensure a proper error message occurs if a YAML/JSON parsing fails."""
    import re
    from pathlib import Path

    import yaml
    from pydantic import AnyHttpUrl

    from s7.exceptions import ConfigsNotFound
    from s7.pydantic_models.datasource import parse_input_configs

    config_keys = ["dataresource", "function", "mapping", "parser"]

    bad_inputs = {
        "json": "{'description'::'test'}",
        "yaml": "description::\ntest",
    }

    # Make sure the bad input data is... bad
    with pytest.raises(yaml.YAMLError):
        yaml.safe_load(bad_inputs[raw_format])

    # Prepare input according to configs_type
    if configs_type in ("dict_Path", "dict_str_path"):
        configs = {}
        for key in config_keys:
            configs[key] = (tmp_path / f"{key}.{raw_format}").resolve()
            configs[key].write_text(bad_inputs[raw_format], encoding="utf-8")

        if configs_type == "dict_str_path":
            configs = {key: str(value) for key, value in configs.items()}

        error_msg = (
            rf"^Could not parse the ({'|'.join(config_keys)}) config (string )?as "
            rf"OTEAPI ({'|'.join(_.capitalize() for _ in config_keys)})Config from "
            rf"{re.escape(str(tmp_path))}/({'|'.join(config_keys)}).{raw_format} "
            r"\(expecting a JSON/YAML format\)\.$"
        )

    elif configs_type in ("dict_AnyHttpUrl", "dict_str_url"):
        # Create URLs for each config
        configs = {}
        for key in config_keys:
            configs[key] = (
                AnyHttpUrl(f"http://example.org/{key}")
                if configs_type == "dict_AnyHttpUrl"
                else f"http://example.org/{key}"
            )

        # Mock HTTP GET call to retrieve the configs online.
        # Mock once and at the root domain, since the error will raise before all
        # configs will be checked.
        httpx_mock.add_response(
            url=re.compile(r"^http://example\.org/.*"),
            method="GET",
            text=bad_inputs[raw_format],
        )

        # This will be the default error message from `try_load_from_json_yaml()`.
        error_msg = r"^Could not parse the string\. Expecting a YAML/JSON format\.$"

    elif configs_type == "dict_str_dump":
        # A raw JSON/YAML dump of the configs
        configs = {key: bad_inputs[raw_format] for key in config_keys}

        error_msg = (
            rf"^Could not parse the ({'|'.join(config_keys)}) config string as OTEAPI "
            rf"({'|'.join(_.capitalize() for _ in config_keys)})Config \(expecting a "
            r"JSON/YAML format\)\.$"
        )

    elif configs_type in ("Path", "str_path"):
        configs = (tmp_path / f"bad_configs.{raw_format}").resolve()
        configs.write_text(bad_inputs[raw_format], encoding="utf-8")

        if configs_type == "str_path":
            configs = str(configs)

        error_msg = (
            r"^Could not parse the configs (string )?as OTEAPI configurations from "
            rf"{re.escape(str(Path(configs)))} \(expecting a JSON/YAML format\)\.$"
        )

    elif configs_type in ("AnyHttpUrl", "str_url"):
        # Mock HTTP GET call to retrieve the configs online
        httpx_mock.add_response(
            url=re.compile(r"^http://example\.org/configs.*"),
            method="GET",
            text=bad_inputs[raw_format],
        )

        configs = (
            AnyHttpUrl("http://example.org/configs")
            if configs_type == "AnyHttpUrl"
            else "http://example.org/configs"
        )

        # This will be the default error message from `try_load_from_json_yaml()`.
        error_msg = r"^Could not parse the string\. Expecting a YAML/JSON format\.$"

    elif configs_type == "str_dump":
        # A raw JSON/YAML dump of the configs
        configs = bad_inputs[raw_format]

        error_msg = (
            r"^Could not parse the configs string as OTEAPI configurations "
            r"\(expecting a JSON/YAML format\)\.$"
        )

    else:
        pytest.fail(f"Unexpected configs type: {configs_type}")

    with pytest.raises(ConfigsNotFound, match=error_msg):
        parse_input_configs(configs)


@pytest.mark.parametrize(
    "configs_type",
    [
        "dict_AnyHttpUrl",
        "dict_str_url",
        "AnyHttpUrl",
        "str_url",
    ],
    ids=[
        "configs:dict_AnyHttpUrl",
        "configs:dict_str_url",
        "configs:AnyHttpUrl",
        "configs:str_url",
    ],
)
def test_parse_input_configs_http_error(
    configs_type: Literal["dict_AnyHttpUrl", "dict_str_url", "AnyHttpUrl", "str_url"],
    httpx_mock: HTTPXMock,
) -> None:
    """Ensure a proper error message occurs if an HTTP error occurs."""
    import re

    from httpx import HTTPError
    from pydantic import AnyHttpUrl

    from s7.exceptions import ConfigsNotFound
    from s7.pydantic_models.datasource import parse_input_configs

    config_keys = ["dataresource", "function", "mapping", "parser"]

    bad_url = "http://example.org"

    # Mock HTTP GET call to raise an HTTP error
    httpx_mock.add_exception(
        HTTPError("404 Not Found"),
        url=re.compile(rf"^{re.escape(bad_url)}.*"),
        method="GET",
    )

    # Prepare input according to configs_type
    if configs_type in ("dict_AnyHttpUrl", "dict_str_url"):
        # Create URLs for each config
        configs = {
            key: (
                AnyHttpUrl(f"{bad_url}/{key}")
                if configs_type == "dict_AnyHttpUrl"
                else f"{bad_url}/{key}"
            )
            for key in config_keys
        }

    elif configs_type in ("AnyHttpUrl", "str_url"):
        configs = AnyHttpUrl(bad_url) if configs_type == "AnyHttpUrl" else bad_url

    else:
        pytest.fail(f"Unexpected configs type: {configs_type}")

    # Determine error message based on the `configs_type`
    error_message = (
        (
            r"^Could not retrieve OTEAPI "
            rf"({'|'.join(_.capitalize() for _ in config_keys)})Config online "
            rf"from {re.escape(bad_url)}/({'|'.join(config_keys)})$"
        )
        if configs_type.startswith("dict_")
        else (
            r"^Could not retrieve OTEAPI configurations online from "
            rf"{re.escape(str(configs))}$"
        )
    )

    # Run `parse_input_configs()` expecting an error
    with pytest.raises(ConfigsNotFound, match=error_message):
        parse_input_configs(configs)


@pytest.mark.parametrize(
    "configs_type",
    [
        "dict_Path",
        "dict_str_path",
        "Path",
        "str_path",
    ],
    ids=[
        "configs:dict_Path",
        "configs:dict_str_path",
        "configs:Path",
        "configs:str_path",
    ],
)
def test_parse_input_configs_path_not_found(
    configs_type: Literal["dict_Path", "dict_str_path", "Path", "str_path"],
    tmp_path: Path,
) -> None:
    """Ensure a proper error message occurs if a file is not found."""
    import re

    from s7.exceptions import ConfigsNotFound
    from s7.pydantic_models.datasource import parse_input_configs

    config_keys = ["dataresource", "function", "mapping", "parser"]

    # Prepare input according to configs_type
    # Determine error message based on the `configs_type`
    if configs_type in ("dict_Path", "dict_str_path"):
        configs = {key: (tmp_path / f"{key}.json").resolve() for key in config_keys}

        assert all(not value.exists() for value in configs.values())

        if configs_type == "dict_str_path":
            configs = {key: str(value) for key, value in configs.items()}

    elif configs_type in ("Path", "str_path"):
        configs = (tmp_path / "bad_configs.json").resolve()

        assert not configs.exists()

        if configs_type == "str_path":
            configs = str(configs)

    else:
        pytest.fail(f"Unexpected configs type: {configs_type}")

    # Determine error message based on the `configs_type`
    error_message = (
        (
            r"^Could not find OTEAPI "
            rf"({'|'.join(_.capitalize() for _ in config_keys)})Config JSON/YAML file "
            rf"at {re.escape(str(tmp_path))}/({'|'.join(config_keys)})\.json$"
        )
        if configs_type.startswith("dict_")
        else (
            r"^Could not find OTEAPI configurations JSON/YAML file at "
            rf"{re.escape(str(configs))}$"
        )
    )

    # Run `parse_input_configs()` expecting an error
    with pytest.raises(ConfigsNotFound, match=error_message):
        parse_input_configs(configs)


def test_parse_input_configs_bad_type() -> None:
    """Ensure a proper error message occurs if a bad type is given."""
    from s7.pydantic_models.datasource import parse_input_configs

    bad_input = ["http://example.org"]

    with pytest.raises(
        TypeError,
        match=(
            r"^The configs provided must be \(a reference to\) a dictionary of "
            r"OTEAPI configurations\.$"
        ),
    ):
        parse_input_configs(bad_input)


@pytest.mark.parametrize(
    ("missing_config", "entity_instance_type"),
    [
        ("dataresource", "None"),
        ("function", "None"),
        ("function", "SOFT7IdentityURIType"),
        ("mapping", "None"),
        ("parser", "None"),
        ("dataresource,parser", "None"),
    ],
)
def test_parse_input_configs_missing_configs(
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
    missing_config: Literal[
        "dataresource", "function", "mapping", "parser", "dataresource,parser"
    ],
    entity_instance_type: Literal["None", "SOFT7IdentityURIType"],
) -> None:
    """Ensure a proper error message or actions occurs if a config is missing."""
    from copy import deepcopy

    from s7.exceptions import EntityNotFound, S7EntityError
    from s7.pydantic_models.datasource import parse_input_configs
    from s7.pydantic_models.soft7_entity import SOFT7IdentityURI

    error_specifics: tuple[type[Exception], str] | None = None

    configs = deepcopy(soft_datasource_configs)
    for config_name in missing_config.split(","):
        configs.pop(config_name)
    assert len(configs) == (4 - len(missing_config.split(",")))

    expected_configs: GetDataConfigDict = {
        key: name_to_config_type_mapping[key](**value)
        for key, value in soft_datasource_configs.items()
        if key in configs or key == "function"
    }

    # Set entity_instance based on the `entity_instance_type`
    if entity_instance_type == "None":
        entity_instance = None
    elif entity_instance_type == "SOFT7IdentityURIType":
        entity_instance = SOFT7IdentityURI(str(soft_entity_init["identity"]))
    else:
        pytest.fail(f"Unexpected entity instance type: {entity_instance_type}")

    # Determine whether an error is expected or not
    if (
        missing_config == "function" and entity_instance_type == "SOFT7IdentityURIType"
    ) or missing_config == "mapping":
        # This is allowed, since the function and mapping configs are optional.

        # Concerning the function config, it is only allowed to be missing if the
        # entity_instance is given.

        if missing_config == "function":
            # Ensure the entity in the generated function configuration matches the
            # `entity_instance` input
            expected_configs["function"].configuration.entity = entity_instance

    elif missing_config == "function" and entity_instance_type == "None":
        error_specifics = (
            EntityNotFound,
            r"^The entity must be provided if the function config is not provided\.$",
        )

    elif missing_config == "dataresource":
        error_specifics = (
            S7EntityError,
            r"^The configs provided must contain a Data Resource configuration$",
        )

    elif missing_config == "parser":
        error_specifics = (
            S7EntityError,
            r"^The configs provided must contain a Parser configuration$",
        )

    elif missing_config == "dataresource,parser":
        error_specifics = (
            S7EntityError,
            r"^The configs provided must contain a Data Resource configuration "
            r"and a Parser configuration$",
        )

    else:
        pytest.fail(f"Unexpected missing config: {missing_config}")

    # Run `parse_input_configs()` either expecting an error or not
    if error_specifics is not None:
        with pytest.raises(error_specifics[0], match=error_specifics[1]):
            parse_input_configs(configs=configs, entity_instance=entity_instance)
    else:
        parsed_input_configs = parse_input_configs(
            configs=configs,
            entity_instance=entity_instance,
        )

        assert {
            key: parsed_input_configs[key] for key in sorted(parsed_input_configs)
        } == {key: expected_configs[key] for key in sorted(expected_configs)}


@pytest.mark.parametrize(
    ("configs_type", "configs_value_kind"),
    [
        ("dict_dict", ""),
        ("dict_Path", ""),
        ("dict_AnyHttpUrl", ""),
        ("dict_str_url", ""),
        ("dict_str_path", ""),
        ("dict_str_json_dump", ""),
        ("dict_str_yaml_dump", ""),
        ("Path", "part"),
        ("Path", "whole-name"),
        ("Path", "whole-type-key"),
        ("Path", "whole-type-value"),
        ("AnyHttpUrl", "part"),
        ("AnyHttpUrl", "whole-name"),
        ("AnyHttpUrl", "whole-type-key"),
        ("AnyHttpUrl", "whole-type-value"),
        ("str_url", "part"),
        ("str_url", "whole-name"),
        ("str_url", "whole-type-key"),
        ("str_url", "whole-type-value"),
        ("str_path", "part"),
        ("str_path", "whole-name"),
        ("str_path", "whole-type-key"),
        ("str_path", "whole-type-value"),
        ("str_json_dump", "part"),
        ("str_json_dump", "whole-name"),
        ("str_json_dump", "whole-type-key"),
        ("str_json_dump", "whole-type-value"),
        ("str_yaml_dump", "part"),
        ("str_yaml_dump", "whole-name"),
        ("str_yaml_dump", "whole-type-key"),
        ("str_yaml_dump", "whole-type-value"),
    ],
    ids=[
        "configs:dict_dict",
        "configs:dict_Path",
        "configs:dict_AnyHttpUrl",
        "configs:dict_str_url",
        "configs:dict_str_path",
        "configs:dict_str_json_dump",
        "configs:dict_str_yaml_dump",
        "configs:Path-part",
        "configs:Path-whole-name",
        "configs:Path-whole-type-key",
        "configs:Path-whole-type-value",
        "configs:AnyHttpUrl-part",
        "configs:AnyHttpUrl-whole-name",
        "configs:AnyHttpUrl-whole-type-key",
        "configs:AnyHttpUrl-whole-type-value",
        "configs:str_url-part",
        "configs:str_url-whole-name",
        "configs:str_url-whole-type-key",
        "configs:str_url-whole-type-value",
        "configs:str_path-part",
        "configs:str_path-whole-name",
        "configs:str_path-whole-type-key",
        "configs:str_path-whole-type-value",
        "configs:str_json_dump-part",
        "configs:str_json_dump-whole-name",
        "configs:str_json_dump-whole-type-key",
        "configs:str_json_dump-whole-type-value",
        "configs:str_yaml_dump-part",
        "configs:str_yaml_dump-whole-name",
        "configs:str_yaml_dump-whole-type-key",
        "configs:str_yaml_dump-whole-type-value",
    ],
)
def test_parse_input_configs_malformed_configs(
    configs_type: Literal[
        "dict_dict",
        "dict_Path",
        "dict_AnyHttpUrl",
        "dict_str_url",
        "dict_str_path",
        "dict_str_json_dump",
        "dict_str_yaml_dump",
        "Path",
        "AnyHttpUrl",
        "str_url",
        "str_path",
        "str_json_dump",
        "str_yaml_dump",
    ],
    configs_value_kind: Literal[
        "", "part", "whole-name", "whole-type-key", "whole-type-value"
    ],
    httpx_mock: HTTPXMock,
    tmp_path: Path,
) -> None:
    """Ensure a proper error message occurs if the configs are malformed."""
    import json
    import re

    import yaml
    from pydantic import AnyHttpUrl

    from s7.exceptions import S7EntityError
    from s7.pydantic_models.datasource import parse_input_configs

    config_keys = ["dataresource", "function", "mapping", "parser"]

    bad_config_name = {"bad": "config"}
    bad_config_type_key = {2: "config"}
    bad_config_type_value = {next(iter(config_keys)): 2}
    bad_configs = {}.fromkeys(config_keys, bad_config_name)

    # Determine the error information based on the `configs_value_kind`
    if configs_value_kind in ("", "part"):
        error_info = (
            S7EntityError,
            rf"^The (\"|')({'|'.join(config_keys)})(\"|') configuration provided could "
            r"not be validated as a proper OTEAPI "
            rf"({'|'.join(_.capitalize() for _ in config_keys)})Config$",
        )
    elif configs_value_kind == "whole-name":
        # Here, we are providing `bad_config_name` and expect an error due to an
        # unsupported key name
        error_info = (
            ValueError,
            rf"^The config name {next(iter(bad_config_name))!r} is not a valid config "
            rf"name\. Valid config names are: {', '.join(sorted(config_keys))}$",
        )
    elif configs_value_kind == "whole-type-key":
        # Here, we are providing `bad_config_type_key` and expect an error due to an
        # unsupported key type
        error_info = (TypeError, r"^The config name must be a string$")
    elif configs_value_kind == "whole-type-value":
        # Here, we are providing `bad_config_type_value` and expect an error due to an
        # unsupported value type
        error_info = (
            TypeError,
            rf"^The (\"|')({'|'.join(config_keys)})(\"|') configuration provided is "
            rf"not a valid OTEAPI {'|'.join(_.capitalize() for _ in config_keys)}"
            rf"Config. Got type {int}$",
        )
    else:
        pytest.fail(f"Unexpected configs value kind: {configs_value_kind}")

    # Set source for all configs_type cases except for those starting with `dict_`
    if not configs_type.startswith("dict_"):
        assert configs_value_kind in (
            "part",
            "whole-name",
            "whole-type-key",
            "whole-type-value",
        )

        if configs_value_kind == "part":
            source = bad_configs
        elif configs_value_kind == "whole-name":
            source = bad_config_name
        elif configs_value_kind == "whole-type-key":
            source = bad_config_type_key
        else:
            source = bad_config_type_value

    # Prepare input according to configs_type
    if configs_type == "dict_dict":
        configs = bad_configs

    elif configs_type in ("dict_Path", "dict_str_path"):
        configs = {}
        for key, value in bad_configs.items():
            configs[key] = (tmp_path / f"{key}.yaml").resolve()
            configs[key].write_text(yaml.safe_dump(value), encoding="utf-8")

        if configs_type == "dict_str_path":
            configs = {key: str(value) for key, value in configs.items()}

    elif configs_type in ("dict_AnyHttpUrl", "dict_str_url"):
        # Mock HTTP GET call to retrieve the configs online
        httpx_mock.add_response(
            url=re.compile(r"^http://example\.org/.*"),
            method="GET",
            text=yaml.safe_dump(next(iter(bad_configs.values()))),
        )

        configs = {
            key: (
                AnyHttpUrl(f"http://example.org/{key}")
                if configs_type == "dict_AnyHttpUrl"
                else f"http://example.org/{key}"
            )
            for key in config_keys
        }

    elif configs_type in ("dict_str_json_dump", "dict_str_yaml_dump"):
        configs = {}
        for key, value in bad_configs.items():
            configs[key] = (
                json.dumps(value)
                if configs_type == "dict_str_json_dump"
                else yaml.safe_dump(value)
            )

    elif configs_type in ("Path", "str_path"):
        configs = tmp_path / "bad_configs.yaml"
        configs.write_text(yaml.safe_dump(source), encoding="utf-8")

        if configs_type == "str_path":
            configs = str(configs.resolve())

    elif configs_type in ("AnyHttpUrl", "str_url"):
        # Mock HTTP GET call to retrieve the configs online
        httpx_mock.add_response(
            url=re.compile(r"^http://example\.org/configs.*"),
            method="GET",
            text=yaml.safe_dump(source),
        )

        configs = (
            AnyHttpUrl("http://example.org/configs")
            if configs_type == "AnyHttpUrl"
            else "http://example.org/configs"
        )

    elif configs_type in ("str_json_dump", "str_yaml_dump"):
        configs = (
            json.dumps(source)
            if configs_type == "str_json_dump"
            else yaml.safe_dump(source)
        )

        # There's a special case here, which is for JSON.
        # JSON keys MUST be strings, so the serialization will always produce string
        # keys.
        # Therefore, for the `whole-type` case, we need to adjust the error message to
        # reflect this. Essentially, it will fail instead similarly to `whole-name`,
        # since "2" is not a valid key name.
        if configs_value_kind == "whole-type-key" and configs_type == "str_json_dump":
            error_info = (
                ValueError,
                r"^The config name '2' is not a valid config name\. Valid config names "
                rf"are: {', '.join(sorted(config_keys))}$",
            )

    else:
        pytest.fail(f"Unexpected configs type: {configs_type}")

    with pytest.raises(error_info[0], match=error_info[1]):
        parse_input_configs(configs)
