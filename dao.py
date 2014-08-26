from pymongo import MongoClient
from pymongo.son_manipulator import SONManipulator
from bson.objectid import ObjectId
from model import *
import trueskill

DEFAULT_RATING = TrueskillRating()

mongo_client = MongoClient('localhost')
players_col = mongo_client.smashranks.players
tournaments_col = mongo_client.smashranks.tournaments

# TODO update passed in model objects when doing an update?

def get_player_by_id(id):
    '''id must be an ObjectId'''
    return Player.from_json(players_col.find_one({'_id': id}))

def get_player_by_alias(alias):
    '''Converts alias to lowercase'''
    return Player.from_json(players_col.find_one({'aliases': {'$in': [alias.lower()]}}))

def get_all_players():
    '''Sorts by lexographical order'''
    return [Player.from_json(p) for p in players_col.find().sort([('name', 1)])]

def add_player(player):
    return players_col.insert(player.get_json_dict())

def delete_player(player):
    return players_col.remove({'_id': player.id})

def update_player(player):
    return players_col.update({'_id': player.id}, player.get_json_dict())

def get_excluded_players():
    return [Player.from_json(p) for p in players_col.find({'exclude': True})]

def exclude_player(player):
    return players_col.update({'_id': player.id}, {'$set': {'exclude': True}})

def include_player(player):
    return players_col.update({'_id': player.id}, {'$set': {'exclude': False}})

def add_alias_to_player(player, alias):
    lowercase_alias = alias.lower()
    if not lowercase_alias in player.aliases:
        player.aliases.append(lowercase_alias)

    return update_player(player)

def update_player_name(player, name):
    # ensure this name is already an alias
    if not name.lower() in player.aliases:
        raise Exception('Player %s does not have %s as an alias already, cannot change name.' % (player, name))

    player.name = name
    return update_player(player)

def merge_players_with_aliases(aliases, alias_to_merge_to):
    check_alias_uniqueness()
    
    if alias_to_merge_to in aliases:
        raise Exception("Cannot merge a player with itself! Alias to merge into: %s. Aliases to merge: %s." 
                        % (alias_to_merge_to, aliases))

    # TODO get a list of players here
    aliases_to_add = set()
    for alias in aliases:
        player = get_player_by_alias(alias)
        aliases_to_add.update(set(player.aliases))
        delete_player(player)

    player_to_update = get_player_by_alias(alias_to_merge_to)
    for alias in aliases_to_add:
        add_alias_to_player(player_to_update, alias)

    # sanity check after merging
    check_alias_uniqueness()

def reset_all_player_ratings():
    return players_col.update({}, {'$set': {'rating': DEFAULT_RATING.get_json_dict()}}, multi=True)

def insert_tournament(tournament):
    return tournaments_col.insert(tournament)

def update_tournament(tournament):
    return tournaments_col.update({'_id': tournament.id}, tournament.get_json_dict())

def get_all_tournaments():
    return [Tournament.from_json(t) for t in tournaments_col.find().sort([('date', 1)])]

def replace_player_in_tournament(tournament, player_to_remove, player_to_add):
    tournament.replace_player(player_to_remove, player_to_add)
    update_tournament(tournament)

def check_alias_uniqueness():
    '''Makes sure that each alias only refers to 1 player'''
    players = get_all_players()
    for player in players:
        for alias in player.aliases:
            print "Checking %s" % alias
            players_matching_alias = _get_players_by_alias(alias)
            if len(players_matching_alias) > 1:
                raise Exception("%s matches the following players: %s" % (alias, players_matching_alias))
            
def _get_players_by_alias(alias):
    '''Converts alias to lowercase'''
    return [Player.from_json(p) for p in players_col.find({'aliases': {'$in': [alias.lower()]}})]
