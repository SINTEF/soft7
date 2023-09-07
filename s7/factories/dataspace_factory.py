"""
Soft7 factory
"""
# pylint: disable=unnecessary-lambda-assignment,unnecessary-direct-lambda-call
import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any


class BaseExt(metaclass=abc.ABCMeta):
    """
    Base class
    """

    def __init__(self, uid=None):
        pass


def __class_factory(name, meta):
    """
    Factory function
    """
    attr = {
        "uriref": meta["uri"],
        "properties": meta["properties"],
    }

    def gen_getset(key: str) -> property:
        def getter(self) -> "Any":
            return (
                self.properties[key]["value"]
                if "value" in self.properties[key]
                else None
            )

        def setter(self, value: "Any") -> None:
            self.properties[key].update({"value": value})

        def deleter(self) -> None:
            del self.properties[key]["value"]

        return property(
            getter,
            setter,
            deleter,
            doc=meta["properties"][key]["description"]
            if "description" in meta["properties"][key]
            else None,
        )

    def initializer(self, **kwargs: "Any") -> None:
        self.__dict__.update(
            {key: value for key, value in kwargs.items() if key in meta["properties"]}
        )

    attr["__init__"] = initializer

    for key in meta["properties"]:
        attr[key] = gen_getset(key)

    return type(name, (BaseExt,), attr)


def __dataspace_class_factory(name, meta, dataspace):
    database = dataspace.create_db(meta["uri"])
    initializer = (
        lambda __database: lambda self, id=None: self.__dict__.update(
            {"id": (__database.document(id)).id}
        )
    )(database)
    generic_setter = (
        lambda database: lambda self, key, value: (
            database.document(self.id).update({key: value})
        )
    )(database)
    attr = {
        "uriref": meta["uri"],
        "properties": meta["properties"],
        "__init__": initializer,
        "set_property": generic_setter,
    }

    gen_dataspace_getset = lambda database: lambda key: lambda: property(
        lambda self: database.document(self.id).data[key]
        if key in database.document(self.id).data
        else None,
        lambda self, value: (database.document(self.id).update({key: value})),
        doc=meta["properties"][key]["description"]
        if "description" in meta["properties"][key]
        else None,
    )

    gen_getset = gen_dataspace_getset(database)
    for key in meta["properties"]:
        attr[key] = gen_getset(key)()

    return type(name, (BaseExt,), attr)


def class_factory(name, meta, dataspace=None):
    """Public factory method."""
    if dataspace:
        return __dataspace_class_factory(name, meta, dataspace)
    return __class_factory(name, meta)
