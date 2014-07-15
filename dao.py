from pymongo import MongoClient
from bson.objectid import ObjectId

mongo_client = MongoClient('localhost')
players_col = mongo_client.players.players
tournaments_col = mongo_client.smashranks.tournaments

def get_all_players():
    return convert_player_id_list(players_col.find())

def get_player_by_id(player_id):
    return convert_player_id(players_col.find_one({'_id': ObjectId(player_id)}))

def get_player_by_name(name):
    return convert_player_id(players_col.find_one({'normalized_name': name.lower()}))

def get_player_by_alias(alias):
    return convert_player_id_list(players_col.find({'aliases': {'$in': [alias]}}))

def add_player(player):
    return players_col.insert(player)

def convert_player_id(player):
    if player is not None:
        player['id'] = str(player['_id'])
        del player['_id']

    return player

def convert_player_id_list(players):
    return [convert_player_id(player) for player in players]
