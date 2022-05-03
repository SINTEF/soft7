"""Database document."""


class Document:
    """Document."""

    def __init__(self, uid, data=None):
        self._uid = uid
        self._data = data

    def update(self, document):
        """Update document."""
        self.data.update(document)
        return self.data

    @property
    def uid(self):
        """Unique document id."""
        return self._uid

    @property
    def data(self):
        """Document data."""
        return self._data
