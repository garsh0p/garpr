import unittest
import server
from mock import patch
import mongomock
from dao import Dao
from scraper.tio import TioScraper
from model import Player, Tournament, TrueskillRating
import json
import rankings
from bson.objectid import ObjectId

NORCAL_FILES = [('test/data/norcal1.tio', 'Singles'), ('test/data/norcal2.tio', 'Singles Pro Bracket')]
TEXAS_FILES = [('test/data/texas1.tio', 'singles'), ('test/data/texas2.tio', 'singles')]

NORCAL_REGION_NAME = 'norcal'
TEXAS_REGION_NAME = 'texas'

class TestServer(unittest.TestCase):
    def setUp(self):
        self.mongo_client_patcher = patch('server.mongo_client', new=mongomock.MongoClient())
        self.mongo_client = self.mongo_client_patcher.start()

        server.app.config['TESTING'] = True
        self.app = server.app.test_client()

        self.norcal_dao = Dao(NORCAL_REGION_NAME, mongo_client=self.mongo_client, new=True)
        self.texas_dao = Dao(TEXAS_REGION_NAME, mongo_client=self.mongo_client, new=True)

        self._import_files()
        rankings.generate_ranking(self.norcal_dao)
        rankings.generate_ranking(self.texas_dao)

    def _import_files(self):
        for f in NORCAL_FILES:
            scraper = TioScraper(f[0], f[1])
            self._import_players(scraper, self.norcal_dao)
            self.norcal_dao.insert_tournament(Tournament.from_scraper('tio', scraper, self.norcal_dao))

        for f in TEXAS_FILES:
            scraper = TioScraper(f[0], f[1])
            self._import_players(scraper, self.texas_dao)
            self.texas_dao.insert_tournament(Tournament.from_scraper('tio', scraper, self.texas_dao))

    def _import_players(self, scraper, dao):
        for player in scraper.get_players():
            db_player = dao.get_player_by_alias(player)
            if db_player is None:
                db_player = Player(player, [player.lower()], TrueskillRating(), False)
                dao.add_player(db_player)

    def test_get_region_list(self):
        data = self.app.get('/regions').data
        self.assertEquals(json.loads(data), {'regions': ['norcal', 'texas']})

    def test_get_player_list(self):
        def for_region(data, dao):
            json_data = json.loads(data)

            self.assertEquals(json_data.keys(), ['players'])
            players_list = json_data['players']
            players_from_db = dao.get_all_players()
            self.assertEquals(len(players_list), len(players_from_db))

            # make sure all the IDs in the response match the db
            for player in players_list:
                expected_keys = set(['id', 'name'])
                self.assertEquals(set(player.keys()), expected_keys)
                self.assertEquals(ObjectId(player['id']), dao.get_player_by_alias(player['name']).id)

        data = self.app.get('/norcal/players').data
        for_region(data, self.norcal_dao)

        data = self.app.get('/texas/players').data
        for_region(data, self.texas_dao)

    def test_get_player(self):
        player = self.norcal_dao.get_player_by_alias('gar')
        data = self.app.get('/norcal/players/' + str(player.id)).data
        json_data = json.loads(data)

        self.assertEquals(len(json_data.keys()), 5)
        self.assertEquals(json_data['id'], str(player.id))
        self.assertEquals(json_data['name'], 'gar')
        self.assertEquals(json_data['aliases'], ['gar'])
        self.assertEquals(json_data['exclude'], False)
        self.assertTrue(json_data['rating']['mu'] > 25.9)
        self.assertTrue(json_data['rating']['sigma'] > 3.89)

        player = self.texas_dao.get_player_by_alias('wobbles')
        data = self.app.get('/texas/players/' + str(player.id)).data
        json_data = json.loads(data)

        self.assertEquals(len(json_data.keys()), 5)
        self.assertEquals(json_data['id'], str(player.id))
        self.assertEquals(json_data['name'], 'Wobbles')
        self.assertEquals(json_data['aliases'], ['wobbles'])
        self.assertEquals(json_data['exclude'], False)
        self.assertTrue(json_data['rating']['mu'] > 44.5)
        self.assertTrue(json_data['rating']['sigma'] > 3.53)
