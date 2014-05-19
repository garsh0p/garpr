import unittest
import dao
from bson.objectid import ObjectId

player1 = {
    'normalized_name': 'gar',
    'name': 'gaR',
    'aliases': ['gaR', 'garrR', 'garsh0p']
} 

player2 = {
    'normalized_name': 'sfat',
    'name': 'SFAT',
    'aliases': ['SFAT', 'MIOM | SFAT', 'MIOM|SFAT']
} 

class TestPlayerDAO(unittest.TestCase):
    def setUp(self):
        dao.players_col = dao.mongo_client.test.players
        dao.players_col.drop()

        self.player1_id = dao.add_player(player1)
        self.player2_id = dao.add_player(player2)

        self.expected1 = player1.copy()
        self.expected1['_id'] = self.player1_id
        self.expected2 = player2.copy()
        self.expected2['_id'] = self.player2_id

    def assert_player(self, actual, expected):
        self.assertEquals(actual['normalized_name'], expected['normalized_name'])
        self.assertEquals(actual['name'], expected['name'])
        self.assertEquals(actual['aliases'], expected['aliases'])

    def test_get_all_players(self):
        players = dao.get_all_players()
        self.assertEquals(len(players), 2)

        self.assert_player(players[0], player1)
        self.assert_player(players[1], player2)

    def test_get_player_by_id(self):
        self.assert_player(dao.get_player_by_id(self.player1_id), player1)
        self.assert_player(dao.get_player_by_id(self.player2_id), player2)
        self.assertIsNone(dao.get_player_by_id(ObjectId()))

    def test_get_player_by_name(self):
        self.assert_player(dao.get_player_by_name('GAR'), player1)
        self.assert_player(dao.get_player_by_name('gar'), player1)
        self.assertIsNone(dao.get_player_by_name('asdfasdf'))

    def test_get_player_by_alias(self):
        players = dao.get_player_by_alias('gaR')
        self.assertEquals(len(players), 1)
        self.assert_player(players[0], player1)

        players = dao.get_player_by_alias('garsh0p')
        self.assertEquals(len(players), 1)
        self.assert_player(players[0], player1)

        players = dao.get_player_by_alias('gar')
        self.assertEquals(len(players), 0)

        players = dao.get_player_by_alias('MIOM | SFAT')
        self.assertEquals(len(players), 1)
        self.assert_player(players[0], player2)

        players = dao.get_player_by_alias('MIOM | sfat')
        self.assertEquals(len(players), 0)
