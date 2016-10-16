import unittest
import rating_calculators
from bson.objectid import ObjectId
from model import Player, Rating

class TestRatingCalculators(unittest.TestCase):
    def setUp(self):
        self.player_1_id = ObjectId()
        self.player_2_id = ObjectId()
        self.region_id = 'norcal'

        self.player_1 = Player(
                name='gaR',
                aliases=['gar', 'garr'],
                ratings={'norcal': Rating(), 'texas': Rating()},
                id=self.player_1_id)
        self.player_2 = Player(
                name='sfat',
                aliases=['sfat', 'miom | sfat'],
                ratings={'norcal': Rating(), 'socal': Rating()},
                id=self.player_2_id)

    def test_update_trueskill_ratings(self):
        rating_calculators.update_trueskill_ratings(self.region_id, winner=self.player_1, loser=self.player_2)

        self.assertTrue(self.player_1.ratings[self.region_id].mu > 25)
        self.assertTrue(self.player_1.ratings['texas'].mu == 25)

        self.assertTrue(self.player_2.ratings[self.region_id].mu < 25)
        self.assertTrue(self.player_2.ratings['socal'].mu == 25)
