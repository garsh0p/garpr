import unittest
import rating_calculators
from bson.objectid import ObjectId
from model import Player, TrueskillRating

class TestRatingCalculators(unittest.TestCase):
    def setUp(self):
        self.player_1_id = ObjectId()
        self.player_2_id = ObjectId()

        self.player_1 = Player('gaR', ['gar', 'garr'], TrueskillRating(), False, id=self.player_1_id)
        self.player_2 = Player('sfat', ['sfat', 'miom | sfat'], TrueskillRating(), False, id=self.player_2_id)

    def test_update_trueskill_ratings(self):
        rating_calculators.update_trueskill_ratings(winner=self.player_1, loser=self.player_2)
        self.assertTrue(self.player_1.rating.trueskill_rating.mu > 25)
        self.assertTrue(self.player_2.rating.trueskill_rating.mu < 25)
