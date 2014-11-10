from bson import json_util
import json
import trueskill

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
        # player IDs
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
    def __init__(self, name, aliases, ratings, regions, id=None):
        # TODO force aliases to lowercase
        self.id = id
        self.name = name
        self.aliases = aliases
        self.ratings = ratings
        self.regions = regions

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

    def merge_aliases_from(self, player):
        self.aliases.extend(player.aliases)

    def get_json_dict(self):
        json_dict = {}

        if self.id:
            json_dict['_id'] = self.id

        json_dict['name'] = self.name
        json_dict['aliases'] = self.aliases
        json_dict['ratings'] = {region: rating.get_json_dict() for region, rating in self.ratings.iteritems()}
        json_dict['regions'] = self.regions

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
                id=json_dict['_id'] if '_id' in json_dict else None)

class Tournament(object):
    def __init__(self, type, raw, date, name, players, matches, regions, id=None):
        self.id = id
        self.type = type
        self.raw = raw
        self.date = date
        self.name = name
        self.matches = matches
        self.regions = regions

        # player IDs
        self.players = players

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
                id=json_dict['_id'] if '_id' in json_dict else None)

    @classmethod
    def from_scraper(cls, type, scraper, dao):
        players = scraper.get_players()
        matches = scraper.get_matches()
        regions = [dao.region_id]

        # TODO make sure 2 aliases in the same tournament don't map to a single player
        # the players and matches returned from the scraper use player aliases
        # we need to convert these to player IDs
        players = [dao.get_player_by_alias(p).id for p in players]
        for m in matches:
            m.winner = dao.get_player_by_alias(m.winner).id
            m.loser = dao.get_player_by_alias(m.loser).id

        return cls(
                type,
                scraper.get_raw(),
                scraper.get_date(),
                scraper.get_name(),
                players,
                matches,
                regions)

class Ranking(object):
    def __init__(self, region, time, tournaments, ranking, id=None):
        self.region = region
        self.id = id
        self.time = time
        self.ranking = ranking

        # object ids
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
    def __init__(self, id, display_name):
        self.id = id
        self.display_name = display_name

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

        return json_dict

    @classmethod
    def from_json(cls, json_dict):
        if json_dict == None:
            return None

        return cls(
                json_dict['_id'],
                json_dict['display_name'])
