from dao import Dao
from pymongo import MongoClient
import rankings
from config.config import Config

config = Config()
mongo_client = MongoClient(config.get_mongo_url())
regions = Dao.get_all_regions(mongo_client)
for region in regions:
    d = Dao(region.id, mongo_client)
    rankings.generate_ranking(d)
