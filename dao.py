from pymongo import MongoClient, DESCENDING
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

    @staticmethod
    def get_all_regions():
        regions = mongo_client.database_names()
        regions = [r.split('_')[1] for r in regions if r.startswith('smashranks_')]
        regions = sorted([r for r in regions if not r.startswith('test')])
        return regions

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

    def merge_players(self, source=None, target=None):
        self.check_alias_uniqueness()

        if source is None or target is None:
            raise TypeError("source or target can't be none!");

        if source == target:
            raise ValueError("source and target can't be the same!")

        target.merge_aliases_from(source)
        self.update_player(target)

        for tournament in self.get_all_tournaments():
            tournament.replace_player(player_to_remove=source, player_to_add=target)
            self.update_tournament(tournament)

        self.delete_player(source)

        # sanity check after merging
        self.check_alias_uniqueness()

    def reset_all_player_ratings(self):
        return self.players_col.update({}, {'$set': {'rating': DEFAULT_RATING.get_json_dict()}}, multi=True)

    def insert_tournament(self, tournament):
        return self.tournaments_col.insert(tournament)

    def update_tournament(self, tournament):
        return self.tournaments_col.update({'_id': tournament.id}, tournament.get_json_dict())

    def get_all_tournaments(self, players=None):
        '''players is a list of Players'''
        query_dict = {}

        if players:
            query_list = []
            for player in players:
                query_list.append({'players': {'$in': [player.id]}})
            query_dict['$and'] = query_list

        return [Tournament.from_json(t) for t in self.tournaments_col.find(query_dict).sort([('date', 1)])]

    def get_tournament_by_id(self, id):
        '''id must be an ObjectId'''
        return Tournament.from_json(self.tournaments_col.find_one({'_id': id}))

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
