import os
import sys

from pymongo import MongoClient

# add root directory to python path
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../'))

from config.config import Config
from dao import Dao

# script to list all users in db
if __name__ == "__main__":
    config = Config()
    mongo_client = MongoClient(host=config.get_mongo_url())
    dao = Dao(None, mongo_client)

    users = dao.get_all_users()
    for user in users:
        print user
