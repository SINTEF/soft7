"""
Soft7 factory
"""
import uuid
import pandas as pd
import abc

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
    attr = {}
    attr["uriref"] = meta['uri']
    attr["properties"] = meta['properties']
    gen_getset = lambda key: \
        lambda: property(
            lambda self: self.properties[key]["value"] if "value" in self.properties[key] else None,
            lambda self, value: self.properties[key].update({"value": value}), 
            doc=meta['properties'][key]["description"] if "description" in meta['properties'][key] else None)
    
    for key in meta['properties']:
        attr[key] = gen_getset(key)()

    return type(name, (BaseExt, ), attr)

def __dataspace_class_factory(name, meta, dataspace):
    db = dataspace.create_db(meta['uri'])
    initializer = (lambda __db: lambda self, id=None: self.__dict__.update({'id': (__db.document(id)).id}))(db)
    generic_setter = (lambda db: lambda self, key, value: (db.document(self.id).update({key: value})))(db)
    attr = dict(
        uriref = meta['uri'],
        properties = meta['properties'],
        __init__=initializer,
        set_property=generic_setter
    )

    
    
    gen_dataspace_getset = \
        lambda db: \
            lambda key: \
                lambda: property(lambda self: db.document(self.id).data[key] if key in db.document(self.id).data else None,
                                 lambda self, value: (db.document(self.id).update({key: value})),
                                 doc = meta['properties'][key]["description"] if "description" in meta['properties'][key] else None)

    
    gen_getset = gen_dataspace_getset(db)
    for key in meta['properties']:
        attr[key] = gen_getset(key)()
    
    
        
    return type(name, (BaseExt, ), attr)

def class_factory(name, meta, dataspace=None):
    if dataspace:
        return __dataspace_class_factory(name, meta, dataspace)
    return __class_factory(name, meta)