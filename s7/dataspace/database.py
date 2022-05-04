"""Dataspace database."""
from uuid import uuid4

from s7.dataspace.document import Document


class Database:
    """Database."""

    def __init__(self, name):
        self._name = name
        self._documents = {}

    def insert(self, document=None, uid=None):
        """Insert a document."""
        if uid is None:
            uid = str(uuid4())
        self._documents[uid] = Document(uid, data=document if document else {})
        return self._documents[uid]

    def document(self, uid):
        """Get a document."""
        if uid is None:
            return self.insert()
        if not uid in self._documents:
            return self.insert(uid=uid)

        return self._documents[uid]

    @property
    def name(self):
        """Name of database."""
        return self._name

    @property
    def documents(self):
        """All documents in database."""
        return list(self._documents)
