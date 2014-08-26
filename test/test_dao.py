import unittest
import dao
from bson.objectid import ObjectId
from model import *

PLAYER_1 = Player('gaR', ['gar', 'garr', 'garrr'], TrueskillRating(), False, id=ObjectId('000000000000000000000001'))
PLAYER_2 = Player('SFAT', ['miom | sfat', 'sfat'], TrueskillRating(), False, id=ObjectId('000000000000000000000002'))
PLAYER_3 = Player('Zac', ['zac'], TrueskillRating(), False, id=ObjectId('000000000000000000000003'))
PLAYER_4 = Player('Mango', ['mango', 'miom|mango', 'mang0', 'c9 mango'], TrueskillRating(), True, id=ObjectId('000000000000000000000004'))
ALL_PLAYERS = [PLAYER_1, PLAYER_2, PLAYER_3, PLAYER_4]

NEW_PLAYER = Player('Shroomed', ['shroomed', 'mmg|shroomed'], TrueskillRating(), True, id=ObjectId('000000000000000000000005'))

class TestDAO(unittest.TestCase):
    def setUp(self):
        dao.players_col = dao.mongo_client.test.players
        dao.players_col.drop()

        dao.tournaments_col = dao.mongo_client.test.tournaments
        dao.tournaments_col.drop()

        for player in ALL_PLAYERS:
            dao.add_player(player)

    def test_get_player_by_id(self):
        self.assertEquals(dao.get_player_by_id(PLAYER_1.id), PLAYER_1)
        self.assertEquals(dao.get_player_by_id(PLAYER_2.id), PLAYER_2)
        self.assertEquals(dao.get_player_by_id(PLAYER_3.id), PLAYER_3)
        self.assertEquals(dao.get_player_by_id(PLAYER_4.id), PLAYER_4)
        self.assertIsNone(dao.get_player_by_id(ObjectId()))

    def test_get_player_by_alias(self):
        self.assertEquals(dao.get_player_by_alias('gar'), PLAYER_1)
        self.assertEquals(dao.get_player_by_alias('GAR'), PLAYER_1)
        self.assertEquals(dao.get_player_by_alias('garrr'), PLAYER_1)
        self.assertEquals(dao.get_player_by_alias('mango'), PLAYER_4)
        self.assertIsNone(dao.get_player_by_alias('asdfasdf'))

    def test_get_all_players(self):
        '''Ensure its sorted alphabetically'''
        players = dao.get_all_players()
        self.assertEquals(len(players), 4)
        self.assertEquals(players[0], PLAYER_4)
        self.assertEquals(players[1], PLAYER_2)
        self.assertEquals(players[2], PLAYER_3)
        self.assertEquals(players[3], PLAYER_1)

    def test_add_player(self):
        players = dao.get_all_players()
        self.assertEquals(len(players), 4)
        self.assertIsNone(dao.get_player_by_alias('shroomed'))

        dao.add_player(NEW_PLAYER)
        players = dao.get_all_players()
        self.assertEquals(len(players), 5)
        self.assertEquals(dao.get_player_by_alias('shroomed'), NEW_PLAYER)

    def test_add_player_duplicate_key(self):
        pass
