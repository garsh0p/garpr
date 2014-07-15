class MatchResult(object):
    def __init__(self, winner=None, loser=None):
        self.winner = winner;
        self.loser = loser;

    def __str__(self):
        return "%s > %s" % (self.winner, self.loser)

    def contains_players(self, player1, player2):
        return (self.winner == player1 and self.loser == player2) or \
               (self.winner == player2 and self.loser == player1)

class Player(object):
    def __init__(self, name, aliases, rating):
        self.name = name
        self.aliases = aliases
        self.rating = rating

    def __str__(self):
        return "%s %s [%s]" % (self.name, self.rating, self.aliases)

class Tournament(object):
    def __init__(self, type, raw):
        self.type = type
        self.raw = raw

        # TODO populate everything from raw
        

