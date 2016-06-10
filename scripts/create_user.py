import os
import sys

from pymongo import MongoClient

# add root directory to python path
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../'))

from config.config import Config
from dao import Dao

# script to create new user in db
if __name__ == "__main__":
    if len(sys.argv) < 4:
        print "incorrect number of arguments!"
        print "usage: python create_user.py username password region1 [region2] [region3]...."
        sys.exit()

    username = sys.argv[1]
    password = sys.argv[2]
    regions =  sys.argv[3:]

    config = Config()
    mongo_client = MongoClient(host=config.get_mongo_url())
    dao = Dao(None, mongo_client)
    if dao.create_user(username, password, regions):
        print "user created:", username
