# /usr/bin/env python3

import json
import pymongo
from pymongo import errors
import configparser
import sys

###read configuration file
config = configparser.ConfigParser()
config.read('../NECKAr.cfg')
host = config.get('Database', 'host') # -> "Python is fun!"
port = config.getint('Database', 'port') # -> "%(bar)s is %(baz)s!"
db = config.get('Database', 'db_dump')
collection = config.get('Database', 'collection_dump')
json_file = config.get('Dump', 'json_file')

#connection to db
print("NECKAR: WD2DB: connecting to MongoDB")
try:
    client = pymongo.MongoClient(host,port)
except errors.ConnectionFailure:
        print("Connection to the database cannot be made. Plase check the config file")

db = client[db]
collection = db[collection]


print("NECKAR: WD2DB: inserting WD items")
with open(json_file) as input_file:
     for line in input_file:
         if len(line) > 2 and not line.startswith("["):
             line = line.strip(",\n")
         else:
             continue

         json_data = json.loads(line)
         collection.insert_one(json_data)

print("NECKAR: WD2DB: creating indices")
collection.create_index([('claims.P31.mainsnak.datavalue.value.numeric-id', pymongo.ASCENDING)])
collection.create_index([('en_sitelink', pymongo.ASCENDING)])
collection.create_index([('de_sitelink', pymongo.ASCENDING)])
collection.create_index([('type', pymongo.ASCENDING)])
collection.create_index([('id', pymongo.ASCENDING)])

print("NECKAR: WD2DB: DONE")