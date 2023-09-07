"""Entity store."""
import os
from urllib.parse import quote_plus

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure


class EntityExistsError(Exception):
    """Raised when an entity already exists."""


class MongoStore:
    """
    Storing soft entities
    """

    def __init__(self, client=None):
        if not client:
            uri = (
                "mongodb://"
                f"{quote_plus(os.getenv('MONGODB_USER'))}:"
                f"{quote_plus(os.getenv('MONGODB_PASSWORD'))}@"
                f"{quote_plus(os.getenv('MONGODB_HOST'))}:"
                f"{int(os.getenv('MONGODB_PORT', '27017'))}"
            )
            client = MongoClient(uri)
        try:
            client.admin.command("ismaster")
        except ConnectionFailure:
            print("Cannot connect to server")

        self._client = client
        self._db = self._client.soft
        self._coll = self._db.entities

    def __del__(self):
        self._client.close()

    def read(self, uriref=None):
        """Get an entity."""
        if not uriref:
            return [e["uri"] for e in self._coll.find({})]

        entity = self._coll.find_one({"uri": uriref}, {"_id": False})
        return entity

    def create(self, entity):
        """Insert an entity."""
        if "uri" not in entity:
            raise ValueError("entity does not contain a uri")
        uriref = entity["uri"]
        if self._coll.find_one({"uri": uriref}) is not None:
            raise EntityExistsError(
                f"Entity with uri: `{uriref}` already exists. Use update() to modify."
            )
        self._coll.insert_one(entity)

    def update(self, entity):
        """Replace an entity."""
        if "uri" not in entity:
            raise ValueError("entity does not contain a uri")
        uriref = entity["uri"]
        self._coll.replace_one({"uri": uriref}, entity)


class EntityStore:
    """Entity Store."""

    def __init__(self, client=None):
        self.store = MongoStore(client)

    def __enter__(self):
        return self.store

    def __exit__(self, exc_type, exc_val, exc_tb):
        del self.store
