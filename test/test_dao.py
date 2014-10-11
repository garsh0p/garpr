import unittest
from dao import Dao, RegionNotFoundException, DuplicateAliasException, InvalidNameException
from bson.objectid import ObjectId
from model import *
from ming import mim
import trueskill

class TestDAO(unittest.TestCase):
    def setUp(self):
        self.region = 'test'
        self.mongo_client = mim.Connection()
        self.dao = Dao(self.region, mongo_client=self.mongo_client, new=True)

        self.player_1_id = ObjectId()
        self.player_2_id = ObjectId()
        self.player_3_id = ObjectId()
        self.player_1 = Player('gaR', ['gar', 'garr'], TrueskillRating(), False, id=self.player_1_id)
        self.player_2 = Player('sfat', ['sfat', 'miom | sfat'], TrueskillRating(), False, id=self.player_2_id)
        self.player_3 = Player(
                'mango', ['mango'], TrueskillRating(trueskill_rating=trueskill.Rating(mu=2, sigma=3)), 
                True, id=self.player_3_id)
        self.players = [self.player_1, self.player_2, self.player_3]

        for player in self.players:
            self.dao.add_player(player)

    def test_init_with_invalid_region(self):
        # create a dao with an existing region
        Dao(self.region, mongo_client=self.mongo_client, new=False)

        # create a dao with a new region
        with self.assertRaises(RegionNotFoundException):
            Dao('newregion', mongo_client=self.mongo_client, new=False)

    def test_get_all_regions(self):
        # add another region
        region = 'newregion'
        Dao(region, mongo_client=self.mongo_client, new=True)

        self.assertEquals(set(self.dao.get_all_regions()), set([self.region, region]))

    def test_get_player_by_id(self):
        self.assertEquals(self.dao.get_player_by_id(self.player_1_id), self.player_1)
        self.assertEquals(self.dao.get_player_by_id(self.player_2_id), self.player_2)
        self.assertEquals(self.dao.get_player_by_id(self.player_3_id), self.player_3)
        self.assertIsNone(self.dao.get_player_by_id(ObjectId()))

    def test_get_player_by_id(self):
        self.assertEquals(self.dao.get_player_by_alias('gar'), self.player_1)
        self.assertEquals(self.dao.get_player_by_alias('GAR'), self.player_1)
        self.assertEquals(self.dao.get_player_by_alias('garr'), self.player_1)
        self.assertEquals(self.dao.get_player_by_alias('sfat'), self.player_2)
        self.assertEquals(self.dao.get_player_by_alias('miom | sfat'), self.player_2)
        self.assertEquals(self.dao.get_player_by_alias('mango'), self.player_3)

        self.assertIsNone(self.dao.get_player_by_alias('miom|sfat'))
        self.assertIsNone(self.dao.get_player_by_alias(''))

    def test_get_all_players(self):
        self.assertEquals(self.dao.get_all_players(), [self.player_1, self.player_3, self.player_2])

    # TODO this can't be tested with MIM right now
    def test_add_player_duplicate(self):
        pass

    def test_delete_player(self):
        self.assertEquals(self.dao.get_player_by_id(self.player_1_id), self.player_1)
        self.assertEquals(self.dao.get_player_by_id(self.player_2_id), self.player_2)
        self.assertEquals(self.dao.get_player_by_id(self.player_3_id), self.player_3)

        self.dao.delete_player(self.player_2)
        self.assertEquals(self.dao.get_player_by_id(self.player_1_id), self.player_1)
        self.assertIsNone(self.dao.get_player_by_id(self.player_2_id))
        self.assertEquals(self.dao.get_player_by_id(self.player_3_id), self.player_3)

        self.dao.delete_player(self.player_3)
        self.assertEquals(self.dao.get_player_by_id(self.player_1_id), self.player_1)
        self.assertIsNone(self.dao.get_player_by_id(self.player_2_id))
        self.assertIsNone(self.dao.get_player_by_id(self.player_3_id))

        self.dao.delete_player(self.player_1)
        self.assertIsNone(self.dao.get_player_by_id(self.player_1_id))
        self.assertIsNone(self.dao.get_player_by_id(self.player_2_id))
        self.assertIsNone(self.dao.get_player_by_id(self.player_3_id))

    def test_update_player(self):
        self.assertEquals(self.dao.get_player_by_id(self.player_1_id), self.player_1)
        self.assertEquals(self.dao.get_player_by_id(self.player_2_id), self.player_2)
        self.assertEquals(self.dao.get_player_by_id(self.player_3_id), self.player_3)

        player_1_clone = Player('gar', ['gar', 'garr'], TrueskillRating(), False, id=self.player_1_id)
        player_1_clone.name = 'garrr'
        player_1_clone.aliases.append('garrr')
        player_1_clone.exclude = True
        self.assertNotEquals(self.dao.get_player_by_id(self.player_1_id), player_1_clone)

        self.dao.update_player(player_1_clone)

        self.assertNotEquals(self.dao.get_player_by_id(self.player_1_id), self.player_1)
        self.assertEquals(self.dao.get_player_by_id(self.player_2_id), self.player_2)
        self.assertEquals(self.dao.get_player_by_id(self.player_3_id), self.player_3)
        self.assertEquals(self.dao.get_player_by_id(self.player_1_id), player_1_clone)

    def test_get_excluded_players(self):
        self.assertEquals(self.dao.get_excluded_players(), [self.player_3])

    def test_exclude_player(self):
        self.assertEquals(self.dao.get_excluded_players(), [self.player_3])

        self.assertFalse(self.player_1.exclude)
        self.dao.exclude_player(self.player_1)
        self.assertTrue(self.player_1.exclude)

        excluded_players = sorted(self.dao.get_excluded_players(), key=lambda p: p.name)
        self.assertEquals(len(excluded_players), 2)
        self.assertEquals(excluded_players[0], self.player_1)
        self.assertEquals(excluded_players[1], self.player_3)

    def test_include_player(self):
        self.assertEquals(self.dao.get_excluded_players(), [self.player_3])

        self.assertTrue(self.player_3.exclude)
        self.dao.include_player(self.player_3)
        self.assertFalse(self.player_3.exclude)

        self.assertEquals(self.dao.get_excluded_players(), [])

    def test_add_alias_to_player(self):
        new_alias = 'gaRRR'
        lowercase_alias = 'garrr'
        old_expected_aliases = ['gar', 'garr']
        new_expected_aliases = ['gar', 'garr', 'garrr']

        self.assertEquals(self.dao.get_player_by_id(self.player_1_id).aliases, old_expected_aliases)
        self.assertEquals(self.player_1.aliases, old_expected_aliases)
        self.dao.add_alias_to_player(self.player_1, new_alias)
        self.assertEquals(self.dao.get_player_by_id(self.player_1_id).aliases, new_expected_aliases)
        self.assertEquals(self.player_1.aliases, new_expected_aliases)

    def test_add_alias_to_player_duplicate(self):
        with self.assertRaises(DuplicateAliasException):
            self.dao.add_alias_to_player(self.player_1, 'garr')

    def test_update_player_name(self):
        self.assertEquals(self.dao.get_player_by_id(self.player_1_id).name, 'gaR')
        self.assertEquals(self.player_1.name, 'gaR')
        self.dao.update_player_name(self.player_1, 'gaRR')
        self.assertEquals(self.dao.get_player_by_id(self.player_1_id).name, 'gaRR')
        self.assertEquals(self.player_1.name, 'gaRR')

    def test_update_player_name_non_alias(self):
        with self.assertRaises(InvalidNameException):
            self.dao.update_player_name(self.player_1, 'asdf')

    def test_reset_all_player_ratings(self):
        self.assertEquals(self.dao.get_player_by_id(self.player_1_id).rating, TrueskillRating())
        self.assertEquals(self.dao.get_player_by_id(self.player_2_id).rating, TrueskillRating())
        self.assertEquals(self.dao.get_player_by_id(self.player_3_id).rating, 
                          TrueskillRating(trueskill_rating=trueskill.Rating(mu=2, sigma=3)))

        self.dao.reset_all_player_ratings()

        self.assertEquals(self.dao.get_player_by_id(self.player_1_id).rating, TrueskillRating())
        self.assertEquals(self.dao.get_player_by_id(self.player_2_id).rating, TrueskillRating())
        self.assertEquals(self.dao.get_player_by_id(self.player_3_id).rating, TrueskillRating())
