"""Pytest fixtures for all tests."""
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from typing import Union, Any


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
def soft_datasource_init() -> "dict[str, Any]":
    return {
        "dimensions": {"N": 5},
        "properties": {
            "atom": ["Si", "Al", "O", "Cu", "Co"],
            "electrons": [14, 13, 8, 29, 27],
            "mass": [28.085, 26.982, 15.999, 63.546, 58.933],
            "radius": [1.10, 1.25, 0.6, 1.35, 1.35],
        },
    }
