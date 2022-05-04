"""
Soft7 dataspace
"""
import uuid
from soft.storagestrategy import Context, Strategy
from soft.dataspace.database import Database

class Dataspace:
    """_summary_
    The S7 dataspace orchestrates databases for object state management.

    """
    def __init__(self, strategy: Strategy):
        self._databases = {}
        self._context = Context(strategy)


    def create_db(self, database):
        if database in self._databases:
            raise RuntimeError('Database already created')

        db = Database(database)
        self._databases[database] = db
        return db


    def database(self, database):
        """_summary_

        Args:
            database (_type_): _description_

        Raises:
            RuntimeError: _description_

        Returns:
            _type_: _description_
        """
        if not database in self._databases:
            raise RuntimeError('Database not created')

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


    def set_strategy(self, strategy: Strategy):
        self._context = Context(strategy)

    @property
    def databases(self):
        return [key for key in self._databases]
