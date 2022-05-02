from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from urllib.parse import quote_plus
import os

class MongoStore:
    """
    Storing soft entities
    """
    
    def __init__(self, client=None):        
        if not client:
            MONGODB_HOST = os.environ.get('MONGODB_HOST')
            MONGODB_PORT = int(os.environ.get('MONGODB_PORT', '27017'))
            MONGODB_USER = os.environ.get('MONGODB_USER')
            MONGODB_PASSWORD = os.environ.get('MONGODB_PASSWORD')

            uri = f"mongodb://{quote_plus(MONGODB_USER)}:{quote_plus(MONGODB_PASSWORD)}@{quote_plus(MONGODB_HOST)}:{MONGODB_PORT}"
            client = MongoClient(uri)
        try:
            client.admin.command('ismaster')
        except ConnectionFailure:
            print ("Cannot connect to server")
        
        self._client = client
        self._db = self._client.soft
        self._coll = self._db.entities
        
    def __del__(self):
        self._client.close()
        
    
    def read(self, uriref=None):
        if not uriref:
            return [e['uri'] for e in self._coll.find({})]
                    
        entity = self._coll.find_one({"uri": uriref}, {'_id': False})
        return entity
    
    
    def create(self, entity):
        assert 'uri' in entity
        uriref = entity['uri']
        if self._coll.find_one({"uri": uriref}) is not None:
            raise Exception(f"Entity with uri: `{uriref}` already exists. Use update() to modify.")
        self._coll.insert_one(entity)


    def update(self, entity):
        assert 'uri' in entity
        uriref = entity['uri']
        self._coll.replace_one({"uri": uriref}, entity)
        
class EntityStore:
    
    def __init__(self, client=None):
        self.store = MongoStore(client)
    
    def __enter__(self):
        return self.store
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        del self.store
        