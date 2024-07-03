"""Tests for `s7.pydantic_models.soft7`."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


def test_entity_shapes_and_dimensions(
    soft_entity_init: dict[str, str | dict],
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

    assert soft_entity_init["dimensions"] and isinstance(
        soft_entity_init["dimensions"], dict
    )
    assert soft_entity_init["properties"] and isinstance(
        soft_entity_init["properties"], dict
    )

    soft_entity_init["dimensions"].update(additional_dimensions)
    soft_entity_init["properties"].update(additional_properties)

    SOFT7Entity(**soft_entity_init)
