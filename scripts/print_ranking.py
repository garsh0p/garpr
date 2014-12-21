from model import *
from dao import Dao
from config.config import Config
from pymongo import MongoClient

config = Config()
mongo_client = MongoClient(host=config.get_mongo_url())

dao = Dao('newzealand', mongo_client=mongo_client)

rank = dao.get_latest_ranking()

for entry in rank.ranking:
	print(dao.get_player_by_id(entry.player).name, entry.rank, entry.rating)
