import os
import sys

from pymongo import MongoClient

# add root directory to python path
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../'))

from config.config import Config
from dao import Dao

# script to change users password
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "incorrect number of arguments!"
        print "usage: python change_passwd.py username password"
        sys.exit()

    username = sys.argv[1]
    password = sys.argv[2]
    config = Config()
    mongo_client = MongoClient(host=config.get_mongo_url())
    dao = Dao(None, mongo_client)

    if not dao.change_passwd(username, password):
        print "user not found! you done goofed"
    else:
        print "password updated sucessfully"
