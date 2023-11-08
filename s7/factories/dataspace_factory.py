"""
Soft7 factory
"""


class BaseExt:
    """
    Base class
    """

    def __init__(self, uid=None):
        pass


def __class_factory(name, meta):
    """
    Factory function
    """
    attr = {}
    attr["uriref"] = meta["uri"]
    attr["properties"] = meta["properties"]

    def gen_getset(key):
        return lambda: property(
            lambda self: self.properties[key]["value"]
            if "value" in self.properties[key]
            else None,
            lambda self, value: self.properties[key].update({"value": value}),
            doc=meta["properties"][key]["description"]
            if "description" in meta["properties"][key]
            else None,
        )

    for key in meta["properties"]:
        attr[key] = gen_getset(key)()

    return type(name, (BaseExt,), attr)


def __dataspace_class_factory(name, meta, dataspace):
    database = dataspace.create_db(meta["uri"])

    def initializer(self, id=None):
        self.__dict__.update({"id": (database.document(id)).id})

    def generic_setter(self, key, value):
        database.document(self.id).update({key: value})

    attr = {
        "uriref": meta["uri"],
        "properties": meta["properties"],
        "__init__": initializer,
        "set_property": generic_setter,
    }

    def gen_dataspace_getset(database):
        return lambda key: lambda: property(
            lambda self: database.document(self.id).data[key]
            if key in database.document(self.id).data
            else None,
            lambda self, value: database.document(self.id).update({key: value}),
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
