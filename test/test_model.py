import unittest
from model import *
import trueskill
from bson.objectid import ObjectId

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

    def test_to_string(self):
        self.assertEquals(str(self.default_rating_a), "(25.000, 8.333)")

    def test_equal(self):
        self.assertTrue(self.default_rating_a == self.default_rating_b)
        self.assertFalse(self.default_rating_a == self.custom_rating)

    def test_not_equal(self):
        self.assertTrue(self.default_rating_a != self.custom_rating)
        self.assertFalse(self.default_rating_a != self.default_rating_b)

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
        self.winner = ObjectId()
        self.loser = ObjectId()
        self.other_player = ObjectId()

        self.match_result = MatchResult(winner=self.winner, loser=self.loser)
        self.other_match_result = MatchResult(winner=self.winner, loser=self.other_player)

        self.match_result_json_dict = {
                'winner': self.winner,
                'loser': self.loser
        }

    def test_to_string(self):
        self.assertEquals(str(self.match_result), '%s > %s' % (self.winner, self.loser))

    def test_equal(self):
        self.assertTrue(self.match_result == MatchResult(winner=self.winner, loser=self.loser))
        self.assertFalse(self.match_result == self.other_match_result)

    def test_not_equal(self):
        self.assertFalse(self.match_result != MatchResult(winner=self.winner, loser=self.loser))
        self.assertTrue(self.match_result != self.other_match_result)

    def test_contains_players(self):
        self.assertTrue(self.match_result.contains_players(self.winner, self.loser))
        self.assertTrue(self.match_result.contains_players(self.loser, self.winner))

        self.assertFalse(self.match_result.contains_players(self.loser, self.loser))
        self.assertFalse(self.match_result.contains_players(self.loser, self.other_player))

    def test_did_player_win(self):
        self.assertTrue(self.match_result.did_player_win(self.winner))
        self.assertFalse(self.match_result.did_player_win(self.loser))

    def test_get_opposing_player_id(self):
        self.assertEquals(self.match_result.get_opposing_player_id(self.winner), self.loser)
        self.assertEquals(self.match_result.get_opposing_player_id(self.loser), self.winner)
        self.assertIsNone(self.match_result.get_opposing_player_id(self.other_player))

    def test_get_json_dict(self):
        self.assertEquals(self.match_result.get_json_dict(), self.match_result_json_dict)

    def test_from_json(self):
        self.assertEquals(self.match_result, MatchResult.from_json(self.match_result_json_dict))

    def test_from_json_none(self):
        self.assertIsNone(MatchResult.from_json(None))

class TestPlayer(unittest.TestCase):
    def setUp(self):
        self.player_1_id = ObjectId()
        self.player_1_name = 'gaR'
        self.player_1_aliases = ['gar', 'garr', 'garpr']
        self.player_1_rating = TrueskillRating()
        self.player_1_exclude = False

        self.player_2_id = ObjectId()
        self.player_2_name = 'MIOM | SFAT'
        self.player_2_aliases = ['miom | sfat', 'sfat', 'miom|sfat']
        self.player_2_rating = TrueskillRating(trueskill_rating=trueskill.Rating(mu=30, sigma=2))
        self.player_2_exclude = True

        self.player_1 = Player(self.player_1_name, self.player_1_aliases, self.player_1_rating, self.player_1_exclude, id=self.player_1_id)
        self.player_1_missing_id = Player(self.player_1_name, self.player_1_aliases, self.player_1_rating, self.player_1_exclude)
        self.player_2 = Player(self.player_2_name, self.player_2_aliases, self.player_2_rating, self.player_2_exclude, id=self.player_2_id)
        
        self.player_1_json_dict = {
                '_id': self.player_1_id,
                'name': self.player_1_name,
                'aliases': self.player_1_aliases,
                'rating': self.player_1_rating.get_json_dict(),
                'exclude': self.player_1_exclude
        }

        self.player_1_json_dict_missing_id = {
                'name': self.player_1_name,
                'aliases': self.player_1_aliases,
                'rating': self.player_1_rating.get_json_dict(),
                'exclude': self.player_1_exclude
        }

    def test_to_string(self):
        self.assertEquals(str(self.player_1), "%s gaR (25.000, 8.333) ['gar', 'garr', 'garpr'] Excluded: False" % str(self.player_1_id))

    def test_equal(self):
        player_1_clone = Player(self.player_1_name, self.player_1_aliases, self.player_1_rating, self.player_1_exclude, id=self.player_1_id)
        self.assertTrue(player_1_clone == self.player_1)
        self.assertFalse(self.player_1 == self.player_2)

    def test_not_equal(self):
        player_1_clone = Player(self.player_1_name, self.player_1_aliases, self.player_1_rating, self.player_1_exclude, id=self.player_1_id)
        self.assertFalse(player_1_clone != self.player_1)
        self.assertTrue(self.player_1 != self.player_2)

    def test_merge_aliases(self):
        expected_aliases = []
        expected_aliases.extend(self.player_1_aliases)
        expected_aliases.extend(self.player_2_aliases)
        
        self.player_1.merge_aliases_from(self.player_2)
        self.assertEquals(self.player_1.aliases, expected_aliases)

    def test_get_json_dict(self):
        self.assertEquals(self.player_1.get_json_dict(), self.player_1_json_dict)

    def test_get_json_dict_missing_id(self):
        self.assertEquals(self.player_1_missing_id.get_json_dict(), self.player_1_json_dict_missing_id)

    def test_from_json(self):
        self.assertEquals(self.player_1, Player.from_json(self.player_1_json_dict))

    def test_from_json_missing_id(self):
        self.assertEquals(self.player_1_missing_id, Player.from_json(self.player_1_json_dict_missing_id))

    def test_from_json_none(self):
        self.assertIsNone(Player.from_json(None))

class TestTournament(unittest.TestCase):
    pass

class TestRanking(unittest.TestCase):
    def test_get_json_dict(self):
        pass

    def test_get_json_dict_missing_id(self):
        pass

    def test_from_json(self):
        pass

    def test_from_json_missing_id(self):
        pass

    def test_from_json_none(self):
        pass

class TestRankingEntry(unittest.TestCase):
    def test_get_json_dict(self):
        pass

    def test_from_json(self):
        pass

    def test_from_json_none(self):
        pass
