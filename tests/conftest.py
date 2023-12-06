"""Pytest fixtures for all tests."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any


def static_folder() -> Path:
    """Path to the 'static' folder."""
    from pathlib import Path

    path = Path(__file__).resolve().parent.resolve() / "static"
    return path


@pytest.fixture(name="static_folder")
def static_folder_fixture() -> Path:
    """Path to the 'static' folder."""
    path = static_folder()
    assert path.exists() and path.is_dir()
    return path


@pytest.fixture
def soft_entity_init(static_folder: Path) -> dict[str, str | dict]:
    """A dict for initializing a `SOFT7Entity`."""
    import yaml

    entity_path = static_folder / "soft_datasource_entity.yaml"
    assert entity_path.exists()
    entity = yaml.safe_load(entity_path.read_text(encoding="utf-8"))

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
    assert (
        "properties" in test_data
        and isinstance(test_data["properties"], dict)
        and test_data["properties"]
    )

    # Convert all property values to the correct type.
    for property_name, property_value in list(test_data["properties"].items()):
        test_data["properties"][property_name] = _list_to_tuple(property_value)

    return test_data
