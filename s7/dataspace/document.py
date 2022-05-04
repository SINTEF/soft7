"""
Simple in-memory document store
"""

class Document:
    """_summary_
    """
    def __init__(self, identity, data=None):
        self._id = identity
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
