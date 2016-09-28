import os
import sys

from pymongo import MongoClient

# add root directory to python path
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../'))

from config.config import Config
from dao import Dao

# script to create new user in db
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "incorrect number of arguments!"
        print "usage: python create_region.py region_name"
        sys.exit()

    region_name = sys.argv[1]

    config = Config()
    mongo_client = MongoClient(host=config.get_mongo_url())
    dao = Dao(None, mongo_client)
    if dao.create_region(region_name, region_name):
        print "region created:", region_name
