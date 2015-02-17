from bs4 import BeautifulSoup
from model import MatchResult
from dateutil import parser

class TioScraper(object):
    def __init__(self, text, bracket_name):
        self.bracket_name = bracket_name
        self.name = None
        self.date = None
        self.matches = None
        self.players = None

        self.text = text

        self.soup = BeautifulSoup(self.text, 'xml')

    @classmethod
    def from_file(cls, filepath, bracket_name):
        with open(filepath) as f:
            text = f.read()
        return cls(text, bracket_name)

    def get_raw(self):
        return self.text

    def get_name(self):
        return self.soup.Event.Name.text

    def get_date(self):
        return parser.parse(self.soup.Event.StartDate.text)

    def get_matches(self):
        player_map = dict((p.ID.text, p.Nickname.text.strip()) for p in self.soup.find_all('Player'))

        bracket = None
        for b in self.soup.find_all('Game'):
            if b.Name.text == self.bracket_name:
                bracket = b
                break

        if bracket is None:
            raise ValueError('Bracket name %s not found!' % self.bracket_name)

        matches = []
        grand_finals_first_set = None
        grand_finals_second_set = None
        for match in bracket.find_all('Match'):
            player_1_id = match.Player1.text
            player_2_id = match.Player2.text
            winner_id = match.Winner.text
            loser_id = player_1_id if winner_id == player_2_id else player_2_id

            try:
                winner = player_map[winner_id]
                loser = player_map[loser_id]
                match_result = MatchResult(winner=winner, loser=loser)

                if match.IsChampionship.text == 'True':
                    grand_finals_first_set = match_result
                elif match.IsSecondChampionship.text == 'True':
                    grand_finals_second_set = match_result
                else: 
                    matches.append(match_result)
            except KeyError:
                print 'Could not find player for ids', player_1_id, player_2_id

        if grand_finals_first_set is not None:
            matches.append(grand_finals_first_set)

        if grand_finals_second_set is not None:
            matches.append(grand_finals_second_set)

        return matches

    def get_players(self):
        if not self.players:
            self.players = set()
            matches = self.get_matches()
            for match in matches:
                self.players.add(match.winner)
                self.players.add(match.loser)
            
            self.players = list(self.players)

        return self.players
