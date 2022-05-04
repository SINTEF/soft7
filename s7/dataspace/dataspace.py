"""
Soft7 dataspace
"""
from s7.dataspace.database import Database

# from s7.storagestrategy import Context, Strategy


class Dataspace:
    """Data space."""

    def __init__(self, strategy):
        self._databases = {}
        self._context = strategy

    def create_db(self, database):
        """Create/Add a new database."""
        if database in self._databases:
            raise ValueError(f"{database} already in known databases.")
        new_database = Database(database)
        self._databases[database] = new_database
        return new_database

    def database(self, database):
        """Return a database."""
        if database not in self._databases:
            raise ValueError(f"{database} not found in known databases.")
        return self._databases[database]

    def push(self):
        """
        Store all current data to a storage strategy
        """
        self._context.write(self._databases)

    def pull(self):
        """
        Retrieve data from a storage strategy
        """
        self._databases = {}
        self._context.read(self._databases)

    @property
    def databases(self):
        """Get all databases."""
        return list(self._databases)
