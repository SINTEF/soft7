""" Unit tests """

from __future__ import annotations

import pytest
from pydantic import AnyUrl, ValidationError

from s7.pydantic_models.soft7_entity import (
    SOFT7Collection,
    SOFT7CollectionDimension,
    SOFT7CollectionProperty,
    SOFT7Entity,
    SOFT7EntityProperty,
)


def test_soft7_entity_property():
    """Test"""
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


def test_soft7_collection_dimension():
    """Test"""
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
