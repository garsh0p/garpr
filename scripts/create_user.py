from pymongo import MongoClient, DESCENDING
from config.config import Config
from sys import argv
import hashlib
from model import User
from dao import USERS_COLLECTION_NAME, DATABASE_NAME, ITERATION_COUNT
import base64


if __name__ == "__main__":
	if len(argv) < 4:
		print "incorrect number of arguments!"
		print "usage: python create_user.py username password region1 [region2] [region3]...."
	username = argv[1]
	password = argv[2]
	regions =  argv[3:]
	config = Config()
	mongo_client = MongoClient(host=config.get_mongo_url())

	#TODO: validate regions all exist

	salt = base64.b64encode(os.urandom(16)) #more bytes of randomness? i think 16 bytes is sufficient for a salt

	hashed_password = base64.b64encode(hashlib.pbkdf2_hmac('sha256', password, salt, ITERATION_COUNT))
	the_user = User(id=None, regions, username, salt, hashed_password)
	users_col = mongo_client[database_name][USERS_COLLECTION_NAME]

	# let's validate that no user exists currently
	if users_col.find_one({'username': username}):
		print "already a user with that username in the db, exiting"
		return
		
	users_col.insert(the_user.get_json_dict())


