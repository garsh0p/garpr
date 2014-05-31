import unittest
from model import MatchResult

class TestMatchResult(unittest.TestCase):
    def setUp(self):
        self.winner = 'player1'
        self.loser = 'player2'

        self.match_result = MatchResult(winner=self.winner, loser=self.loser)
    def test_to_string(self):
        self.assertEquals(str(self.match_result), 'player1 > player2')

    def test_contains_players(self):
        self.assertTrue(self.match_result.contains_players(self.winner, self.loser))
        self.assertTrue(self.match_result.contains_players(self.loser, self.winner))

        self.assertFalse(self.match_result.contains_players(self.loser, self.loser))
        self.assertFalse(self.match_result.contains_players(self.loser, 'asdfasdf'))
