# change users password
from pymongo import MongoClient, DESCENDING
from config.config import Config
from sys import argv
import hashlib
from model import User
from dao import USERS_COLLECTION_NAME, DATABASE_NAME, ITERATION_COUNT
import base64


if __name__ == "__main__":
	if len(argv) != 3:
		print "incorrect number of arguments!"
		print "usage: python change_passwd.py username password"
	username = argv[1]
	password = argv[2]
	config = Config()
	mongo_client = MongoClient(host=config.get_mongo_url())


	salt = base64.b64encode(os.urandom(16)) #more bytes of randomness? i think 16 bytes is sufficient for a salt

	hashed_password = base64.b64encode(hashlib.pbkdf2_hmac('sha256', password, salt, ITERATION_COUNT))
	users_col = mongo_client[database_name][USERS_COLLECTION_NAME]

	# modifies the users password, or returns None if it couldnt find the user
	if not users_col.find_and_modify(query={'username': username}, update={"$set": {'hashed_password': hashed_password, 'salt': salt}}):
		print "user not found! you done goofed"
	else:
		print "password updated sucessfully"
	return