import unittest
from model import *
import trueskill

class TestTrueskillRating(unittest.TestCase):
    def setUp(self):
        self.default_rating_a = TrueskillRating()
        self.default_rating_b = TrueskillRating()
        self.custom_rating = TrueskillRating(trueskill_rating=trueskill.Rating(mu=2, sigma=3))

        self.default_rating_a_json_dict = {
                'mu': self.default_rating_a.trueskill_rating.mu,
                'sigma': self.default_rating_a.trueskill_rating.sigma,
        }

    def test_create_with_rating(self):
        self.assertEquals(self.custom_rating.trueskill_rating.mu, 2)
        self.assertEquals(self.custom_rating.trueskill_rating.sigma, 3)

    def test_create_default_rating(self):
        self.assertEquals(self.default_rating_a.trueskill_rating.mu, 25)
        self.assertAlmostEquals(self.default_rating_a.trueskill_rating.sigma, 8.333, places=3)

    def test_equal(self):
        self.assertEquals(self.default_rating_a, self.default_rating_b)

    def test_not_equal(self):
        self.assertNotEquals(self.default_rating_a, self.custom_rating)

    def test_equal_not_instance(self):
        self.assertNotEquals(self.default_rating_a, MatchResult())

    def test_get_json_dict(self):
        self.assertEquals(self.default_rating_a.get_json_dict(), self.default_rating_a_json_dict)

    def test_from_json(self):
        self.assertEquals(TrueskillRating.from_json(self.default_rating_a_json_dict), self.default_rating_a)

    def test_from_json_none(self):
        self.assertIsNone(TrueskillRating.from_json(None))

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
