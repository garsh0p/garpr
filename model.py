from bson import json_util
import json
import trueskill

class TrueskillRating(object):
    def __init__(self, trueskill_rating=None):
        if trueskill_rating:
            self.trueskill_rating = trueskill_rating
        else:
            self.trueskill_rating = trueskill.Rating()

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
                self.trueskill_rating == other.trueskill_rating

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
        self.winner = winner;
        self.loser = loser;

    def __str__(self):
        return "%s > %s" % (self.winner, self.loser)

    def contains_players(self, player1, player2):
        return (self.winner == player1 and self.loser == player2) or \
               (self.winner == player2 and self.loser == player1)

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
    def __init__(self, name, aliases, rating, exclude, id=None):
        self.id = id
        self.name = name
        self.aliases = aliases
        self.rating = rating
        self.exclude = exclude

    def __str__(self):
        return "%s %s %s [%s]" % (self.id, self.name, self.rating, self.aliases)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
                self.id == other.id and \
                self.name == other.name and \
                set(self.aliases) == set(other.aliases) and \
                self.rating == other.rating and \
                self.exclude == other.exclude

    def get_json_dict(self):
        json_dict = {}

        if self.id:
            json_dict['_id'] = self.id

        json_dict['name'] = self.name
        json_dict['aliases'] = self.aliases
        json_dict['rating'] = self.rating.get_json_dict()
        json_dict['exclude'] = self.exclude

        return json_dict

    @classmethod
    def from_json(cls, json_dict):
        if json_dict == None:
            return None

        return cls(
                json_dict['name'], 
                json_dict['aliases'], 
                TrueskillRating.from_json(json_dict['rating']), 
                json_dict['exclude'], 
                id=json_dict['_id'])

class Tournament(object):
    def __init__(self, type, scraper=None, id=None):
        self.type = type
        self.id = id

        if scraper != None:
            self.raw = scraper.get_raw()
            self.date = scraper.get_date()
            self.name = scraper.get_name()
            self.players = scraper.get_players()
            self.matches = scraper.get_matches()

    def replace_player(self, player_to_remove, player_to_add):
        if not player_to_remove in self.players:
            raise Exception("Player %s is not in this tournament" % player_to_remove)

        self.players.remove(player_to_remove)
        self.players.append(player_to_add)

        for match in self.matches:
            if match.winner == player_to_remove:
                match.winner = player_to_add

            if match.loser == player_to_remove:
                match.loser = player_to_add

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

        return json_dict

    @classmethod
    def from_json(cls, json_dict):
        tournament = cls(json_dict['type'], id=json_dict['_id'])

        tournament.raw = json_dict['raw']
        tournament.date = json_dict['date']
        tournament.name = json_dict['name']
        tournament.players = json_dict['players']
        tournament.matches = [MatchResult.from_json(m) for m in json_dict['matches']]

        return tournament

class Ranking(object):
    def __init__(self, time, tournaments, ranking, id=None):
        self.id = id
        self.time = time
        self.tournaments = tournaments
        self.ranking = ranking

    def get_json_dict(self):
        json_dict = {}

        if self.id:
            json_dict['_id'] = self.id

        json_dict['time'] = self.time
        json_dict['tournaments'] = self.tournaments
        json_dict['ranking'] = [r.get_json_dict() for r in self.ranking]

        return json_dict

    @classmethod
    def from_json(cls, json_dict):
        if json_dict == None:
            return None

        return cls(
                json_dict['time'], 
                json_dict['tournaments'], 
                [RankingEntry.from_json(r) for r in json_dict['ranking']],
                id=json_dict['_id'])

class RankingEntry(object):
    def __init__(self, rank, player, rating):
        self.rank = rank
        self.player = player
        self.rating = rating

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
