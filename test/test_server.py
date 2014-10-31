import unittest
import server
from mock import patch
import mongomock
from dao import Dao
from scraper.tio import TioScraper
from model import Player, Tournament, TrueskillRating
import json
import rankings

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
        data = self.app.get('/norcal/players').data
        print json.loads(data)
