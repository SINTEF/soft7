<<<<<<< HEAD
"""
"""
from soft.dataspace.document import Document
from uuid import uuid4

class Database:
=======
"""Dataspace database."""
from uuid import uuid4

from s7.dataspace.document import Document


class Database:
    """Database."""

>>>>>>> bf69cfe680c985e705fd79370dbf59f21b0b4871
    def __init__(self, name):
        self._name = name
        self._documents = {}

<<<<<<< HEAD

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
=======
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
>>>>>>> bf69cfe680c985e705fd79370dbf59f21b0b4871
