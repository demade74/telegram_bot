import pymongo
import os
from urllib.parse import quote_plus

#mongo_url = os.getenv('MONGOLAB_URI', 'mongodb://localhost:27017')
client = pymongo.MongoClient(os.environ['MONGODB_URI'])
users_collection = client.users_places.users
