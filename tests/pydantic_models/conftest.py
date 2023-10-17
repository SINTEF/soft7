"""Pytest fixtures for `pydantic_models`."""
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from typing import Union


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
