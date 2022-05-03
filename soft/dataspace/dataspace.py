"""
Soft7 dataspace
"""
import uuid
from soft.storagestrategy import Context, Strategy
from soft.dataspace.database import Database

class Dataspace:
    def __init__(self, strategy: Strategy):
        self._databases = {}
        self._context = Context(strategy)
        
        
    def create_db(self, database):
        assert database not in self._databases
        db = Database(database)
        self._databases[database] = db
        return db
    
    
    def database(self, database):
        assert database in self._databases
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
        
