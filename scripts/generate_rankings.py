from dao import Dao
from pymongo import MongoClient
import rankings

mongo_client = MongoClient('localhost')
regions = Dao.get_all_regions(mongo_client)
for region in regions:
    d = Dao(region.id, mongo_client)
    rankings.generate_ranking(d)
