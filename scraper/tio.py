from bs4 import BeautifulSoup
from model import MatchResult

class TioScraper(object):
    def __init__(self, filepath, bracket_name):
        self.filepath = filepath
        self.bracket_name = bracket_name
        self.name = None
        self.date = None
        self.matches = None
        self.players = None

        with open(filepath) as f:
            self.text = f.read()

        self.soup = BeautifulSoup(self.text, 'xml')

    def get_raw(self):
        return self.text

    def get_name(self):
        return self.soup.Event.Name.text

    # TODO figure out what format to return date in
    def get_date(self):
        return self.soup.Event.StartDate.text

    # TODO verify that match order is correct for 2 set grand finals
    def get_matches(self):
        player_map = dict((p.ID.text, p.Nickname.text) for p in self.soup.find_all('Player'))

        bracket = None
        for b in self.soup.find_all('Game'):
            if b.Name.text == self.bracket_name:
                bracket = b
                break

        matches = []
        for match in bracket.find_all('Match'):
            player_1_id = match.Player1.text
            player_2_id = match.Player2.text
            winner_id = match.Winner.text
            loser_id = player_1_id if winner_id == player_2_id else player_2_id

            try:
                winner = player_map[winner_id]
                loser = player_map[loser_id]

                matches.append(MatchResult(winner=winner, loser=loser))
            except KeyError:
                print 'Could not find player for ids', player_1_id, player_2_id

        return matches

    def get_players(self):
        if not self.players:
            self.players = set()
            matches = self.get_matches()
            for match in matches:
                self.players.add(match.winner)
                self.players.add(match.loser)

        return self.players
