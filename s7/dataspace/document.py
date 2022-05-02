"""
"""

class Document:
    def __init__(self, id, data=None):
        self._id = id
        self._data = data        

    def update(self, document):
        self.data.update(document)
        return self.data
    
    @property
    def id(self):
        return self._id
    
    @property
    def data(self):
        return self._data