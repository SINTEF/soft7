""" Unit tests """

from __future__ import annotations

import pytest


def test_soft7_collection_dimension():
    """Test"""
    from s7.pydantic_models.soft7_entity import SOFT7CollectionDimension

    dimension_data = {
        "description": "Test dimension",
        "minValue": 0,
        "maxValue": 10,
        "dimensionMapping": {"map1": "value1"},
    }
    dimension = SOFT7CollectionDimension(**dimension_data)
    assert dimension.description == "Test dimension"
    assert dimension.minValue == 0
    assert dimension.maxValue == 10
    assert dimension.dimensionMapping == {"map1": "value1"}


def test_soft7_collection_property():
    """Test"""
    from s7.pydantic_models.soft7_entity import (
        SOFT7CollectionProperty,
    )

    property_data = {
        "type": "string",
        "shape": ["dim1", "dim2"],
        "description": "Test property",
        "unit": "m/s",
    }
    prop = SOFT7CollectionProperty(**property_data)
    assert prop.type_ == "string"
    assert prop.shape == ["dim1", "dim2"]
    assert prop.description == "Test property"
    assert prop.unit == "m/s"


def test_soft7_collection():
    """Test"""
    from pydantic import AnyUrl

    from s7.pydantic_models.soft7_entity import SOFT7Collection

    collection_data = {
        "identity": "http://example.com/collection",
        "description": "Test collection",
        "dimensions": {"dim1": {"description": "Dimension 1"}},
        "properties": {
            "prop1": {
                "type": "string",
                "shape": ["dim1"],
                "description": "Property 1",
                "unit": "m",
            }
        },
        "$schemas": {
            "type1": {"schema1": {"properties": {"prop1": {"type": "string"}}}}
        },
    }
    collection = SOFT7Collection(**collection_data)
    assert collection.identity == AnyUrl("http://example.com/collection")
    assert collection.description == "Test collection"
    assert "dim1" in collection.dimensions
    assert "prop1" in collection.properties


def test_soft7_collection_invalid_ref():
    """Test"""
    from pydantic import ValidationError

    from s7.pydantic_models.soft7_entity import SOFT7Collection

    collection_data = {
        "identity": "http://example.com/collection",
        "description": "Test collection",
        "dimensions": {"dim1": {"description": "Dimension 1"}},
        "properties": {
            "prop1": {
                "type": {"$ref": "#/schemas/type1/invalid_schema"},
                "shape": ["dim1"],
                "description": "Property 1",
                "unit": "m",
            }
        },
        "$schemas": {
            "type1": {"schema1": {"properties": {"prop1": {"type": "string"}}}}
        },
    }
    with pytest.raises(ValidationError):
        SOFT7Collection(**collection_data)
