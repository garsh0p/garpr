from pymongo import MongoClient, DESCENDING
from pymongo.son_manipulator import SONManipulator
from bson.objectid import ObjectId
from model import *
import trueskill

DEFAULT_RATING = TrueskillRating()

mongo_client = MongoClient('localhost')

# TODO update passed in model objects when doing an update?

class Dao(object):
    def __init__(self, region):
        self.players_col = mongo_client['smashranks_%s' % region].players
        self.tournaments_col = mongo_client['smashranks_%s' % region].tournaments
        self.rankings_col = mongo_client['smashranks_%s' % region].rankings

    def get_player_by_id(self, id):
        '''id must be an ObjectId'''
        return Player.from_json(self.players_col.find_one({'_id': id}))

    def get_player_by_alias(self, alias):
        '''Converts alias to lowercase'''
        return Player.from_json(self.players_col.find_one({'aliases': {'$in': [alias.lower()]}}))

    def get_all_players(self):
        '''Sorts by lexographical order'''
        return [Player.from_json(p) for p in self.players_col.find().sort([('name', 1)])]

    def add_player(self, player):
        return self.players_col.insert(player.get_json_dict())

    def delete_player(self, player):
        return self.players_col.remove({'_id': player.id})

    def update_player(self, player):
        return self.players_col.update({'_id': player.id}, player.get_json_dict())

    def get_excluded_players(self):
        return [Player.from_json(p) for p in self.players_col.find({'exclude': True})]

    def exclude_player(self, player):
        return self.players_col.update({'_id': player.id}, {'$set': {'exclude': True}})

    def include_player(self, player):
        return self.players_col.update({'_id': player.id}, {'$set': {'exclude': False}})

    def add_alias_to_player(self, player, alias):
        lowercase_alias = alias.lower()
        if not lowercase_alias in player.aliases:
            player.aliases.append(lowercase_alias)

        return self.update_player(player)

    def update_player_name(self, player, name):
        # ensure this name is already an alias
        if not name.lower() in player.aliases:
            raise Exception('Player %s does not have %s as an alias already, cannot change name.' % (player, name))

        player.name = name
        return self.update_player(player)

    def merge_players_with_aliases(self, aliases, alias_to_merge_to):
        self.check_alias_uniqueness()

        if not self.get_player_by_alias(alias_to_merge_to):
            raise Exception("Player %s was not found" % alias_to_merge_to)
        
        if alias_to_merge_to in aliases:
            raise Exception("Cannot merge a player with itself! Alias to merge into: %s. Aliases to merge: %s." 
                            % (alias_to_merge_to, aliases))

        # TODO get a list of players here
        aliases_to_add = set()
        for alias in aliases:
            player = self.get_player_by_alias(alias)
            aliases_to_add.update(set(player.aliases))
            self.delete_player(player)

        player_to_update = self.get_player_by_alias(alias_to_merge_to)
        for alias in aliases_to_add:
            self.add_alias_to_player(player_to_update, alias)

        # sanity check after merging
        self.check_alias_uniqueness()

    def reset_all_player_ratings(self):
        return self.players_col.update({}, {'$set': {'rating': DEFAULT_RATING.get_json_dict()}}, multi=True)

    def insert_tournament(self, tournament):
        return self.tournaments_col.insert(tournament)

    def update_tournament(self, tournament):
        return self.tournaments_col.update({'_id': tournament.id}, tournament.get_json_dict())

    def get_all_tournaments(self):
        return [Tournament.from_json(t) for t in self.tournaments_col.find().sort([('date', 1)])]

    def replace_player_in_tournament(self, tournament, player_to_remove, player_to_add):
        tournament.replace_player(player_to_remove, player_to_add)
        self.update_tournament(tournament)

    def check_alias_uniqueness(self):
        '''Makes sure that each alias only refers to 1 player'''
        players = self.get_all_players()
        for player in players:
            for alias in player.aliases:
                print "Checking %s" % alias
                players_matching_alias = self._get_players_by_alias(alias)
                if len(players_matching_alias) > 1:
                    raise Exception("%s matches the following players: %s" % (alias, players_matching_alias))

    def insert_ranking(self, ranking):
        return self.rankings_col.insert(ranking.get_json_dict())

    def get_latest_ranking(self):
        return Ranking.from_json(self.rankings_col.find().sort('time', DESCENDING)[0])
                
    def _get_players_by_alias(self, alias):
        '''Converts alias to lowercase'''
        return [Player.from_json(p) for p in self.players_col.find({'aliases': {'$in': [alias.lower()]}})]
