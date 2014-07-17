from bson import json_util
import json

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
    def __init__(self, name, aliases, rating, id=None):
        self.id = id
        self.name = name
        self.aliases = aliases
        self.rating = rating

    def __str__(self):
        return "%s %s %s [%s]" % (self.id, self.name, self.rating, self.aliases)

    def get_json_dict(self):
        json_dict = {}

        if self.id:
            json_dict['_id'] = self.id

        json_dict['name'] = self.name
        json_dict['aliases'] = self.aliases
        json_dict['rating'] = self.rating

        return json_dict

    @classmethod
    def from_json(cls, json_dict):
        if json_dict == None:
            return None

        return cls(json_dict['name'], json_dict['aliases'], json_dict['rating'], id=json_dict['_id'])

class Tournament(object):
    def __init__(self, type, scraper):
        self.type = type
        self.raw = scraper.get_raw()
        self.date = scraper.get_date()
        self.name = scraper.get_name()
        self.players = scraper.get_players()
        self.matches = scraper.get_matches()

    def get_json_dict(self):
        json_dict = {}

        json_dict['type'] = self.type
        json_dict['raw'] = self.raw
        json_dict['date'] = self.date
        json_dict['name'] = self.name
        json_dict['players'] = self.players
        json_dict['matches'] = [m.get_json_dict() for m in self.matches]

        return json_dict

