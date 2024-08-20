"""Pytest fixtures for all tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any, Union


def static_folder() -> Path:
    """Path to the 'static' folder.

    This is here to support _generate_entity_test_cases() in
    tests/oteapi_plugin/test_soft7_function.py.
    """
    from pathlib import Path

    return Path(__file__).resolve().parent.resolve() / "static"


@pytest.fixture(name="static_folder")
def static_folder_fixture() -> Path:
    """Path to the 'static' folder."""
    path = static_folder()

    assert path.exists()
    assert path.is_dir()

    return path


@pytest.fixture
def soft_entity_init_source(static_folder: Path) -> Path:
    """Source to the SOFT7 entity YAML file used in the `soft_entity_init` fixture."""
    return static_folder / "soft_datasource_entity.yaml"


@pytest.fixture
def soft_entity_init(
    soft_entity_init_source: Path,
) -> dict[str, Union[str, dict[str, Any]]]:
    """A dict for initializing a `SOFT7Entity`."""
    import yaml

    assert soft_entity_init_source.exists()
    entity = yaml.safe_load(soft_entity_init_source.read_text(encoding="utf-8"))

    # entity should be parsed as a dict.
    assert isinstance(entity, dict)

    return entity


@pytest.fixture
def soft_datasource_entity_mapping_init(
    static_folder: Path,
) -> dict[str, dict[str, str] | list[tuple[str, str, str]]]:
    """A dict representing a mapping used for a SOFT7DataSource based on the
    `SOFT7Entity` given in the `soft_entity_init()` fixture."""
    return {
        "prefixes": {
            "data_source": (
                f"{(static_folder / 'soft_datasource_content.yaml').as_uri()}#"
            ),
            "s7_entity": "http://onto-ns.com/s7/0.1.0/MolecularSpecies#",
        },
        "triples": [
            # Properties
            ("data_source:properties.atom", "", "s7_entity:properties.atom"),
            ("data_source:properties.electrons", "", "s7_entity:properties.electrons"),
            ("data_source:properties.mass", "", "s7_entity:properties.mass"),
            ("data_source:properties.radius", "", "s7_entity:properties.radius"),
            # Dimensions
            ("data_source:dimensions.N", "", "s7_entity:dimensions.N"),
        ],
    }


@pytest.fixture
def soft_datasource_init(static_folder: Path) -> dict[str, Any]:
    """A dict representating data source content."""
    import yaml

    def _list_to_tuple(value: Any) -> tuple[Any, ...]:
        """Convert a list to a tuple."""
        if isinstance(value, list):
            return tuple(_list_to_tuple(_) for _ in value)
        return value

    test_data_path = static_folder / "soft_datasource_content.yaml"
    assert test_data_path.exists()
    test_data = yaml.safe_load(test_data_path.read_text(encoding="utf-8"))

    # test_data should be parsed as a dict.
    assert isinstance(test_data, dict)

    # "properties" should exist and be a non-empty dict.
    assert "properties" in test_data
    assert isinstance(test_data["properties"], dict)
    assert test_data["properties"]

    # Convert all property values to the correct type.
    for property_name, property_value in list(test_data["properties"].items()):
        test_data["properties"][property_name] = _list_to_tuple(property_value)

    return test_data


@pytest.fixture
def soft_instance_data_source(static_folder: Path) -> Path:
    """Source to the SOFT7 instance data YAML file used in the `soft_instance_data`
    fixture.
    """
    return static_folder / "soft_datasource_entity_test_data.yaml"


@pytest.fixture
def soft_instance_data(soft_instance_data_source: Path) -> dict[str, dict[str, Any]]:
    """A dict for initializing a `SOFT7Instance` based on the entity expressed in the
    `soft_entity_init` fixture."""
    import yaml

    assert soft_instance_data_source.exists()
    instance_data = yaml.safe_load(
        soft_instance_data_source.read_text(encoding="utf-8")
    )

    # instance_data should be parsed as a dict.
    assert isinstance(instance_data, dict)

    return instance_data


@pytest.fixture
def soft_datasource_configs(
    static_folder: Path,
    soft_entity_init: dict[str, Union[str, dict[str, Any]]],
    soft_datasource_entity_mapping_init: dict[
        str, dict[str, str] | list[tuple[str, str, str]]
    ],
) -> dict[str, dict[str, Any]]:
    """A dict representing the configurations for a SOFT7DataSource."""
    from s7.pydantic_models.oteapi import default_soft7_ote_function_config

    return {
        "dataresource": {
            "resourceType": "resource/url",
            "downloadUrl": (static_folder / "soft_datasource_content.yaml").as_uri(),
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
        "function": default_soft7_ote_function_config(
            soft_entity_init["identity"]
        ).model_dump(mode="json"),
    }
