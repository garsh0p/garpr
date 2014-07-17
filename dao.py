from pymongo import MongoClient
from pymongo.son_manipulator import SONManipulator
from bson.objectid import ObjectId
from model import Player, MatchResult, Tournament

DEFAULT_RATING = 1200

mongo_client = MongoClient('localhost')
players_col = mongo_client.smashranks.players
tournaments_col = mongo_client.smashranks.tournaments

# TODO update passed in model objects when doing an update?

def get_player_by_alias(alias):
    '''Converts alias to lowercase'''
    return Player.from_json(players_col.find_one({'aliases': {'$in': [alias.lower()]}}))

def get_players_by_alias(alias):
    '''Converts alias to lowercase'''
    return [Player.from_json(p) for p in players_col.find({'aliases': {'$in': [alias.lower()]}})]

def get_all_players():
    return [Player.from_json(p) for p in players_col.find().sort([('name', 1)])]

def get_all_players_by_rating():
    return [Player.from_json(p) for p in players_col.find().sort([('rating', -1)])]

def add_player(player):
    return players_col.insert(player.get_json_dict())

# TODO use $addToSet
def add_alias_to_player(player, alias):
    return players_col.update({'_id': player.id}, {'$push': {'aliases': alias.lower()}})

def delete_player(player):
    return players_col.remove({'_id': player.id})

def update_player_name(player, name):
    # ensure this name is already an alias
    if not name.lower() in player.aliases:
        raise Exception('Player %s does not have %s as an alias already, cannot change name.' % (player, name))

    player.name = name
    return players_col.update({'_id': player.id}, {'$set': {'name': player.name}})

def update_player_rating(player, rating):
    return players_col.update({'_id': player.id}, {'$set': {'rating': rating}})

def merge_players_with_aliases(aliases, alias_to_merge_to):
    check_alias_uniqueness()
    
    if alias_to_merge_to in aliases:
        raise Exception("Cannot merge a player with itself! Alias to merge into: %s. Aliases to merge: %s." 
                        % (alias_to_merge_to, aliases))

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

def insert_tournament(tournament):
    return tournaments_col.insert(tournament)

def get_all_tournaments():
    return [Tournament.from_json(t) for t in tournaments_col.find().sort([('date', 1)])]

def reset_all_player_ratings():
    return players_col.update({}, {'$set': {'rating': DEFAULT_RATING}}, multi=True)

def check_alias_uniqueness():
    '''Makes sure that each alias only refers to 1 player'''
    players = get_all_players()
    for player in players:
        for alias in player.aliases:
            print "Checking %s" % alias
            players_matching_alias = get_players_by_alias(alias)
            if len(players_matching_alias) > 1:
                raise Exception("%s matches the following players: %s" % (alias, players_matching_alias))
            
