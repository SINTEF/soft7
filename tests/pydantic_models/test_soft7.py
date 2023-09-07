"""Tests for `s7.pydantic_models.soft7`."""
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from typing import Union


@pytest.mark.parametrize(
    "type_string,py_type",
    (
        ("string", str),
        ("float", float),
        ("int", int),
        ("complex", complex),
        ("dict", dict),
        ("boolean", bool),
        ("bytes", bytes),
        ("bytearray", bytearray),
    ),
)
def test_property_type_enum_py_cls(type_string: str, py_type: type) -> None:
    """Check all returned types from `py_cls` can be initialized as expected."""
    from s7.pydantic_models.soft7 import SOFT7EntityPropertyType

    assert SOFT7EntityPropertyType(type_string).py_cls == py_type


def test_property_type_enum() -> None:
    """Check all enumerations have a valid `py_cls` value."""
    from s7.pydantic_models.soft7 import SOFT7EntityPropertyType

    for enum in SOFT7EntityPropertyType:
        assert enum.py_cls


def test_entity_shapes_and_dimensions(
    soft_entity_init: "dict[str, Union[str, dict]]",
) -> None:
    """Ensure the validator `shapes_and_dimensions` enforces the desired rules."""
    from s7.pydantic_models.soft7 import SOFT7Entity

    dimensions = {
        "N": "Number of elements.",
        "nsites": "Number of sites.",
        "cartesian": "Cartesian coordinates.",
    }
    properties = {
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
        "positions": {
            "type": "float",
            "shape": ["nsites", "cartesian"],
            "description": "Atomic positions.",
            "unit": "Å",
        },
    }
    soft_entity_init["dimensions"] = dimensions
    soft_entity_init["properties"] = properties

    SOFT7Entity(**soft_entity_init)
