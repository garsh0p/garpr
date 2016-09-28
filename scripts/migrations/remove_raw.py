import os
import sys

from bson.objectid import ObjectId
from pymongo import MongoClient

# add root directory to python path
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../../'))

from config.config import Config
import model as M

config = Config()
mongo_client = MongoClient(host=config.get_mongo_url())

DATABASE_NAME = config.get_db_name()

TOURNAMENTS_COLLECTION_NAME = 'tournaments'
PENDING_TOURNAMENTS_COLLECTION_NAME = 'pending_tournaments'
RAW_FILES_COLLECTION_NAME = 'raw_files'

tournaments_col = mongo_client[DATABASE_NAME][TOURNAMENTS_COLLECTION_NAME]
pending_tournaments_col = mongo_client[DATABASE_NAME][PENDING_TOURNAMENTS_COLLECTION_NAME]
raw_files_col = mongo_client[DATABASE_NAME][RAW_FILES_COLLECTION_NAME]

for t in tournaments_col.find():
    if 'raw' in t:
        raw_data = unicode(t['raw'])

        raw_file = {'_id': ObjectId(),
                    'data': raw_data}
        raw_files_col.insert(raw_file)

        del t['raw']
        t['raw_id'] = raw_file['_id']

        tournaments_col.update({'_id': t['_id']}, t)

for pt in pending_tournaments_col.find():
    if 'raw' in pt:
        raw_data = unicode(pt['raw'])

        raw_file = {'_id': ObjectId(),
                    'data': raw_data}
        raw_files_col.insert(raw_file)

        del pt['raw']
        pt['raw_id'] = raw_file['_id']

        pending_tournaments_col.update({'_id': pt['_id']}, pt)
