from pymongo import MongoClient, DESCENDING
from bson.objectid import ObjectId
from model import *
import trueskill

DEFAULT_RATING = TrueskillRating()

class RegionNotFoundException(Exception):
    pass

class DuplicateAliasException(Exception):
    pass

class InvalidNameException(Exception):
    pass

class Dao(object):
    def __init__(self, region, mongo_client=MongoClient('localhost'), new=False):
        self.mongo_client = mongo_client
        if not new and not region in Dao.get_all_regions(mongo_client=self.mongo_client):
            raise RegionNotFoundException("%s is not a valid region! Set new=True to create a new region." 
                                          % region)

        database_name = 'smashranks_%s' % region       
        self.players_col = mongo_client[database_name].players
        self.tournaments_col = mongo_client[database_name].tournaments
        self.rankings_col = mongo_client[database_name].rankings

    @classmethod
    def get_all_regions(cls, mongo_client=MongoClient('localhost')):
        regions = mongo_client.database_names()
        regions = [r.split('_')[1] for r in regions if r.startswith('smashranks_')]
        return sorted(regions)

    def get_player_by_id(self, id):
        '''id must be an ObjectId'''
        return Player.from_json(self.players_col.find_one({'_id': id}))

    def get_player_by_alias(self, alias):
        '''Converts alias to lowercase'''
        return Player.from_json(self.players_col.find_one({'aliases': {'$in': [alias.lower()]}}))

    def get_all_players(self):
        '''Sorts by name in lexographical order'''
        return [Player.from_json(p) for p in self.players_col.find().sort([('name', 1)])]

    def add_player(self, player):
        return self.players_col.insert(player.get_json_dict())

    def delete_player(self, player):
        return self.players_col.remove({'_id': player.id})

    def update_player(self, player):
        return self.players_col.update({'_id': player.id}, player.get_json_dict())

    # TODO bulk update
    def update_players(self, players):
        pass

    def get_excluded_players(self):
        return [Player.from_json(p) for p in self.players_col.find({'exclude': True})]

    def exclude_player(self, player):
        player.exclude = True
        return self.update_player(player)

    def include_player(self, player):
        player.exclude = False
        return self.update_player(player)

    def add_alias_to_player(self, player, alias):
        lowercase_alias = alias.lower()

        if lowercase_alias in player.aliases:
            raise DuplicateAliasException('%s is already an alias for %s!' % (alias, player.name))

        player.aliases.append(lowercase_alias)

        return self.update_player(player)

    def update_player_name(self, player, name):
        # ensure this name is already an alias
        if not name.lower() in player.aliases:
            raise InvalidNameException(
                    'Player %s does not have %s as an alias already, cannot change name.' 
                    % (player, name))

        player.name = name
        return self.update_player(player)

    def reset_all_player_ratings(self):
        return self.players_col.update({}, {'$set': {'rating': DEFAULT_RATING.get_json_dict()}}, multi=True)

    def insert_tournament(self, tournament):
        return self.tournaments_col.insert(tournament.get_json_dict())

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

    # TODO reduce db calls for this
    def merge_players(self, source=None, target=None):
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

    def insert_ranking(self, ranking):
        return self.rankings_col.insert(ranking.get_json_dict())

    def get_latest_ranking(self):
        return Ranking.from_json(self.rankings_col.find().sort('time', DESCENDING)[0])

