"""Tests for the DataSpace factory module."""


def test_class_factory() -> None:
    """Test __class_factory()"""
    from s7.factories.dataspace_factory import BaseExt, __class_factory

    meta = {
        "uri": "http://example.com/uri",
        "properties": {
            "name": {"type": "string", "description": "The name of the DataSpace"},
            "description": {
                "type": "string",
                "description": "The description of the DataSpace",
            },
        },
    }
    name = "Test"
    cls = __class_factory(name, meta)

    # Test class
    assert issubclass(cls, BaseExt)
    assert cls.__name__ == name
    assert cls.__bases__[0] == BaseExt

    # Test class attributes
    assert cls.uriref == meta["uri"]
    assert cls.properties == meta["properties"]
    assert cls.name.__doc__ == meta["properties"]["name"]["description"]
    assert cls.description.__doc__ == meta["properties"]["description"]["description"]

    # Test getter and setter
    instance = cls()
    assert instance.name == None
    instance.name = "test"
    assert instance.name == "test"
    assert instance.description == None
    instance.description = "test"
    assert instance.description == "test"

    pre_filled_instance = cls(name="test", description="test")
    assert pre_filled_instance.name == "test"
    assert pre_filled_instance.description == "test"
