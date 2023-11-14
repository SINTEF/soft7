"""Pytest fixtures for all tests."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any


@pytest.fixture
def static_folder() -> Path:
    """Path to the 'static' folder."""
    from pathlib import Path

    path = Path(__file__).resolve().parent.resolve() / "static"
    assert path.exists() and path.is_dir()
    return path


@pytest.fixture
def soft_entity_init() -> dict[str, str | dict]:
    """A dict for initializing a `SOFT7Entity`."""
    return {
        "identity": "https://onto-ns.com/s7/0.1.0/temperature",
        "description": "A bare-bones entity for testing.",
        "dimensions": {"N": "Number of elements."},
        "properties": {
            "atom": {
                "type": "string",
                "shape": ["N"],
                "description": "An atom.",
            },
            "electrons": {
                "type": "int",
                "shape": ["N"],
                "description": "Number of electrons.",
            },
            "mass": {
                "type": "float",
                "shape": ["N"],
                "description": "Atomic mass.",
                "unit": "amu",
            },
            "radius": {
                "type": "float",
                "shape": ["N"],
                "description": "Atomic radius.",
                "unit": "Å",
            },
        },
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
