from bson import json_util
from bson.objectid import ObjectId
import json
import trueskill
import hashlib
import os
from passlib.hash import sha256_crypt

ITERATION_COUNT = 100000

class TrueskillRating(object):
    def __init__(self, trueskill_rating=None):
        if trueskill_rating:
            self.trueskill_rating = trueskill_rating
        else:
            self.trueskill_rating = trueskill.Rating()

    def __str__(self):
        return "(%.3f, %.3f)" % (self.trueskill_rating.mu, self.trueskill_rating.sigma)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
                self.trueskill_rating == other.trueskill_rating

    def __ne__(self, other):
        return not self == other

    def get_json_dict(self):
        json_dict = {}

        json_dict['mu'] = self.trueskill_rating.mu
        json_dict['sigma'] = self.trueskill_rating.sigma

        return json_dict

    @classmethod
    def from_json(cls, json_dict):
        if json_dict == None:
            return None

        return cls(trueskill.Rating(mu=json_dict['mu'], sigma=json_dict['sigma']))


class MatchResult(object):
    def __init__(self, winner=None, loser=None):
        '''
        :param winner: ObjectId
        :param loser: ObjectId
        '''
        self.winner = winner
        self.loser = loser

    def __str__(self):
        return "%s > %s" % (self.winner, self.loser)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
                self.winner == other.winner and \
                self.loser == other.loser

    def __ne__(self, other):
        return not self == other

    def contains_players(self, player1, player2):
        return (self.winner == player1 and self.loser == player2) or \
               (self.winner == player2 and self.loser == player1)

    def contains_player(self, player_id):
        return self.winner == player_id or self.loser == player_id

    def did_player_win(self, player_id):
        return self.winner == player_id

    def get_opposing_player_id(self, player_id):
        if self.winner == player_id:
            return self.loser
        elif self.loser == player_id:
            return self.winner
        else:
            return None

    def get_json_dict(self):
        json_dict = {}

        json_dict['winner'] = self.winner
        json_dict['loser'] = self.loser

        return json_dict

    @classmethod
    def from_json(cls, json_dict):
        if json_dict == None:
            return None

        return cls(winner=json_dict['winner'], loser=json_dict['loser'])

class Player(object):
    def __init__(self, name, aliases, ratings, regions,
            merged=False, merge_parent=None, merge_children=None, id=None,):
        # TODO force aliases to lowercase
        '''
        :param name: string
        :param aliases:  list of strings
        :param ratings:  dict[string] -> rating, where rating is a dict[string] -> float
        :param regions: list of strings
        :param id: ObjectId, autogenerated when you insert into mongo
        :param merged: Bool, whether this Player has been merged into another player
        :param merge_parent: ObjectId of Player this player has been merged into
        :param merge_children: list of ObjectIds of Players that have been merged into this player
        '''
        self.id = id
        self.name = name
        self.aliases = aliases
        self.ratings = ratings
        self.regions = regions

        self.merged = merged
        self.merge_parent = merge_parent
        if not merge_children:
            self.merge_children = [self.id]
        else:
            self.merge_children = merge_children

    @classmethod
    def create_with_default_values(cls, name, region):
        return cls(name, [name.lower()], {}, [region])

    def __str__(self):
        return "%s %s %s %s %s" % (
                self.id,
                self.name,
                {reg: str(rat) for reg, rat in self.ratings.iteritems()},
                self.aliases,
                self.regions)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
                self.id == other.id and \
                self.name == other.name and \
                set(self.aliases) == set(other.aliases) and \
                self.ratings == other.ratings and \
                self.regions == other.regions

    def __ne__(self, other):
        return not self == other

    def get_json_dict(self):
        json_dict = {}

        if self.id:
            json_dict['_id'] = self.id

        json_dict['name'] = self.name
        json_dict['aliases'] = self.aliases
        json_dict['ratings'] = {region: rating.get_json_dict() for region, rating in self.ratings.iteritems()}
        json_dict['regions'] = self.regions

        json_dict['merged'] = self.merged
        json_dict['merge_parent'] = self.merge_parent
        json_dict['merge_children'] = self.merge_children

        return json_dict

    @classmethod
    def from_json(cls, json_dict):
        if json_dict == None:
            return None

        return cls(
                json_dict['name'],
                json_dict['aliases'],
                {region: TrueskillRating.from_json(rating_dict) for region, rating_dict in json_dict['ratings'].iteritems()},
                json_dict['regions'],
                json_dict.get('merged', False),
                json_dict.get('merge_parent', None),
                json_dict.get('merge_children', [json_dict.get('_id', None)]),
                id=json_dict.get('_id', None))

class Tournament(object):
    def __init__(self, type, raw, date, name, players, matches, regions, orig_ids=None, id=None):
        '''
        :param type: string, either "tio", "challonge", or "smashgg"
        :param raw: for tio, this is an xml string. for challonge its a dict from string --> string
        :param date: datetime
        :param name: string
        :param players: list of ObjectIDs
        :param orig_ids: list of original (non-merged) player IDs of Tournament
        :param matches:  list of MatchResults
        :param regions: list of string
        :param id: ObjectID, autogenerated by mongo during insert
        '''
        self.id = id
        self.type = type
        self.raw = raw
        self.date = date
        self.name = name
        self.matches = matches
        self.regions = regions
        self.players = players
        if orig_ids:
            self.orig_ids = orig_ids
        else:
            self.orig_ids = list(self.players)

    def replace_player(self, player_to_remove=None, player_to_add=None):
        # TODO edge cases with this
        # TODO the player being added cannot play himself in any match
        if player_to_remove is None or player_to_add is None:
            raise TypeError("player_to_remove and player_to_add cannot be None!")

        player_to_remove_id = player_to_remove.id
        player_to_add_id = player_to_add.id

        if not player_to_remove_id in self.players:
            print "Player with id %s is not in this tournament. Ignoring." % player_to_remove.id
            return

        self.players.remove(player_to_remove_id)
        self.players.append(player_to_add_id)

        for match in self.matches:
            if match.winner == player_to_remove_id:
                match.winner = player_to_add_id

            if match.loser == player_to_remove_id:
                match.loser = player_to_add_id

    def get_json_dict(self):
        json_dict = {}

        if self.id:
            json_dict['_id'] = self.id

        json_dict['type'] = self.type
        json_dict['raw'] = self.raw
        json_dict['date'] = self.date
        json_dict['name'] = self.name
        json_dict['players'] = self.players
        json_dict['orig_ids'] = self.orig_ids
        json_dict['matches'] = [m.get_json_dict() for m in self.matches]
        json_dict['regions'] = self.regions

        return json_dict

    @classmethod
    def from_json(cls, json_dict):
        if json_dict == None:
            return None

        return cls(
                json_dict['type'],
                json_dict['raw'],
                json_dict['date'],
                json_dict['name'],
                json_dict['players'],
                [MatchResult.from_json(m) for m in json_dict['matches']],
                json_dict['regions'],
                json_dict.get('orig_ids', None),
                id=json_dict['_id'] if '_id' in json_dict else None)

    # TODO "sanity checks"
    @classmethod
    def from_pending_tournament(cls, pending_tournament):
        # takes a real alias to id map instead of a list of objects
        def _get_player_id_from_map_or_throw(alias_to_id_map, alias):
            if alias in alias_to_id_map:
                return alias_to_id_map[alias]
            else:
                raise ValueError('Alias %s has no ID in map\n: %s' % (alias, alias_to_id_map))

        alias_to_id_map = dict([(entry['player_alias'], entry['player_id']) for entry in pending_tournament.alias_to_id_map if entry['player_id'] is not None])

        # we need to convert pending tournament players/matches to player IDs
        players = [_get_player_id_from_map_or_throw(alias_to_id_map, p) for p in pending_tournament.players]
        for m in pending_tournament.matches:
            m.winner = _get_player_id_from_map_or_throw(alias_to_id_map, m.winner)
            m.loser = _get_player_id_from_map_or_throw(alias_to_id_map, m.loser)
        return cls(
                pending_tournament.type,
                pending_tournament.raw,
                pending_tournament.date,
                pending_tournament.name,
                players,
                pending_tournament.matches,
                pending_tournament.regions,
                players,
                pending_tournament.id)

    # TODO this should go away as we should never build a Tournament straight from a scraper
    # it should be from a PendingTournament
    @classmethod
    def from_scraper(cls, type, scraper, alias_to_id_map, region_id):
        pending_tournament = PendingTournament.from_scraper(type, scraper, region_id)
        pending_tournament.alias_to_id_map = alias_to_id_map

        return Tournament.from_pending_tournament(pending_tournament)


class PendingTournament(object):
    '''Same as a Tournament, except it uses aliases for players instead of ids.
       Used during tournament import, before aliases are mapped to player ids.'''
    def __init__(self, type, raw, date, name, players, matches, regions, alias_to_id_map=None, id=None):
        '''
        :param type: string, either "tio", "challonge", "smashgg"
        :param raw: for tio, this is an xml string. for challonge its a dict from string --> string.
                    for smashgg its a dictionary of string-->string or string-->array[string]
        :param date: datetime
        :param name: string
        :param players: list of ObjectIDs
        :param matches:  list of MatchResults
        :param regions: list of string
        :param alias_to_id_map: list of pairs of
            {"player_alias": player_alias, "player_id": player_id} dicts
        :param id: ObjectID, autogenerated by mongo during insert
        '''
        self.id = id
        self.type = type
        self.raw = raw
        self.date = date
        self.name = name
        self.matches = matches
        self.regions = regions

        # this is actually a list because mongo doesn't support having keys (i.e. aliases) with periods in them
        self.alias_to_id_map = [] if alias_to_id_map is None else alias_to_id_map

        # player aliases, not ids!
        self.players = players

    def get_json_dict(self):
        json_dict = {}

        if self.id:
            json_dict['_id'] = self.id

        json_dict['type'] = self.type
        json_dict['raw'] = self.raw
        json_dict['date'] = self.date
        json_dict['name'] = self.name
        json_dict['players'] = self.players
        json_dict['matches'] = [m.get_json_dict() for m in self.matches]
        json_dict['regions'] = self.regions
        json_dict['alias_to_id_map'] = self.alias_to_id_map

        return json_dict

    @classmethod
    def from_json(cls, json_dict):
        if json_dict == None:
            return None

        return cls(
                json_dict['type'],
                json_dict['raw'],
                json_dict['date'],
                json_dict['name'],
                json_dict['players'],
                [MatchResult.from_json(m) for m in json_dict['matches']],
                json_dict['regions'],
                json_dict['alias_to_id_map'],
                id=json_dict['_id'] if '_id' in json_dict else None)

    def set_alias_id_mapping(self, alias, id):
        for mapping in self.alias_to_id_map:
            if mapping['player_alias'] == alias:
                mapping['player_alias'] = alias
                mapping['player_id'] = id
                return

        # if we've gotten out here, we couldn't find an existing match, so add a new element
        self.alias_to_id_map.append({
            'player_alias': alias,
            'player_id': id
        })

    def delete_alias_id_mapping(self, alias):
        for mapping in self.alias_to_id_map:
            if mapping['player_alias'] == alias:
                self.alias_to_id_map.remove(mapping)
                return mapping

    @classmethod
    def from_scraper(cls, type, scraper, region_id):
        regions = [region_id]
        return cls(
                type,
                scraper.get_raw(),
                scraper.get_date(),
                scraper.get_name(),
                scraper.get_players(),
                scraper.get_matches(),
                regions)

    #TODO: untested/unused!
    @classmethod
    def from_scraper_with_alias_map(cls, type, scraper, alias_to_id_map, region_id):
        pending_tournament = PendingTournament.from_scraper(type, scraper, region_id)
        pending_tournament.alias_to_id_map = alias_to_id_map
        # alias_to_id_map is a map from player alias (string) -> player id (ObjectId)
        def _get_player_id_from_map_or_throw(alias_to_id_map, alias):
            player_id = alias_to_id_map[alias]
            if player_id is None:
                raise Exception('Alias %s has no ID in map\n: %s' % (alias, alias_to_id_map))
            else:
                return player_id
        # the players and matches returned from the scraper use player aliases
        # we need to convert these to player IDs
        players = [_get_player_id_from_map_or_throw(alias_to_id_map, p) for p in players]
        for m in matches:
            m.winner = _get_player_id_from_map_or_throw(alias_to_id_map, m.winner)
            m.loser = _get_player_id_from_map_or_throw(alias_to_id_map, m.loser)
        pending_tournament.players = players
        pending_tournament.matches = matches

        return Tournament.from_pending_tournament(pending_tournament)


class Ranking(object):
    def __init__(self, region, time, tournaments, ranking, id=None):
        '''
        :param region: string
        :param time: datetime
        :param tournaments: list of ObjectIds
        :param ranking: TODO
        :param id: TODO
        '''
        self.region = region
        self.id = id
        self.time = time
        self.ranking = ranking
        self.tournaments = tournaments

    def get_json_dict(self):
        json_dict = {}

        if self.id:
            json_dict['_id'] = self.id

        json_dict['region'] = self.region
        json_dict['time'] = self.time
        json_dict['tournaments'] = self.tournaments
        json_dict['ranking'] = [r.get_json_dict() for r in self.ranking]

        return json_dict

    @classmethod
    def from_json(cls, json_dict):
        if json_dict == None:
            return None

        return cls(
                json_dict['region'],
                json_dict['time'],
                json_dict['tournaments'],
                [RankingEntry.from_json(r) for r in json_dict['ranking']],
                id=json_dict['_id'] if '_id' in json_dict else None)

# TODO be explicit about this being a player_id
class RankingEntry(object):
    def __init__(self, rank, player, rating):
        '''
        :param rank: TODO
        :param player: TODO
        :param rating: TODO
        '''
        self.rank = rank
        self.player = player
        self.rating = rating

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
                self.rank == other.rank and \
                self.player == other.player and \
                self.rating == other.rating

    def __ne__(self, other):
        return not self == other

    def get_json_dict(self):
        json_dict = {}

        json_dict['rank'] = self.rank
        json_dict['player'] = self.player
        json_dict['rating'] = self.rating

        return json_dict

    @classmethod
    def from_json(cls, json_dict):
        if json_dict == None:
            return None

        return cls(
                json_dict['rank'],
                json_dict['player'],
                json_dict['rating'])

class Region(object):
    def __init__(self, id, display_name, rankings=None):
        '''
        :param id: TODO
        :param display_name: TODO
        '''
        self.id = id
        self.display_name = display_name

        if rankings is not None:
            self.rankings = rankings
        else:
            self.rankings = RegionRankingsCriteria()

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
                self.id == other.id and \
                self.display_name == other.display_name

    def __ne__(self, other):
        return not self == other

    def get_json_dict(self):
        json_dict = {}

        json_dict['_id'] = self.id
        json_dict['display_name'] = self.display_name
        json_dict['rankings'] = self.rankings.get_json_dict()

        return json_dict

    @classmethod
    def from_json(cls, json_dict):
        if json_dict == None:
            return None

        return cls(
                json_dict['_id'],
                json_dict['display_name'])

class RegionRankingsCriteria(object):
    def __init__(self, day_limit=60, num_tourneys=2):
        self.day_limit = day_limit
        self.num_tourneys = num_tourneys

    def get_json_dict(self):
        json_dict = {}

        json_dict['day_limit'] = self.day_limit
        json_dict['num_tourneys'] = self.num_tourneys

        return json_dict

class User(object):
    def __init__(self, id, admin_regions, username, salt, hashed_password):
        self.id = id
        self.admin_regions = admin_regions
        self.username = username
        self.salt = salt
        self.hashed_password = hashed_password

    def __str__(self):
        return "%s %s %s" % (self.id, self.username, self.admin_regions)

    def get_json_dict(self):
        json_dict = {}
        json_dict['_id'] = self.id
        json_dict['username'] = self.username
        json_dict['admin_regions'] = self.admin_regions
        json_dict['salt'] = self.salt
        json_dict['hashed_password'] = self.hashed_password

        return json_dict

    @property
    def clean_user(self):
        ret = self.get_json_dict()
        for field in ["hashed_password", "salt"]:
            ret.pop(field, None)
        return ret

    @classmethod
    def from_json(cls, json_dict):
        if json_dict == None:
            return None

        return cls(
                json_dict['_id'],
                json_dict['admin_regions'],
                json_dict['username'],
                json_dict['salt'],
                json_dict['hashed_password']
                )

    # probably shouldn't use this method, doesn't salt
    @classmethod
    def create_with_default_values(cls, regions, username, password):
        salt = os.urandom(16)
        # hashed_password = hashlib.pbkdf2_hmac('sha256', password, salt, ITERATION_COUNT)
        hashed_password = sha256_crypt.encrypt(password, rounds=ITERATION_COUNT)
        return cls("userid--" + username, regions, username, "", hashed_password)

class Merge(object):
    # merge source_player into target_player
    def __init__(self, requester_user_id, source_player_obj_id, target_player_obj_id, time, id=None):
        self.requester_user_id = requester_user_id
        self.source_player_obj_id = source_player_obj_id
        self.target_player_obj_id = target_player_obj_id
        self.time = time
        self.id = id

    def get_json_dict(self):
        json_dict = {}

        json_dict['requester_user_id'] = self.requester_user_id
        json_dict['source_player_obj_id'] = self.source_player_obj_id
        json_dict['target_player_obj_id'] = self.target_player_obj_id
        json_dict['time'] = self.time
        if self.id: json_dict['_id'] = self.id

        return json_dict

    @classmethod
    def from_json(cls, json_dict):
        if json_dict == None:
            return None

        return cls(
                json_dict['requester_user_id'],
                json_dict['source_player_obj_id'],
                json_dict['target_player_obj_id'],
                json_dict['time'],
                id=(json_dict['_id'] if '_id' in json_dict else None)
                )

class SessionMapping(object):
    def __init__(self, session_id, user_id):
        self.session_id = session_id
        self.user_id = user_id


    def get_json_dict(self):
        json_dict = {}

        json_dict['session_id'] = self.session_id
        json_dict['user_id'] = self.user_id
        return json_dict

    @classmethod
    def from_json(cls, json_dict):
        if json_dict == None:
            return None

        return cls(
                json_dict['session_id'],
                json_dict['user_id'],
                id=json_dict['_id'] if '_id' in json_dict else None
                )
