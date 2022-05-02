"""
"""
from soft.dataspace.document import Document
from uuid import uuid4

class Database:
    def __init__(self, name):
        self._name = name
        self._documents = {}        
    
    
    def insert(self, document=None, id=None):
        if id is None:
            id = str(uuid4())
        self._documents[id] = Document(id, data=document if document else {})
        return self._documents[id]
    
    
    def document(self, id):
        if id is None:
            return self.insert()
        if not id in self._documents:
            return self.insert(id=id)
        
        return self._documents[id]


    @property
    def name(self):
        return self._name


    @property
    def documents(self):
        return [key for key in self._documents]
