import pymongo
import os

client = pymongo.MongoClient(os.environ['MONGODB_URI'])
users_collection = client.users_places.users
