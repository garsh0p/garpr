from pymongo import MongoClient
from bson.objectid import ObjectId
from model import Player

mongo_client = MongoClient('localhost')
players_col = mongo_client.smashranks.players
tournaments_col = mongo_client.smashranks.tournaments


def get_player_by_alias(alias):
    '''Converts alias to lowercase'''
    return Player.from_json(players_col.find_one({'aliases': {'$in': [alias.lower()]}}))

def add_player(player):
    return players_col.insert(player.get_json_dict())

def add_alias_to_player(player, alias):
    return players_col.update({'_id': player.id}, {'$push': {'aliases': alias.lower()}})

def insert_tournament(tournament):
    return tournaments_col.insert(tournament)

