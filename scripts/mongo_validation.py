import os
import sys

from pymongo import MongoClient

# add root directory to python path
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../'))

from config.config import Config
from dao import Dao
from model import Player, Tournament

# script for making sure stuff in db conforms to description in model.py
def mongo_validate():
    config = Config()
    mongo_client = MongoClient(host=config.get_mongo_url())
    dao = Dao(None, mongo_client)

    # validate players
    print 'Validating players...'
    for player_data in dao.players_col.find():
        player = Player.from_json(player_data)
        dao.players_col.update({'_id': player.id}, player.get_json_dict())

    # validate tournaments
    print 'Validating tournaments...'
    for tournament_data in dao.tournaments_col.find():
        tournament = Tournament.from_json(tournament_data)
        dao.tournaments_col.update({'_id': tournament.id}, tournament.get_json_dict())


if __name__ == "__main__":
    mongo_validate()
