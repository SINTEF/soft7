"""Pytest fixtures for all tests."""
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any, Union


@pytest.fixture
def static_folder() -> "Path":
    """Path to the 'static' folder."""
    from pathlib import Path

    path = Path(__file__).resolve().parent.resolve() / "static"
    assert path.exists() and path.is_dir()
    return path


@pytest.fixture
def soft_entity_init() -> "dict[str, Union[str, dict]]":
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
def soft_datasource_init(static_folder: "Path") -> "dict[str, Any]":
    """A dict representating data source content."""
    import yaml

    test_data_path = static_folder / "soft_datasource_content.yaml"
    assert test_data_path.exists()
    test_data = yaml.safe_load(test_data_path.read_text(encoding="utf-8"))
    assert isinstance(test_data, dict)
    return test_data
