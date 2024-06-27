"""Tests for `s7.pydantic_models.soft7_entity`."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from typing import Union


def test_entity_shapes_and_dimensions(
    soft_entity_init: dict[str, Union[str, dict]],
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

    assert soft_entity_init["dimensions"]
    assert isinstance(soft_entity_init["dimensions"], dict)

    assert soft_entity_init["properties"]
    assert isinstance(soft_entity_init["properties"], dict)

    soft_entity_init["dimensions"].update(additional_dimensions)
    soft_entity_init["properties"].update(additional_properties)

    SOFT7Entity(**soft_entity_init)


def test_soft7_entity_property():
    """Test"""
    from s7.pydantic_models.soft7_entity import SOFT7EntityProperty

    property_data = {
        "type": "string",
        "shape": ["dim1", "dim2"],
        "description": "Test property",
        "unit": "m/s",
    }
    prop = SOFT7EntityProperty(**property_data)
    assert prop.type == "string"
    assert prop.shape == ["dim1", "dim2"]
    assert prop.description == "Test property"
    assert prop.unit == "m/s"


def test_soft7_entity_property_invalid_type():
    """Test"""
    from pydantic import ValidationError

    from s7.pydantic_models.soft7_entity import SOFT7EntityProperty

    property_data = {
        "type": "invalid_type",
        "shape": ["dim1", "dim2"],
        "description": "Test property",
        "unit": "m/s",
    }
    with pytest.raises(ValidationError):
        SOFT7EntityProperty(**property_data)


def test_soft7_entity():
    """Test"""
    from pydantic import AnyUrl

    from s7.pydantic_models.soft7_entity import SOFT7Entity

    entity_data = {
        "identity": "http://example.com/entity",
        "description": "Test entity",
        "dimensions": {"dim1": "Dimension 1", "dim2": "Dimension 2"},
        "properties": {
            "prop1": {
                "type": "string",
                "shape": ["dim1"],
                "description": "Property 1",
                "unit": "m",
            }
        },
    }
    entity = SOFT7Entity(**entity_data)
    assert entity.identity == AnyUrl("http://example.com/entity")
    assert entity.description == "Test entity"
    assert entity.dimensions == {"dim1": "Dimension 1", "dim2": "Dimension 2"}
    assert "prop1" in entity.properties


def test_soft7_entity_empty_properties():
    """Test"""
    from pydantic import ValidationError

    from s7.pydantic_models.soft7_entity import SOFT7Entity

    entity_data = {
        "identity": "http://example.com/entity",
        "description": "Test entity",
        "dimensions": {"dim1": "Dimension 1", "dim2": "Dimension 2"},
        "properties": {},
    }
    with pytest.raises(ValidationError):
        SOFT7Entity(**entity_data)


def test_soft7_entity_private_property():
    """Test"""
    from pydantic import ValidationError

    from s7.pydantic_models.soft7_entity import SOFT7Entity

    entity_data = {
        "identity": "http://example.com/entity",
        "description": "Test entity",
        "dimensions": {"dim1": "Dimension 1", "dim2": "Dimension 2"},
        "properties": {
            "_private_prop": {
                "type": "string",
                "shape": ["dim1"],
                "description": "Private Property",
                "unit": "m",
            }
        },
    }
    with pytest.raises(ValidationError):
        SOFT7Entity(**entity_data)


def test_soft7_entity_shape_and_dimensions_mismatch():
    """Test"""
    from pydantic import ValidationError

    from s7.pydantic_models.soft7_entity import SOFT7Entity

    entity_data = {
        "identity": "http://example.com/entity",
        "description": "Test entity",
        "dimensions": {"dim1": "Dimension 1"},
        "properties": {
            "prop1": {
                "type": "string",
                "shape": ["dim1", "dim2"],
                "description": "Property 1",
                "unit": "m",
            }
        },
    }
    with pytest.raises(ValidationError):
        SOFT7Entity(**entity_data)
