import base64
import facebook
import hashlib
import json
import mongomock
import os
import requests
import string
import unittest

from bson.objectid import ObjectId
from datetime import datetime
from mock import patch, Mock

import rankings
import server

from dao import Dao, DATABASE_NAME, ITERATION_COUNT
from scraper.tio import TioScraper
from model import AliasMapping, AliasMatch, Match, Merge, Player, PendingTournament, \
                 Ranking, RankingEntry, Rating, Region, Tournament, User, Session

NORCAL_FILES = [('test/data/norcal1.tio', 'Singles'), ('test/data/norcal2.tio', 'Singles Pro Bracket')]
TEXAS_FILES = [('test/data/texas1.tio', 'singles'), ('test/data/texas2.tio', 'singles')]
NORCAL_PENDING_FILES = [('test/data/pending1.tio', 'bam 6 singles')]

TEMP_DB_NAME = 'garpr_test_tmp'

def _import_file(f, dao):
    scraper = TioScraper.from_file(f[0], f[1])
    _import_players(scraper, dao)
    player_map = dao.get_player_id_map_from_player_aliases(scraper.get_players())
    pending_tournament, _ = PendingTournament.from_scraper('tio', scraper, dao.region_id)
    pending_tournament.alias_to_id_map = player_map
    tournament = Tournament.from_pending_tournament(pending_tournament)
    dao.insert_tournament(tournament)

def _import_players(scraper, dao):
    for player in scraper.get_players():
        db_player = dao.get_player_by_alias(player)
        if db_player is None:
            db_player = Player(
                    id=ObjectId(),
                    name=player,
                    aliases=[player.lower()],
                    ratings={dao.region_id: Rating()},
                    regions=[dao.region_id])
            dao.insert_player(db_player)

class TestServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        mongo_client = mongomock.MongoClient()

        norcal_region = Region(id='norcal', display_name='Norcal')
        texas_region = Region(id='texas', display_name='Texas')
        Dao.insert_region(norcal_region, mongo_client)
        Dao.insert_region(texas_region, mongo_client)

        norcal_dao = Dao('norcal', mongo_client=mongo_client)
        texas_dao = Dao('texas', mongo_client=mongo_client)

        for f in NORCAL_FILES:
            _import_file(f, norcal_dao)

        for f in TEXAS_FILES:
            _import_file(f, texas_dao)

        for f in NORCAL_PENDING_FILES:
            scraper = TioScraper.from_file(f[0], f[1])
            norcal_dao.insert_pending_tournament(PendingTournament.from_scraper('tio', scraper, norcal_dao.region_id)[0])

        now = datetime(2014, 11, 1)
        rankings.generate_ranking(norcal_dao, now=now)
        rankings.generate_ranking(texas_dao, now=now)

        user_id = 'asdf'
        user_full_name = 'full name'
        user_admin_regions = ['norcal', 'nyc']
        user = User(
            id=user_id,
            admin_regions=user_admin_regions,
            username=user_full_name,
            salt='nacl',
            hashed_password='browns')
        norcal_dao.insert_user(user)

        users_col = mongo_client[DATABASE_NAME][User.collection_name]
        salt = base64.b64encode(os.urandom(16))
        hashed_password = base64.b64encode(hashlib.pbkdf2_hmac('sha256', 'rip', salt, ITERATION_COUNT))

        gar = User(
            id='userid--gar',
            admin_regions=['norcal'],
            username='gar',
            salt=salt,
            hashed_password=hashed_password)
        norcal_dao.insert_user(gar)

        # store current mongo db instead of rerunning every time
        # (unfortunately mongomock doesn't implement copydb)
        cls.mongo_data = {}
        for coll in mongo_client[DATABASE_NAME].collection_names():
            cls.mongo_data[coll] = list(mongo_client[DATABASE_NAME][coll].find())

    def setUp(self):
        self.mongo_client_patcher = patch('server.mongo_client', new=mongomock.MongoClient())
        self.mongo_client = self.mongo_client_patcher.start()


        # copy data from globals
        # faster than loading every time
        for coll, data in TestServer.mongo_data.items():
            if data:
                self.mongo_client[DATABASE_NAME][coll].insert_many(TestServer.mongo_data[coll])

        server.app.config['TESTING'] = True
        self.app = server.app.test_client()

        self.norcal_region = Region(id='norcal', display_name='Norcal')
        self.texas_region = Region(id='texas', display_name='Texas')

        self.norcal_dao = Dao('norcal', mongo_client=self.mongo_client)
        self.assertIsNotNone(self.norcal_dao)
        self.texas_dao = Dao('texas', mongo_client=self.mongo_client)
        self.assertIsNotNone(self.texas_dao)

        self.user_id = 'asdf'
        self.user_full_name = 'full name'
        self.user_admin_regions = ['norcal', 'nyc']
        self.user = User(
            id=self.user_id,
            admin_regions=self.user_admin_regions,
            username=self.user_full_name,
            salt='nacl',
            hashed_password='browns')
        self.users_col = self.mongo_client[DATABASE_NAME][User.collection_name]
        self.sessions_col = self.mongo_client[DATABASE_NAME][Session.collection_name]

### start of actual test cases

    def test_cors_checker(self):
        self.assertTrue(server.is_allowed_origin("http://njssbm.com"))
        self.assertTrue(server.is_allowed_origin("https://njssbm.com"))
        self.assertTrue(server.is_allowed_origin("http://njssbm.com:3000"))
        self.assertTrue(server.is_allowed_origin("https://njssbm.com:3000"))
        self.assertTrue(server.is_allowed_origin("http://192.168.33.10"))
        self.assertTrue(server.is_allowed_origin("https://192.168.33.10"))
        self.assertTrue(server.is_allowed_origin("https://192.168.33.10:433"))
        self.assertTrue(server.is_allowed_origin("http://192.168.33.10:433"))
        self.assertTrue(server.is_allowed_origin("http://192.168.33.1"))
        self.assertTrue(server.is_allowed_origin("https://192.168.33.1"))
        self.assertTrue(server.is_allowed_origin("https://192.168.33.1:433"))
        self.assertTrue(server.is_allowed_origin("http://192.168.33.1:433"))
        self.assertTrue(server.is_allowed_origin("http://notgarpr.com:433"))
        self.assertTrue(server.is_allowed_origin("https://notgarpr.com"))
        self.assertTrue(server.is_allowed_origin("https://notgarpr.com:420"))
        self.assertTrue(server.is_allowed_origin("http://notgarpr.com"))
        self.assertTrue(server.is_allowed_origin("http://stage.notgarpr.com"))
        self.assertTrue(server.is_allowed_origin("http://www.notgarpr.com"))
        self.assertTrue(server.is_allowed_origin("https://stage.notgarpr.com"))
        self.assertTrue(server.is_allowed_origin("https://www.notgarpr.com"))
        self.assertTrue(server.is_allowed_origin("http://stage.notgarpr.com:44"))
        self.assertTrue(server.is_allowed_origin("http://www.notgarpr.com:919"))
        self.assertFalse(server.is_allowed_origin("http://notgarpr.com.evil.com"))
        self.assertFalse(server.is_allowed_origin("http://192.168.33.1.evil.com"))
        self.assertFalse(server.is_allowed_origin("http://192.168.33.1:445.evil.com"))
        self.assertFalse(server.is_allowed_origin("http://notgarpr.com:445.evil.com"))
        self.assertFalse(server.is_allowed_origin("http://notgarpr.com:443\x00.evil.com"))
        self.assertFalse(server.is_allowed_origin("http://notgarpr.com:443\r\n.evil.com"))
        self.assertFalse(server.is_allowed_origin("http://notgarpr.com:443\n.evil.com"))

    def test_get_region_list(self):
        data = self.app.get('/regions').data

        expected_region_dict = {
                'regions': [
                    {'id': 'norcal', 'display_name': 'Norcal',
                        'ranking_num_tourneys_attended': 2,
                        'ranking_activity_day_limit': 60,
                        'tournament_qualified_day_limit': 999},
                    {'id': 'texas', 'display_name': 'Texas',
                        'ranking_num_tourneys_attended': 2,
                        'ranking_activity_day_limit': 60,
                        'tournament_qualified_day_limit': 999}
                ]
        }

        self.assertEquals(json.loads(data), expected_region_dict)

    def test_get_player_list(self):
        def for_region(json_data, dao):
            self.assertEquals(json_data.keys(), ['players'])
            players_list = json_data['players']
            players_from_db = dao.get_all_players()
            self.assertEquals(len(players_list), len(players_from_db))

            for player in players_list:
                expected_keys = set(['id', 'name', 'merged', 'merge_children', 'merge_parent', 'regions', 'ratings'])
                self.assertEquals(set(player.keys()), expected_keys)
                self.assertEquals(ObjectId(player['id']), dao.get_player_by_alias(player['name']).id)

        data = self.app.get('/norcal/players').data
        json_data = json.loads(data)
        self.assertEquals(len(json_data['players']), 65)
        for_region(json_data, self.norcal_dao)

        data = self.app.get('/texas/players').data
        json_data = json.loads(data)
        self.assertEquals(len(json_data['players']), 41)
        for_region(json_data, self.texas_dao)

    def test_get_player_list_with_alias(self):
        player = self.norcal_dao.get_player_by_alias('gar')

        data = self.app.get('/norcal/players?alias=gar').data
        json_data = json.loads(data)
        self.assertEquals(len(json_data['players']), 1)

        json_player = json_data['players'][0]
        expected_keys = set(['id', 'name', 'merged', 'merge_children', 'merge_parent', 'regions', 'ratings'])
        self.assertEquals(set(json_player.keys()), expected_keys)
        self.assertEquals(ObjectId(json_player['id']), player.id)

    def test_get_player_list_case_insensitive(self):
        player = self.norcal_dao.get_player_by_alias('gar')

        data = self.app.get('/norcal/players?alias=GAR').data
        json_data = json.loads(data)
        self.assertEquals(len(json_data['players']), 1)

        json_player = json_data['players'][0]
        expected_keys = set(['id', 'name', 'merged', 'merge_children', 'merge_parent', 'regions', 'ratings'])
        self.assertEquals(set(json_player.keys()), expected_keys)
        self.assertEquals(ObjectId(json_player['id']), player.id)

    def test_get_player_list_with_bad_alias(self):
        data = self.app.get('/norcal/players?alias=BADALIAS').data
        json_data = json.loads(data)
        self.assertEquals(len(json_data['players']), 0)

    def test_get_player_list_with_query(self):
        data = self.app.get('/norcal/players?query=AND').data
        json_data = json.loads(data)

        self.assertEquals(len(json_data['players']), 3)

        json_player = json_data['players'][0]
        self.assertEquals(json_player['name'], 'Ampersand')

        json_player = json_data['players'][1]
        self.assertEquals(json_player['name'], 'laudandas')

        json_player = json_data['players'][2]
        self.assertEquals(json_player['name'], 'laudandus')

    def test_get_player_list_with_query_short_name(self):
        # add a player with a single letter name
        self.norcal_dao.insert_player(Player.create_with_default_values('l', 'norcal'))

        data = self.app.get('/norcal/players?query=l').data
        json_data = json.loads(data)

        self.assertEquals(len(json_data['players']), 6)

        json_player = json_data['players'][0]
        self.assertEquals(json_player['name'], 'l')

    def test_get_player_list_with_query_split_tokens(self):
        data = self.app.get('/norcal/players?query=z').data
        json_data = json.loads(data)

        self.assertEquals(len(json_data['players']), 2)

        json_player = json_data['players'][0]
        self.assertEquals(json_player['name'], 'Zift')

        json_player = json_data['players'][1]
        self.assertEquals(json_player['name'], 'dr.z')

        data = self.app.get('/norcal/players?query=d').data
        json_data = json.loads(data)

        self.assertEquals(len(json_data['players']), 7)

        json_player = json_data['players'][0]
        self.assertEquals(json_player['name'], 'CT Denti')

    def test_get_player(self):
        player = self.norcal_dao.get_player_by_alias('gar')
        data = self.app.get('/norcal/players/' + str(player.id)).data
        json_data = json.loads(data)

        self.assertEquals(len(json_data.keys()), 8)
        self.assertEquals(json_data['id'], str(player.id))
        self.assertEquals(json_data['name'], 'gar')
        self.assertEquals(json_data['aliases'], ['gar'])
        self.assertEquals(json_data['regions'], ['norcal'])
        self.assertTrue(json_data['ratings']['norcal']['mu'] > 25.9)
        self.assertTrue(json_data['ratings']['norcal']['sigma'] > 3.89)
        self.assertEquals(json_data['merged'], False)
        self.assertEquals(json_data['merge_parent'], None)

        player = self.texas_dao.get_player_by_alias('wobbles')
        data = self.app.get('/texas/players/' + str(player.id)).data
        json_data = json.loads(data)

        self.assertEquals(len(json_data.keys()), 8)
        self.assertEquals(json_data['id'], str(player.id))
        self.assertEquals(json_data['name'], 'Wobbles')
        self.assertEquals(json_data['aliases'], ['wobbles'])
        self.assertEquals(json_data['regions'], ['texas'])
        self.assertTrue(json_data['ratings']['texas']['mu'] > 44.5)
        self.assertTrue(json_data['ratings']['texas']['sigma'] > 3.53)
        self.assertEquals(json_data['merged'], False)
        self.assertEquals(json_data['merge_parent'], None)

    def test_get_tournament_list(self):
        def for_region(data, dao):
            json_data = json.loads(data)

            self.assertEquals(json_data.keys(), ['tournaments'])
            tournaments_list = json_data['tournaments']
            tournaments_from_db = dao.get_all_tournaments(regions=[dao.region_id])
            self.assertEquals(len(tournaments_list), len(tournaments_from_db))

            for tournament in tournaments_list:
                tournament_from_db = dao.get_tournament_by_id(ObjectId(tournament['id']))
                expected_keys = set(['id', 'name', 'date', 'regions'])
                self.assertEquals(set(tournament.keys()), expected_keys)
                self.assertEquals(tournament['id'], str(tournament_from_db.id))
                self.assertEquals(tournament['name'], tournament_from_db.name)
                self.assertEquals(tournament['date'], tournament_from_db.date.strftime('%x'))
                self.assertEquals(tournament['regions'], [dao.region_id])

        data = self.app.get('/norcal/tournaments').data
        for_region(data, self.norcal_dao)

        data = self.app.get('/texas/tournaments').data
        for_region(data, self.texas_dao)

    @patch('server.get_user_from_request')
    def test_get_tournament_list_include_pending(self, mock_get_user_from_request):
        dao = self.norcal_dao
        mock_get_user_from_request.return_value = self.user
        data = self.app.get('/norcal/tournaments?includePending=true').data
        json_data = json.loads(data)

        self.assertEquals(json_data.keys(), ['tournaments'])
        tournaments_list = json_data['tournaments']
        tournaments_from_db = dao.get_all_tournaments(regions=[dao.region_id])
        pending_tournaments_from_db = dao.get_all_pending_tournaments(regions=[dao.region_id])
        self.assertEquals(len(tournaments_list), len(tournaments_from_db) + len(pending_tournaments_from_db))

        # first 2 tournaments should be regular tournaments
        for i in xrange(2):
            tournament = tournaments_list[i]
            tournament_from_db = dao.get_tournament_by_id(ObjectId(tournament['id']))
            expected_keys = set(['id', 'name', 'date', 'regions', 'pending'])

            self.assertEquals(set(tournament.keys()), expected_keys)
            self.assertEquals(tournament['id'], str(tournament_from_db.id))
            self.assertEquals(tournament['name'], tournament_from_db.name)
            self.assertEquals(tournament['date'], tournament_from_db.date.strftime('%x'))
            self.assertEquals(tournament['regions'], [dao.region_id])
            self.assertEquals(tournament['pending'], False)

        # the 3rd tournament should be a pending tournament
        pending_tournament = tournaments_list[2]
        pending_tournament_from_db = dao.get_pending_tournament_by_id(ObjectId(pending_tournament['id']))
        expected_keys = set(['id', 'name', 'date', 'regions', 'pending'])
        self.assertEquals(set(pending_tournament.keys()), expected_keys)
        self.assertEquals(pending_tournament['id'], str(pending_tournament_from_db.id))
        self.assertEquals(pending_tournament['name'], pending_tournament_from_db.name)
        self.assertEquals(pending_tournament['date'], pending_tournament_from_db.date.strftime('%x'))
        self.assertEquals(pending_tournament['regions'], [dao.region_id])
        self.assertEquals(pending_tournament['pending'], True)

    @patch('server.get_user_from_request')
    def test_get_tournament_list_include_pending_false(self, mock_get_user_from_request):
        dao = self.norcal_dao
        data = self.app.get('/norcal/tournaments?includePending=false').data
        json_data = json.loads(data)
        mock_get_user_from_request.return_value = self.user


        self.assertEquals(json_data.keys(), ['tournaments'])
        tournaments_list = json_data['tournaments']
        tournaments_from_db = dao.get_all_tournaments(regions=[dao.region_id])
        self.assertEquals(len(tournaments_list), len(tournaments_from_db))

        for tournament in tournaments_list:
            tournament_from_db = dao.get_tournament_by_id(ObjectId(tournament['id']))
            expected_keys = set(['id', 'name', 'date', 'regions'])
            self.assertEquals(set(tournament.keys()), expected_keys)
            self.assertEquals(tournament['id'], str(tournament_from_db.id))
            self.assertEquals(tournament['name'], tournament_from_db.name)
            self.assertEquals(tournament['date'], tournament_from_db.date.strftime('%x'))
            self.assertEquals(tournament['regions'], [dao.region_id])

    @patch('server.get_user_from_request')
    def test_get_tournament_list_include_pending_not_logged_in(self, mock_get_user_from_request):
        mock_get_user_from_request.return_value = None
        dao = self.norcal_dao
        data = self.app.get('/norcal/tournaments?includePending=true').data
        json_data = json.loads(data)

        self.assertEquals(json_data.keys(), ['tournaments'])
        tournaments_list = json_data['tournaments']
        tournaments_from_db = dao.get_all_tournaments(regions=[dao.region_id])
        self.assertEquals(len(tournaments_list), len(tournaments_from_db))

        for tournament in tournaments_list:
            tournament_from_db = dao.get_tournament_by_id(ObjectId(tournament['id']))
            expected_keys = set(['id', 'name', 'date', 'regions'])
            self.assertEquals(set(tournament.keys()), expected_keys)
            self.assertEquals(tournament['id'], str(tournament_from_db.id))
            self.assertEquals(tournament['name'], tournament_from_db.name)
            self.assertEquals(tournament['date'], tournament_from_db.date.strftime('%x'))
            self.assertEquals(tournament['regions'], [dao.region_id])

    @patch('server.get_user_from_request')
    def test_get_tournament_list_include_pending_not_admin(self, mock_get_user_from_request):
        self.user.admin_regions = []
        mock_get_user_from_request.return_value = self.user
        dao = self.norcal_dao
        data = self.app.get('/norcal/tournaments?includePending=true').data
        json_data = json.loads(data)

        self.assertEquals(json_data.keys(), ['tournaments'])
        tournaments_list = json_data['tournaments']
        tournaments_from_db = dao.get_all_tournaments(regions=[dao.region_id])
        self.assertEquals(len(tournaments_list), len(tournaments_from_db))

        for tournament in tournaments_list:
            tournament_from_db = dao.get_tournament_by_id(ObjectId(tournament['id']))
            expected_keys = set(['id', 'name', 'date', 'regions'])
            self.assertEquals(set(tournament.keys()), expected_keys)
            self.assertEquals(tournament['id'], str(tournament_from_db.id))
            self.assertEquals(tournament['name'], tournament_from_db.name)
            self.assertEquals(tournament['date'], tournament_from_db.date.strftime('%x'))
            self.assertEquals(tournament['regions'], [dao.region_id])

    @patch('server.get_user_from_request')
    @patch('server.TioScraper')
    def test_post_to_tournament_list_tio(self, mock_tio_scraper, mock_get_user_from_request):
        mock_get_user_from_request.return_value = self.user
        scraper = TioScraper.from_file(NORCAL_FILES[0][0], NORCAL_FILES[0][1])
        mock_tio_scraper.return_value = scraper
        data = {
            'data': 'data',
            'type': 'tio',
            'bracket': 'bracket'
        }

        response = self.app.post('/norcal/tournaments', data=json.dumps(data), content_type='application/json')
        json_data = json.loads(response.data)

        mock_tio_scraper.assert_called_once_with('data', 'bracket')

        self.assertEquals(1, len(json_data))
        self.assertEquals(24, len(json_data['id']))
        pending_tournament = self.norcal_dao.get_pending_tournament_by_id(ObjectId(json_data['id']))
        self.assertIsNotNone(pending_tournament)
        self.assertEquals(len(pending_tournament.alias_to_id_map), 59)

    @patch('server.get_user_from_request')
    def test_post_to_tournament_list_tio_missing_bracket(self, mock_get_user_from_request):
        mock_get_user_from_request.return_value = self.user
        data = {
            'data': 'data',
            'type': 'tio',
        }

        response = self.app.post('/norcal/tournaments', data=json.dumps(data), content_type='application/json')

        self.assertEquals(response.status_code, 400)
        self.assertEquals(response.data, '"Missing bracket name"')

    @patch('server.get_user_from_request')
    @patch('server.ChallongeScraper')
    def test_post_to_tournament_list_challonge(self, mock_challonge_scraper, mock_get_user_from_request):
        mock_get_user_from_request.return_value = self.user
        scraper = TioScraper.from_file(NORCAL_FILES[0][0], NORCAL_FILES[0][1])
        mock_challonge_scraper.return_value = scraper
        data = {
            'data': 'data',
            'type': 'challonge'
        }

        response = self.app.post('/norcal/tournaments', data=json.dumps(data), content_type='application/json')
        json_data = json.loads(response.data)

        mock_challonge_scraper.assert_called_once_with('data')

        self.assertEquals(1, len(json_data))
        self.assertEquals(24, len(json_data['id']))
        pending_tournament = self.norcal_dao.get_pending_tournament_by_id(ObjectId(json_data['id']))
        self.assertIsNotNone(pending_tournament)
        self.assertEquals(len(pending_tournament.alias_to_id_map), 59)

    @patch('server.get_user_from_request')
    def test_post_to_tournament_list_missing_data(self, mock_get_user_from_request):
        mock_get_user_from_request.return_value = self.user
        data = {'type': 'tio'}
        response = self.app.post('/norcal/tournaments', data=json.dumps(data), content_type='application/json')
        self.assertEquals(response.status_code, 400)
        self.assertEquals(response.data, '"data required"')

    @patch('server.get_user_from_request')
    def test_post_to_tournament_list_unknown_type(self, mock_get_user_from_request):
        mock_get_user_from_request.return_value = self.user
        data = {
            'data': 'data',
            'type': 'unknown'
        }
        response = self.app.post('/norcal/tournaments', data=json.dumps(data), content_type='application/json')
        self.assertEquals(response.status_code, 400)
        self.assertEquals(response.data, '"Unknown type"')

    @patch('server.get_user_from_request')
    def test_post_to_tournament_list_invalid_permissions(self, mock_get_user_from_request):
        mock_get_user_from_request.return_value = self.user
        response = self.app.post('/texas/tournaments')
        self.assertEquals(response.status_code, 403)
        self.assertEquals(response.data, '"Permission denied"')

    def setup_finalize_tournament_fixtures(self):
        player_1_id = ObjectId()
        player_2_id = ObjectId()
        player_3_id = ObjectId()
        player_4_id = ObjectId()
        player_1 = Player(
            name='C9 Mango',
            aliases=['C9 Mango'],
            ratings={'norcal': Rating(), 'texas': Rating()},
            regions=['norcal', 'texas'],
            id=player_1_id)
        player_2 = Player(
            name='[A]rmada',
            aliases=['[A]rmada'],
            ratings={'norcal': Rating(), 'texas': Rating()},
            regions=['norcal', 'texas'],
            id=player_2_id)
        player_3 = Player(
            name='Liquid`Hungrybox',
            aliases=['Liquid`Hungrybox'],
            ratings={'norcal': Rating()},
            regions=['norcal'],
            id=player_3_id)
        player_4 = Player(
            name='Poor | Zhu',
            aliases=['Poor | Zhu'],
            ratings={'norcal': Rating()},
            regions=['norcal'],
            id=player_4_id)

        players = [player_1, player_2, player_3, player_4]

        player_1_name = 'Mango'
        player_2_name = 'Armada'
        player_3_name = 'Hungrybox'
        player_4_name = 'Zhu'
        new_player_name = 'Scar'

        # pending tournament that can be finalized
        pending_tournament_id_1 = ObjectId()
        pending_tournament_players_1 = [player_1_name, player_2_name, player_3_name, player_4_name, new_player_name]
        pending_tournament_matches_1 = [
                AliasMatch(winner=player_2_name, loser=player_1_name),
                AliasMatch(winner=player_3_name, loser=player_4_name),
                AliasMatch(winner=player_1_name, loser=player_3_name),
                AliasMatch(winner=player_1_name, loser=player_2_name),
                AliasMatch(winner=player_1_name, loser=player_2_name),
                AliasMatch(winner=player_4_name, loser=new_player_name),
        ]

        pending_tournament_1 = PendingTournament(
                                    name='Genesis top 5',
                                    type='tio',
                                    regions=['norcal'],
                                    date=datetime(2009, 7, 10),
                                    raw='raw',
                                    players=pending_tournament_players_1,
                                    matches=pending_tournament_matches_1,
                                    id=pending_tournament_id_1)

        pending_tournament_1.set_alias_id_mapping(player_1_name, player_1_id)
        pending_tournament_1.set_alias_id_mapping(player_2_name, player_2_id)
        pending_tournament_1.set_alias_id_mapping(player_3_name, player_3_id)
        pending_tournament_1.set_alias_id_mapping(player_4_name, player_4_id)

        # set id mapping to None for a player that doesn't exist
        pending_tournament_1.set_alias_id_mapping(new_player_name, None)

        # pending tournament in wrong region
        pending_tournament_id_2 = ObjectId()
        pending_tournament_players_2 = [player_1_name, player_2_name]
        pending_tournament_matches_2 = [
                AliasMatch(winner=player_2_name, loser=player_1_name),
        ]

        pending_tournament_2 = PendingTournament(
                                    name='Fake Texas Tournament',
                                    type='tio',
                                    regions=['texas'],
                                    date=datetime(2014, 7, 10),
                                    raw='raw',
                                    players=pending_tournament_players_2,
                                    matches=pending_tournament_matches_2,
                                    id=pending_tournament_id_2)

        pending_tournament_2.set_alias_id_mapping(player_1_name, player_1_id)
        pending_tournament_2.set_alias_id_mapping(player_2_name, player_2_id)

        # incompletely mapped pending tournament
        pending_tournament_id_3 = ObjectId()
        pending_tournament_3 = PendingTournament(
                                    name='Genesis top 4 incomplete',
                                    type='tio',
                                    regions=['norcal'],
                                    date=datetime(2009, 7, 10),
                                    raw='raw',
                                    players=pending_tournament_players_1,
                                    matches=pending_tournament_matches_1,
                                    id=pending_tournament_id_3)


        pending_tournament_3.set_alias_id_mapping(player_1_name, player_1_id)
        pending_tournament_3.set_alias_id_mapping(player_2_name, player_2_id)
        # Note that Hungrybox and Zhu are unmapped

        # pending tournament with multiple players mapping to a single player id
        pending_tournament_id_4 = ObjectId()
        pending_tournament_players_4 = [player_1_name, player_2_name]
        pending_tournament_matches_4 = [
                AliasMatch(winner=player_2_name, loser=player_1_name),
        ]

        pending_tournament_4 = PendingTournament(
                                    name='Genesis top 5',
                                    type='tio',
                                    regions=['norcal'],
                                    date=datetime(2011, 7, 10),
                                    raw='raw',
                                    players=pending_tournament_players_4,
                                    matches=pending_tournament_matches_4,
                                    id=pending_tournament_id_4)

        pending_tournament_4.set_alias_id_mapping(player_1_name, player_1_id)
        pending_tournament_4.set_alias_id_mapping(player_2_name, player_1_id)

        for player in players:
            self.norcal_dao.insert_player(player)

        self.norcal_dao.insert_pending_tournament(pending_tournament_1)
        self.norcal_dao.insert_pending_tournament(pending_tournament_3)
        self.texas_dao.insert_pending_tournament(pending_tournament_2)
        self.norcal_dao.insert_pending_tournament(pending_tournament_4)

        # return players and pending tournaments for test use and cleanup
        # pending tournaments are padded by 0 so indices work out nicely
        return {
            "players": players,
            "pending_tournaments": (0, pending_tournament_1, pending_tournament_2, pending_tournament_3, pending_tournament_4)
        }

    def cleanup_finalize_tournament_fixtures(self, fixtures):
        for player in fixtures["players"]:
            self.norcal_dao.delete_player(player)
        new_player = self.norcal_dao.get_player_by_alias('Scar')
        if new_player:
            self.norcal_dao.delete_player(new_player)
        tmp, pending_tournament_1, pending_tournament_2, pending_tournament_3, pending_tournament_4 = fixtures["pending_tournaments"]

        self.norcal_dao.delete_pending_tournament(pending_tournament_1)
        self.norcal_dao.delete_pending_tournament(pending_tournament_3)
        self.texas_dao.delete_pending_tournament(pending_tournament_2)
        self.norcal_dao.delete_pending_tournament(pending_tournament_4)

    @patch('server.get_user_from_request')
    def test_finalize_tournament_incorrect_region(self, mock_get_user_from_request):
        fixtures = self.setup_finalize_tournament_fixtures()
        fixture_pending_tournaments = fixtures["pending_tournaments"]
        mock_get_user_from_request.return_value = self.user

        # incorrect region
        no_permissions_response = self.app.post(
            '/texas/tournaments/' + str(fixture_pending_tournaments[2].id) + '/finalize')
        self.assertEquals(no_permissions_response.status_code, 403)
        self.assertEquals(no_permissions_response.data, '"Permission denied"')

        self.cleanup_finalize_tournament_fixtures(fixtures)

    @patch('server.get_user_from_request')
    def test_finalize_nonexistent_tournament(self, mock_get_user_from_request):
        fixtures = self.setup_finalize_tournament_fixtures()
        mock_get_user_from_request.return_value = self.user

        # no pending tournament with this id
        missing_response = self.app.post('/norcal/tournaments/' + str(ObjectId()) + '/finalize')
        self.assertEquals(missing_response.status_code, 400, msg=str(missing_response.data))
        self.assertEquals(missing_response.data,
            '"No pending tournament found with that id."')

        self.cleanup_finalize_tournament_fixtures(fixtures)

    @patch('server.get_user_from_request')
    def test_finalize_incompletely_mapped_tournament(self, mock_get_user_from_request):
        mock_get_user_from_request.return_value = self.user
        fixtures = self.setup_finalize_tournament_fixtures()
        fixture_pending_tournaments = fixtures["pending_tournaments"]

        # alias_to_id_map doesn't map each alias
        incomplete_response = self.app.post(
            '/norcal/tournaments/' + str(fixture_pending_tournaments[3].id) + '/finalize')
        self.assertEquals(incomplete_response.status_code, 400, msg=str(incomplete_response.data))
        self.assertEquals(incomplete_response.data,
            '"Not all player aliases in this pending tournament have been mapped to player ids."')

        self.cleanup_finalize_tournament_fixtures(fixtures)

    @patch('server.get_user_from_request')
    def test_finalize_tournament_with_double_mapping(self, mock_get_user_from_request):
        """Multiple aliases are mapped to the same player id."""
        mock_get_user_from_request.return_value = self.user
        fixtures = self.setup_finalize_tournament_fixtures()
        fixture_pending_tournaments = fixtures["pending_tournaments"]

        # alias_to_id_map doesn't map each alias
        incomplete_response = self.app.post(
            '/norcal/tournaments/' + str(fixture_pending_tournaments[4].id) + '/finalize')
        self.assertEquals(incomplete_response.status_code, 400, msg=str(incomplete_response.data))
        self.assertEquals(incomplete_response.data,
            '"Player id %s is already mapped"' % fixtures["players"][0].id)

        self.cleanup_finalize_tournament_fixtures(fixtures)

    @patch('server.get_user_from_request')
    def test_finalize_tournament(self, mock_get_user_from_request):
        fixtures = self.setup_finalize_tournament_fixtures()
        fixture_pending_tournaments = fixtures["pending_tournaments"]
        mock_get_user_from_request.return_value = self.user

        # finalize first pending tournament
        success_response = self.app.post(
            '/norcal/tournaments/' + str(fixture_pending_tournaments[1].id) + '/finalize')
        self.assertEquals(success_response.status_code, 200, msg=success_response.data)
        success_response_data = json.loads(success_response.data)
        self.assertTrue(success_response_data['success'])
        self.assertTrue('tournament_id' in success_response_data)
        new_tournament_id = success_response_data['tournament_id']
        # finalized tournament gets the same id
        self.assertIsNotNone(new_tournament_id)
        self.assertEquals(new_tournament_id, str(fixture_pending_tournaments[1].id))

        # check final list of tournaments
        tournaments_list_response = self.app.get('/norcal/tournaments?includePending=false')
        self.assertEquals(tournaments_list_response.status_code, 200)
        tournaments_data = json.loads(tournaments_list_response.data)
        tournaments_ids = set([str(tournament['id']) for tournament in tournaments_data['tournaments']])
        self.assertTrue(str(new_tournament_id) in tournaments_ids)
        self.assertFalse(str(fixture_pending_tournaments[3].id) in tournaments_ids)

        pending_tournaments_list_response = self.app.get('/norcal/tournaments?includePending=true')
        self.assertEquals(pending_tournaments_list_response.status_code, 200)
        pending_tournaments_data = json.loads(pending_tournaments_list_response.data)
        pending_tournaments_ids = set([str(tournament['id']) for tournament in pending_tournaments_data['tournaments']])

        self.assertTrue(str(new_tournament_id) in pending_tournaments_ids)
        self.assertTrue(str(fixture_pending_tournaments[3].id) in pending_tournaments_ids)

        new_player_name = 'Scar'
        new_player = self.norcal_dao.get_player_by_alias(new_player_name)
        self.assertIsNotNone(new_player)
        self.assertEquals(new_player.name, new_player_name)

        self.cleanup_finalize_tournament_fixtures(fixtures)

    def test_get_tournament(self):
        tournament = self.norcal_dao.get_all_tournaments(regions=['norcal'])[0]
        data = self.app.get('/norcal/tournaments/' + str(tournament.id)).data
        json_data = json.loads(data)

        self.assertEquals(len(json_data.keys()), 9)
        self.assertEquals(json_data['id'], str(tournament.id))
        self.assertEquals(json_data['name'], 'BAM: 4 stocks is not a lead')
        self.assertEquals(json_data['type'], 'tio')
        self.assertEquals(json_data['date'], tournament.date.strftime('%x'))
        self.assertEquals(json_data['regions'], ['norcal'])
        self.assertEquals(len(json_data['players']), len(tournament.players))
        self.assertEquals(len(json_data['matches']), len(tournament.matches))

        for player in json_data['players']:
            db_player = self.norcal_dao.get_player_by_id(ObjectId(player['id']))
            self.assertEquals(len(player.keys()), 2)
            self.assertEquals(player['id'], str(db_player.id))
            self.assertEquals(player['name'], db_player.name)

        # spot check first and last match
        match = json_data['matches'][0]
        db_match = tournament.matches[0]
        self.assertEquals(len(match.keys()), 6)
        self.assertEquals(match['winner_id'], str(db_match.winner))
        self.assertEquals(match['winner_name'], self.norcal_dao.get_player_by_id(ObjectId(match['winner_id'])).name)
        self.assertEquals(match['loser_id'], str(db_match.loser))
        self.assertEquals(match['loser_name'], self.norcal_dao.get_player_by_id(ObjectId(match['loser_id'])).name)
        match = json_data['matches'][-1]
        db_match = tournament.matches[-1]
        self.assertEquals(len(match.keys()), 6)
        self.assertEquals(match['winner_id'], str(db_match.winner))
        self.assertEquals(match['winner_name'], self.norcal_dao.get_player_by_id(ObjectId(match['winner_id'])).name)
        self.assertEquals(match['loser_id'], str(db_match.loser))
        self.assertEquals(match['loser_name'], self.norcal_dao.get_player_by_id(ObjectId(match['loser_id'])).name)

        # sanity tests for another region
        tournament = self.texas_dao.get_all_tournaments()[0]
        data = self.app.get('/texas/tournaments/' + str(tournament.id)).data
        json_data = json.loads(data)

        self.assertEquals(len(json_data.keys()), 9)
        self.assertEquals(json_data['id'], str(tournament.id))
        self.assertEquals(json_data['name'], 'FX Biweekly 6')
        self.assertEquals(json_data['type'], 'tio')
        self.assertEquals(json_data['date'], tournament.date.strftime('%x'))
        self.assertEquals(json_data['regions'], ['texas'])
        self.assertEquals(len(json_data['players']), len(tournament.players))
        self.assertEquals(len(json_data['matches']), len(tournament.matches))

    @patch('server.get_user_from_request')
    def test_get_tournament_pending(self,mock_get_user_from_request):
        mock_get_user_from_request.return_value = self.user
        pending_tournament = self.norcal_dao.get_all_pending_tournaments(regions=['norcal'])[0]
        data = self.app.get('/norcal/tournaments/' + str(pending_tournament.id)).data
        json_data = json.loads(data)

        self.assertEquals(len(json_data.keys()), 10)
        self.assertEquals(json_data['id'], str(pending_tournament.id))
        self.assertEquals(json_data['name'], 'bam 6 - 11-8-14')
        self.assertEquals(json_data['type'], 'tio')
        self.assertEquals(json_data['date'], pending_tournament.date.strftime('%x'))
        self.assertEquals(json_data['regions'], ['norcal'])
        self.assertEquals(len(json_data['players']), len(pending_tournament.players))
        self.assertEquals(len(json_data['matches']), len(pending_tournament.matches))
        self.assertEquals(json_data['alias_to_id_map'], [])

        # spot check 1 match
        match = json_data['matches'][0]
        self.assertEquals(len(match.keys()), 2)

    def test_get_tournament_pending_unauth(self):
        pending_tournament = self.norcal_dao.get_all_pending_tournaments(regions=['norcal'])[0]
        data = self.app.get('/norcal/tournaments/' + str(pending_tournament.id)).data
        self.assertEqual(data, '"Permission denied"', msg=data)

    @patch('server.get_user_from_request')
    def test_put_alias_mapping(self, mock_get_user_from_request):
        mock_get_user_from_request.return_value = self.user
        pending_tournament = self.norcal_dao.get_all_pending_tournaments(regions=['norcal'])[0]
        self.assertEquals(pending_tournament.regions, ['norcal'])

        player_tag = pending_tournament.players[0]
        real_player = self.norcal_dao.get_all_players()[0]
        mapping = AliasMapping(player_alias=player_tag, player_id=real_player.id)
        self.assertFalse(mapping in pending_tournament.alias_to_id_map)

        pending_tournament.set_alias_id_mapping(player_tag, real_player.id)
        pending_tournament_json = pending_tournament.dump(context='web', exclude=('raw',))

        # test put
        response = self.app.put('/norcal/pending_tournaments/' + str(pending_tournament.id),
            data=json.dumps(pending_tournament_json), content_type='application/json')
        json_data = json.loads(response.data)

        self.assertEquals(str(pending_tournament.id), json_data['id'])

        pending_tournament_from_db = self.norcal_dao.get_pending_tournament_by_id(ObjectId(json_data['id']))
        self.assertIsNotNone(pending_tournament)
        self.assertTrue(mapping in pending_tournament_from_db.alias_to_id_map)

    def test_get_rankings(self):
        data = self.app.get('/norcal/rankings').data
        json_data = json.loads(data)
        db_ranking = self.norcal_dao.get_latest_ranking()

        self.assertEquals(len(json_data.keys()), 6)
        self.assertEquals(json_data['time'], db_ranking.time.strftime("%x"))
        self.assertEquals(json_data['tournaments'], [str(t) for t in db_ranking.tournaments])
        self.assertEquals(json_data['region'], self.norcal_dao.region_id)
        self.assertEquals(len(json_data['ranking']), len(db_ranking.ranking))

        # spot check first and last ranking entries
        ranking_entry = json_data['ranking'][0]
        db_ranking_entry = db_ranking.ranking[0]
        self.assertEquals(len(ranking_entry.keys()), 4)
        self.assertEquals(ranking_entry['rank'], db_ranking_entry.rank)
        self.assertEquals(ranking_entry['id'], str(db_ranking_entry.player))
        self.assertEquals(ranking_entry['name'], self.norcal_dao.get_player_by_id(db_ranking_entry.player).name)

        self.assertTrue(ranking_entry['rating'] > 24.3)
        ranking_entry = json_data['ranking'][-1]
        db_ranking_entry = db_ranking.ranking[-1]
        self.assertEquals(len(ranking_entry.keys()), 4)
        self.assertEquals(ranking_entry['rank'], db_ranking_entry.rank)
        self.assertEquals(ranking_entry['id'], str(db_ranking_entry.player))
        self.assertEquals(ranking_entry['name'], self.norcal_dao.get_player_by_id(db_ranking_entry.player).name)
        self.assertTrue(ranking_entry['rating'] > -3.86)

    def test_get_rankings_ignore_invalid_player_id(self):
        # delete a player that exists in the rankings
        db_ranking = self.norcal_dao.get_latest_ranking()
        player_to_delete = self.norcal_dao.get_player_by_id(db_ranking.ranking[1].player)
        self.norcal_dao.delete_player(player_to_delete)

        data = self.app.get('/norcal/rankings').data
        json_data = json.loads(data)
        db_ranking = self.norcal_dao.get_latest_ranking()

        self.assertEquals(len(json_data.keys()), 6)
        self.assertEquals(json_data['time'], db_ranking.time.strftime("%x"))
        self.assertEquals(json_data['tournaments'], [str(t) for t in db_ranking.tournaments])
        self.assertEquals(json_data['region'], self.norcal_dao.region_id)

        # subtract 1 for the player we removed
        self.assertEquals(len(json_data['ranking']), len(db_ranking.ranking) - 1)

        # spot check first and last ranking entries
        ranking_entry = json_data['ranking'][0]
        db_ranking_entry = db_ranking.ranking[0]
        self.assertEquals(len(ranking_entry.keys()), 4)
        self.assertEquals(ranking_entry['rank'], db_ranking_entry.rank)
        self.assertEquals(ranking_entry['id'], str(db_ranking_entry.player))
        self.assertEquals(ranking_entry['name'], self.norcal_dao.get_player_by_id(db_ranking_entry.player).name)
        self.assertTrue(ranking_entry['rating'] > 24.3)

        ranking_entry = json_data['ranking'][-1]
        db_ranking_entry = db_ranking.ranking[-1]
        self.assertEquals(len(ranking_entry.keys()), 4)
        self.assertEquals(ranking_entry['rank'], db_ranking_entry.rank)
        self.assertEquals(ranking_entry['id'], str(db_ranking_entry.player))
        self.assertEquals(ranking_entry['name'], self.norcal_dao.get_player_by_id(db_ranking_entry.player).name)
        self.assertTrue(ranking_entry['rating'] > -3.86)

    @patch('server.get_user_from_request')
    @patch('server.datetime')
    def test_post_rankings(self, mock_datetime, mock_get_user_from_request):
        now = datetime(2014, 11, 2)

        mock_datetime.now.return_value = now
        mock_get_user_from_request.return_value = self.user

        data = self.app.post('/norcal/rankings').data
        json_data = json.loads(data)
        db_ranking = self.norcal_dao.get_latest_ranking()

        self.assertEquals(now, db_ranking.time)
        self.assertEquals(json_data['time'], db_ranking.time.strftime("%x"))
        self.assertEquals(len(json_data['ranking']), len(db_ranking.ranking))

    @patch('server.get_user_from_request')
    @patch('server.datetime')
    def test_post_rankings_with_params(self, mock_datetime, mock_get_user_from_request):
        now = datetime(2014, 11, 2)

        mock_datetime.now.return_value = now
        mock_get_user_from_request.return_value = self.user

        the_data = {
            'ranking_num_tourneys_attended': 3,
            'ranking_activity_day_limit': 1,
            'tournament_qualified_day_limit': 999
        }
        data = self.app.post('/norcal/rankings', data=json.dumps(the_data), content_type='application/json').data
        json_data = json.loads(data)
        db_ranking = self.norcal_dao.get_latest_ranking()

        self.assertEquals(now, db_ranking.time)
        self.assertEquals(json_data['time'], db_ranking.time.strftime("%x"))
        self.assertEquals(len(json_data['ranking']), 0)

    @patch('server.get_user_from_request')
    def test_post_rankings_permission_denied(self, mock_get_user_from_request):
        mock_get_user_from_request.return_value = self.user

        response = self.app.post('/texas/rankings')
        self.assertEquals(response.status_code, 403)
        self.assertEquals(response.data, '"Permission denied"')

    @patch('server.get_user_from_request')
    def test_put_rankings(self, mock_get_user_from_request):
        now = datetime(2014, 11, 2)

        the_data = {
            'ranking_num_tourneys_attended': 3,
            'ranking_activity_day_limit': 90,
            'tournament_qualified_day_limit': 999
        }

        mock_get_user_from_request.return_value = self.user

        data = self.app.put('/norcal/rankings',data=json.dumps(the_data), content_type='application/json').data
        json_data = json.loads(data)

        self.assertEqual(json_data['ranking_num_tourneys_attended'], 3)
        self.assertEqual(json_data['ranking_activity_day_limit'], 90)
        self.assertEqual(json_data['tournament_qualified_day_limit'], 999)

    @patch('server.get_user_from_request')
    def test_put_rankings_permission_denied(self, mock_get_user_from_request):
        mock_get_user_from_request.return_value = self.user

        the_data = {
            'ranking_num_tourneys_attended': 3,
            'ranking_activity_day_limit': 90,
            'tournament_qualified_day_limit': 999
        }

        response = self.app.put('/texas/rankings', data=json.dumps(the_data), content_type='application/json')
        self.assertEquals(response.status_code, 403)
        self.assertEquals(response.data, '"Permission denied"')

    def test_get_matches(self):
        player = self.norcal_dao.get_player_by_alias('gar')
        data = self.app.get('/norcal/matches/' + str(player.id)).data
        json_data = json.loads(data)

        self.assertEquals(len(json_data.keys()), 4)

        self.assertEquals(len(json_data['player'].keys()), 2)
        self.assertEquals(json_data['player']['id'], str(player.id))
        self.assertEquals(json_data['player']['name'], player.name)
        self.assertEquals(json_data['wins'], 3)
        self.assertEquals(json_data['losses'], 4)

        matches = json_data['matches']
        self.assertEquals(len(matches), 7)

        # spot check a few matches
        match = matches[0]
        opponent = self.norcal_dao.get_player_by_alias('darrell')
        tournament = self.norcal_dao.get_all_tournaments(regions=['norcal'])[0]
        self.assertEquals(len(match.keys()), 6)
        self.assertEquals(match['opponent_id'], str(opponent.id))
        self.assertEquals(match['opponent_name'], opponent.name)
        self.assertEquals(match['result'], 'lose')
        self.assertEquals(match['tournament_id'], str(tournament.id))
        self.assertEquals(match['tournament_name'], tournament.name)
        self.assertEquals(match['tournament_date'], tournament.date.strftime("%x"))

        match = matches[2]
        opponent = self.norcal_dao.get_player_by_alias('eric')
        tournament = self.norcal_dao.get_all_tournaments(regions=['norcal'])[1]
        self.assertEquals(len(match.keys()), 6)
        self.assertEquals(match['opponent_id'], str(opponent.id))
        self.assertEquals(match['opponent_name'], opponent.name)
        self.assertEquals(match['result'], 'win')
        self.assertEquals(match['tournament_id'], str(tournament.id))
        self.assertEquals(match['tournament_name'], tournament.name)
        self.assertEquals(match['tournament_date'], tournament.date.strftime("%x"))

    def test_get_matches_with_opponent(self):
        player = self.norcal_dao.get_player_by_alias('gar')
        opponent = self.norcal_dao.get_player_by_alias('tang')
        data = self.app.get('/norcal/matches/' + str(player.id) + "?opponent=" + str(opponent.id)).data
        json_data = json.loads(data)

        self.assertEquals(len(json_data.keys()), 5)
        self.assertEquals(json_data['wins'], 0)
        self.assertEquals(json_data['losses'], 1)

        self.assertEquals(len(json_data['player'].keys()), 2)
        self.assertEquals(json_data['player']['id'], str(player.id))
        self.assertEquals(json_data['player']['name'], player.name)

        self.assertEquals(len(json_data['opponent'].keys()), 2)
        self.assertEquals(json_data['opponent']['id'], str(opponent.id))
        self.assertEquals(json_data['opponent']['name'], opponent.name)

        matches = json_data['matches']
        self.assertEquals(len(matches), 1)

        match = matches[0]
        tournament = self.norcal_dao.get_all_tournaments(regions=['norcal'])[0]
        self.assertEquals(len(match.keys()), 6)
        self.assertEquals(match['opponent_id'], str(opponent.id))
        self.assertEquals(match['opponent_name'], opponent.name)
        self.assertEquals(match['result'], 'lose')
        self.assertEquals(match['tournament_id'], str(tournament.id))
        self.assertEquals(match['tournament_name'], tournament.name)
        self.assertEquals(match['tournament_date'], tournament.date.strftime("%x"))

    @patch('server.get_user_from_request')
    def test_get_current_user(self, mock_get_user_from_request):
        mock_get_user_from_request.return_value = self.user
        data = self.app.get('/users/session').data
        json_data = json.loads(data)

        self.assertEquals(json_data['id'], self.user_id)

    @patch('server.get_user_from_request')
    def test_put_tournament_name_change(self, mock_get_user_from_request):
        #initial setup
        mock_get_user_from_request.return_value = self.user
        dao = self.norcal_dao
        #pick a tournament
        tournaments_from_db = dao.get_all_tournaments(regions=['norcal'])
        the_tourney = dao.get_tournament_by_id(tournaments_from_db[0].id)

        #save info about it
        tourney_id = the_tourney.id
        old_date = the_tourney.date
        old_matches = the_tourney.matches
        old_players = the_tourney.players
        old_regions = the_tourney.regions
        old_type = the_tourney.type

        #construct info for first test
        new_tourney_name = "jessesGodlikeTourney"
        raw_dict = {'name': new_tourney_name}
        test_data = json.dumps(raw_dict)

        #try overwriting an existing tournament and changing just its name, make sure all the other attributes are fine
        rv = self.app.put('/norcal/tournaments/' + str(tourney_id), data=test_data, content_type='application/json')
        self.assertEqual(rv.status, '200 OK')
        the_tourney = dao.get_tournament_by_id(tourney_id)
        self.assertEquals(the_tourney.name, new_tourney_name, msg=rv.data)
        self.assertEquals(old_date, the_tourney.date)
        self.assertEquals(old_matches, the_tourney.matches)
        self.assertEquals(old_players, the_tourney.players)
        self.assertEquals(old_regions, the_tourney.regions)
        self.assertEquals(old_type, the_tourney.type)

    @patch('server.get_user_from_request')
    def test_put_tournament_everything_change(self, mock_get_user_from_request):
        #initial setup
        mock_get_user_from_request.return_value = self.user
        dao = self.norcal_dao
        #pick a tournament
        tournaments_from_db = dao.get_all_tournaments(regions=['norcal'])
        the_tourney = dao.get_tournament_by_id(tournaments_from_db[0].id)

        #save info about it
        tourney_id = the_tourney.id
        new_tourney_name = "jessesGodlikeTourney"
        old_type = the_tourney.type
        #setup for test 2

        # add new players to dao
        player1_obj = Player(
            name='testshroomed',
            aliases=['testshroomed'],
            ratings={'norcal': Rating()},
            regions=['norcal'],
            id=ObjectId())
        player2_obj = Player(
            name='testpewpewu',
            aliases=['testpewpewu'],
            ratings={'norcal': Rating()},
            regions=['norcal', 'socal'],
            id=ObjectId())
        dao.insert_player(player1_obj)
        dao.insert_player(player2_obj)


        player1_dict = {'id': str(player1_obj.id), 'name': player1_obj.name}
        player2_dict = {'id': str(player2_obj.id), 'name': player2_obj.name}
        match1_dict = {
            'winner_id': player1_dict['id'],
            'winner_name': player1_dict['name'],
            'loser_id': player2_dict['id'],
            'loser_name': player2_dict['name'],
            'excluded': False,
            'match_id': 0,
        }
        match2_dict = {
            'winner_id': player2_dict['id'],
            'winner_name': player2_dict['name'],
            'loser_id': player1_dict['id'],
            'loser_name': player1_dict['name'],
            'excluded': True,
            'match_id': 1,
        }

        new_players = [player1_dict, player2_dict]
        new_matches = [match1_dict, match2_dict]

        new_date = datetime.now()
        new_regions = ("norcal", "socal")
        raw_dict = {'name': new_tourney_name,
                    'date': new_date.strftime("%m/%d/%y"),
                    'matches': new_matches,
                    'regions': new_regions,
                    'players': new_players}
        test_data = json.dumps(raw_dict)

        # try overwriting all its writeable attributes: date players matches regions
        rv = self.app.put('/norcal/tournaments/' + str(tourney_id), data=test_data, content_type='application/json')
        self.assertEqual(rv.status, '200 OK')
        json_data = json.loads(rv.data)

        # check that things are correct
        self.assertEquals(json_data['name'], new_tourney_name)
        self.assertEquals(json_data['date'], new_date.strftime('%m/%d/%y'))
        for m1, m2 in zip(json_data['matches'], new_matches):
            self.assertEqual(m1['winner_id'], m2['winner_id'])
            self.assertEqual(m1['winner_name'], m2['winner_name'])
            self.assertEqual(m1['loser_id'], m2['loser_id'])
            self.assertEqual(m1['loser_name'], m2['loser_name'])
            self.assertEqual(m1['excluded'], m2['excluded'])
            self.assertEqual(m1['match_id'], m2['match_id'])
        for p1, p2 in zip(json_data['players'], new_players):
            self.assertEqual(p1['id'], p2['id'])
            self.assertEqual(p1['name'], p2['name'])
        self.assertEquals(set(json_data['regions']), set(new_regions))

        the_tourney = dao.get_tournament_by_id(tourney_id)
        self.assertEquals(new_tourney_name, the_tourney.name)
        self.assertEquals(new_date.toordinal(), the_tourney.date.toordinal())
        for m1, m2 in zip(new_matches, the_tourney.matches):
            self.assertEqual(m1['winner_id'], str(m2.winner))
            self.assertEqual(m1['loser_id'], str(m2.loser))

        self.assertEquals(
            set([player1_obj.id, player2_obj.id]),
            set(the_tourney.players))
        self.assertEquals(set(new_regions), set(the_tourney.regions))
        self.assertEquals(old_type, the_tourney.type)

    def test_put_tournament_invalid_id(self):
        #construct info
        new_tourney_name = "jessesGodlikeTourney"
        raw_dict = {'name': new_tourney_name}
        test_data = json.dumps(raw_dict)
        # try sending one with an invalid tourney ID
        rv = self.app.put('/norcal/tournaments/' + str(ObjectId()), data=test_data, content_type='application/json')
        self.assertEquals(rv.status, '404 NOT FOUND')

    @patch('server.get_user_from_request')
    def test_put_tournament_invalid_player_name(self, mock_get_user_from_request):
        #initial setup
        mock_get_user_from_request.return_value = self.user
        dao = self.norcal_dao
        #pick a tournament
        tournaments_from_db = dao.get_all_tournaments(regions=['norcal'])
        the_tourney = tournaments_from_db[0]
        #save info about it
        tourney_id = the_tourney.id
        #non string player name
        raw_dict = {'players': ("abc", 123)}
        test_data = json.dumps(raw_dict)
        rv = self.app.put('/norcal/tournaments/' + str(tourney_id), data=test_data, content_type='application/json')
        self.assertEquals(rv.status, '400 BAD REQUEST')

    @patch('server.get_user_from_request')
    def test_put_tournament_invalid_winner(self, mock_get_user_from_request):
        #initial setup
        mock_get_user_from_request.return_value = self.user
        dao = self.norcal_dao
        #pick a tournament
        tournaments_from_db = dao.get_all_tournaments(regions=['norcal'])
        the_tourney = tournaments_from_db[0]
        #save info about it
        tourney_id = the_tourney.id
        #match with numerical winner
        raw_dict = {'matches': {'winner': 123, 'loser': 'bob'}}
        test_data = json.dumps(raw_dict)
        rv = self.app.put('/norcal/tournaments/' + str(tourney_id), data=test_data, content_type='application/json')
        self.assertEquals(rv.status, '400 BAD REQUEST')

    @patch('server.get_user_from_request')
    def test_put_tournament_invalid_types_loser(self, mock_get_user_from_request):
        #initial setup
        mock_get_user_from_request.return_value = self.user
        dao = self.norcal_dao
        #pick a tournament
        tournaments_from_db = dao.get_all_tournaments(regions=['norcal'])
        the_tourney = tournaments_from_db[0]
        #save info about it
        tourney_id = the_tourney.id
        #match with numerical loser
        raw_dict = {'matches': {'winner': 'bob', 'loser': 123}}
        test_data = json.dumps(raw_dict)
        rv = self.app.put('/norcal/tournaments/' + str(tourney_id), data=test_data, content_type='application/json')
        self.assertEquals(rv.status, '400 BAD REQUEST')

    @patch('server.get_user_from_request')
    def test_put_tournament_invalid_types_both(self, mock_get_user_from_request):
        #initial setup
        mock_get_user_from_request.return_value = self.user
        dao = self.norcal_dao
        #pick a tournament
        tournaments_from_db = dao.get_all_tournaments(regions=['norcal'])
        the_tourney = tournaments_from_db[0]
        #save info about it
        tourney_id = the_tourney.id
        #match with both numerical
        raw_dict = {'matches': {'winner': 1234, 'loser': 123}}
        test_data = json.dumps(raw_dict)
        rv = self.app.put('/norcal/tournaments/' + str(tourney_id), data=test_data, content_type='application/json')
        self.assertEquals(rv.status, '400 BAD REQUEST')

    @patch('server.get_user_from_request')
    def test_put_tournament_invalid_region(self, mock_get_user_from_request):
        #initial setup
        mock_get_user_from_request.return_value = self.user
        dao = self.norcal_dao
        #pick a tournament
        tournaments_from_db = dao.get_all_tournaments(regions=['norcal'])
        the_tourney = tournaments_from_db[0]
        #save info about it
        tourney_id = the_tourney.id
        #match with both numerical
        raw_dict = {'regions': ("abc", 123)}
        test_data = json.dumps(raw_dict)
        rv = self.app.put('/norcal/tournaments/' + str(tourney_id), data=test_data, content_type='application/json')
        self.assertEquals(rv.status, '400 BAD REQUEST')

    @patch('server.get_user_from_request')
    def test_put_tournament_invalid_matches(self, mock_get_user_from_request):
        #initial setup
        mock_get_user_from_request.return_value = self.user
        dao = self.norcal_dao
        #pick a tournament
        tournaments_from_db = dao.get_all_tournaments(regions=['norcal'])
        the_tourney = tournaments_from_db[0]
        #save info about it
        tourney_id = the_tourney.id
        #match with both numerical
        raw_dict = {'matches': 123}
        test_data = json.dumps(raw_dict)
        rv = self.app.put('/norcal/tournaments/' + str(tourney_id), data=test_data, content_type='application/json')
        self.assertEquals(rv.status, '400 BAD REQUEST')

    @patch('server.get_user_from_request')
    def test_put_tournament_permission_denied(self, mock_get_user_from_request):
        mock_get_user_from_request.return_value = self.user
        dao = self.texas_dao
        tournaments_from_db = dao.get_all_tournaments(regions=['texas'])
        the_tourney = tournaments_from_db[0]
        response = self.app.put('/texas/tournaments/' + str(the_tourney.id), data = '{}', content_type='application/json')
        self.assertEquals(response.status_code, 403)
        self.assertEquals(response.data, '"Permission denied"')

    @patch('server.get_user_from_request')
    def test_put_player_update_name(self, mock_get_user_from_request):
        #setup
        mock_get_user_from_request.return_value = self.user
        dao = self.norcal_dao
        players = dao.get_all_players()
        the_player = players[0]
        player_id = the_player.id
        old_regions = the_player.regions
        old_aliases = the_player.aliases
        old_ratings = the_player.ratings

        #construct info for first test
        new_name = 'someone'
        raw_dict = {'name': new_name}
        test_data = json.dumps(raw_dict)

        #test updating name
        rv = self.app.put('/norcal/players/' + str(the_player.id), data=test_data, content_type='application/json')
        self.assertEqual(rv.status, '200 OK')
        the_player = dao.get_player_by_id(player_id)
        self.assertEqual(the_player.ratings, old_ratings)
        self.assertEqual(set(the_player.aliases), set(old_aliases))
        self.assertEqual(set(the_player.regions), set(old_regions))
        self.assertEqual(the_player.name, new_name)

    @patch('server.get_user_from_request')
    def test_put_player_update_aliases(self, mock_get_user_from_request):
        #setup
        mock_get_user_from_request.return_value = self.user
        dao = self.norcal_dao
        players = dao.get_all_players()
        the_player = players[0]
        player_id = the_player.id
        old_regions = the_player.regions
        old_ratings = the_player.ratings

        #first, change their name
        new_name = 'someone'
        raw_dict = {'name': new_name}
        test_data = json.dumps(raw_dict)

        rv = self.app.put('/norcal/players/' + str(the_player.id), data=test_data, content_type='application/json')
        self.assertEqual(rv.status, '200 OK')

        #construct info for second test
        new_aliases = ('someone', 'someoneelse', 'unknowndude')
        raw_dict = {'aliases': new_aliases}
        test_data = json.dumps(raw_dict)

        #test updating aliases
        rv = self.app.put('/norcal/players/' + str(the_player.id), data=test_data, content_type='application/json')
        self.assertEqual(rv.status, '200 OK', msg=rv.data)
        the_player = dao.get_player_by_id(player_id)
        self.assertEqual(set(the_player.aliases), set(new_aliases))
        self.assertEqual(the_player.ratings, old_ratings)
        self.assertEqual(set(the_player.regions), set(old_regions))

    @patch('server.get_user_from_request')
    def test_put_player_invalid_aliases(self, mock_get_user_from_request):
        #setup
        mock_get_user_from_request.return_value = self.user
        dao = self.norcal_dao
        players = dao.get_all_players()
        the_player = players[0]

        #construct info for third test
        new_aliases = ('nope', 'someoneelse', 'unknowndude')
        raw_dict = {'aliases': new_aliases}
        test_data = json.dumps(raw_dict)

        #test updating aliases with invalid aliases list
        rv = self.app.put('/norcal/players/' + str(the_player.id), data=test_data, content_type='application/json')
        self.assertEquals(rv.status, '400 BAD REQUEST')

    @patch('server.get_user_from_request')
    def test_put_player_update_regions(self, mock_get_user_from_request):
        #setup
        mock_get_user_from_request.return_value = self.user
        dao = self.norcal_dao
        players = dao.get_all_players()
        the_player = players[0]
        player_id = the_player.id
        old_ratings = the_player.ratings

        #construct info for fourth test
        new_regions = ('norcal', 'nyc')
        raw_dict = {'regions': new_regions}
        test_data = json.dumps(raw_dict)

        #test updating regions
        rv = self.app.put('/norcal/players/' + str(the_player.id), data=test_data, content_type='application/json')
        self.assertEqual(rv.status, '200 OK', msg=rv.data)
        the_player = dao.get_player_by_id(player_id)
        self.assertEqual(the_player.ratings, old_ratings)
        self.assertEqual(set(the_player.regions), set(new_regions))

    def test_put_player_not_found(self):
        #construct info for test
        new_regions = ('norcal', 'nyc')
        raw_dict = {'regions': new_regions}
        test_data = json.dumps(raw_dict)
        #test player not found
        rv = self.app.put('/norcal/players/' + str(ObjectId()), data=test_data, content_type='application/json')
        self.assertEquals(rv.status, '404 NOT FOUND')

    @patch('server.get_user_from_request')
    def test_put_player_nonstring_aliases(self, mock_get_user_from_request):
        #setup
        mock_get_user_from_request.return_value = self.user
        dao = self.norcal_dao
        players = dao.get_all_players()
        the_player = players[0]
        #construct info for test
        raw_dict = {'aliases': ('abc', 123)}
        test_data = json.dumps(raw_dict)

        #test updating regions
        rv = self.app.put('/norcal/players/' + str(the_player.id), data=test_data, content_type='application/json')
        self.assertEquals(rv.status, '400 BAD REQUEST')

    @patch('server.get_user_from_request')
    def test_put_player_nonstring_regions(self, mock_get_user_from_request):
        #setup
        mock_get_user_from_request.return_value = self.user
        dao = self.norcal_dao
        players = dao.get_all_players()
        the_player = players[0]
        player_id = the_player.id
        #construct info for test
        aliases = ('norcal', 'nyc')
        raw_dict = {'aliases': ('abc', 123)}
        test_data = json.dumps(raw_dict)

        #test updating regions
        rv = self.app.put('/norcal/players/' + str(the_player.id), data=test_data, content_type='application/json')
        self.assertEquals(rv.status, '400 BAD REQUEST')

    @patch('server.get_user_from_request')
    def test_delete_player(self, mock_get_user_from_request):
        mock_get_user_from_request.return_value = self.user

        # Add a new player to delete (because it won't have any matches).
        player_id = self.norcal_dao.insert_player(
            Player.create_with_default_values('new player', 'norcal'))
        self.assertIsNotNone(self.norcal_dao.get_player_by_id(player_id))

        response = self.app.delete('/norcal/players/' + str(player_id))

        self.assertEquals(response.status_code, 200)
        self.assertIsNone(self.norcal_dao.get_player_by_id(player_id))

    @patch('server.get_user_from_request')
    def test_delete_player_still_has_matches(self, mock_get_user_from_request):
        mock_get_user_from_request.return_value = self.user

        player_id  = self.norcal_dao.get_player_by_alias('gar').id

        response = self.app.delete('/norcal/players/' + str(player_id))

        self.assertEquals(response.status_code, 400)
        self.assertIsNotNone(self.norcal_dao.get_player_by_id(player_id))

    @patch('server.get_user_from_request')
    def test_delete_player_wrong_region_admin(self, mock_get_user_from_request):
        mock_get_user_from_request.return_value = self.user
        player_id = self.norcal_dao.insert_player(
            Player.create_with_default_values('new player', 'texas'))
        response = self.app.delete('/texas/players/' + str(player_id))
        self.assertEquals(response.status_code, 403, msg=response.status_code)

    def test_delete_player_unauth(self):
        player_id = self.norcal_dao.insert_player(
            Player.create_with_default_values('new player', 'norcal'))
        response = self.app.delete('/norcal/players/' + str(player_id))
        self.assertEquals(response.status_code, 403, msg=response.status_code)

    @patch('server.get_user_from_request')
    def test_put_merge(self, mock_get_user_from_request):
        mock_get_user_from_request.return_value = self.user
        dao = self.norcal_dao
        all_players = dao.get_all_players()
        player_one = all_players[0]

        # dummy player to merge
        player_two = Player(
            name='blah',
            aliases=['blah'],
            ratings=dict(),
            regions=['norcal'],
            id=ObjectId())
        dao.insert_player(player_two)

        raw_dict = {'target_player_id': str(player_one.id), 'source_player_id' : str(player_two.id) }
        test_data = json.dumps(raw_dict)
        rv = self.app.put('/norcal/merges', data=str(test_data), content_type='application/json')
        self.assertEquals(rv.status, '200 OK', msg=rv.data)

        data_dict = json.loads(rv.data)
        merge_id = data_dict['id']
        self.assertTrue(merge_id, msg=merge_id)
        # okay, now look in the dao and see if the merge is actually in there
        the_merge = dao.get_merge(ObjectId(merge_id))

        # assert the correct player is in the correct place
        self.assertTrue(the_merge, msg=merge_id)
        self.assertEquals(the_merge.target_player_obj_id, player_one.id)
        self.assertEquals(the_merge.source_player_obj_id, player_two.id)

    @patch('server.get_user_from_request')
    def test_put_merge_not_admin(self, mock_get_user_from_request):
        old_admin_regions = self.user.admin_regions
        self.user.admin_regions = []
        mock_get_user_from_request.return_value = self.user
        dao = self.texas_dao
        all_players = dao.get_all_players()
        player_one = all_players[0]
        player_two = all_players[1]
        raw_dict = {'target_player_id': str(player_one.id), 'source_player_id' : str(player_two.id) }
        test_data = json.dumps(raw_dict)
        rv = self.app.put('/texas/merges', data=str(test_data), content_type='application/json')
        self.assertEquals(rv.data, "\"user is not an admin\"")
        self.user.admin_regions = old_admin_regions

    @patch('server.get_user_from_request')
    def test_put_merge_invalid_id(self, mock_get_user_from_request):
        mock_get_user_from_request.return_value = self.user
        dao = self.norcal_dao
        raw_dict = {'target_player_id': "abcd", 'source_player_id' : "adskj" }
        test_data = json.dumps(raw_dict)
        rv = self.app.put('/norcal/merges', data=str(test_data), content_type='application/json')
        self.assertEquals(rv.data, "\"invalid ids, that wasn't an ObjectID\"", msg=rv.data)


    @patch('server.get_user_from_request')
    def test_put_merge_target_not_found(self, mock_get_user_from_request):
        mock_get_user_from_request.return_value = self.user
        dao = self.norcal_dao
        all_players = dao.get_all_players()
        player_one = all_players[0]
        player_two = all_players[1]
        raw_dict = {'target_player_id': "552f53650181b84aaaa01051", 'source_player_id' : str(player_two.id)  }
        test_data = json.dumps(raw_dict)
        rv = self.app.put('/norcal/merges', data=str(test_data), content_type='application/json')
        self.assertEquals(rv.data, "\"target_player not found\"", msg=rv.data)


    @patch('server.get_user_from_request')
    def test_put_merge_source_not_found(self, mock_get_user_from_request):
        mock_get_user_from_request.return_value = self.user
        dao = self.norcal_dao
        all_players = dao.get_all_players()
        player_one = all_players[0]
        player_two = all_players[1]
        raw_dict = {'target_player_id': str(player_one.id), 'source_player_id' : "552f53650181b84aaaa01051"  }
        test_data = json.dumps(raw_dict)
        rv = self.app.put('/norcal/merges', data=str(test_data), content_type='application/json')
        self.assertEquals(rv.data, "\"source_player not found\"", msg=rv.data)

    @patch('server.get_user_from_request')
    def test_post_tournament_from_tio(self, mock_get_user_from_request):
        mock_get_user_from_request.return_value = self.user
        dao = self.norcal_dao

        raw_dict = {}
        #then try sending a valid tio tournament and see if it works
        with open('test/data/Justice4.tio') as f:
            raw_dict['data'] = f.read()[3:] #weird hack, cause the first 3 bytes of a tio file are unprintable and that breaks something
        raw_dict['type'] = "tio"
        raw_dict['bracket'] = 'Bracket'
        the_data = json.dumps(raw_dict)
        response = self.app.post('/norcal/tournaments', data=the_data, content_type='application/json')
        for x in response.data:
            self.assertTrue(x in string.printable)
        self.assertEquals(response.status_code, 200, msg=str(response.data) + str(response.status_code))
        the_dict = json.loads(response.data)
        the_tourney = dao.get_pending_tournament_by_id(ObjectId(the_dict['id']))

        self.assertEqual(the_tourney.name, u'Justice 4')
        self.assertEqual(len(the_tourney.players), 48)

        self.assertEquals(the_dict['id'], str(the_tourney.id))
        self.assertEquals(the_tourney.type, 'tio')
        self.assertEquals(the_tourney.regions, ['norcal'])

        #let's spot check and make sure hax vs armada happens twice
        sweden_wins_count = 0
        for m in the_tourney.matches:
            if m.winner == "P4K | EMP | Armada" and m.loser == "VGBC | Hax":
                sweden_wins_count += 1
        self.assertEquals(sweden_wins_count, 2, msg="armada didn't double elim hax??")

    @patch('server.get_user_from_request')
    def test_post_tournament_from_tio_without_trim(self, mock_get_user_from_request): #TODO: rewrite to use new endpoint
        mock_get_user_from_request.return_value = self.user
        dao = self.norcal_dao
        #print "all regions:", ' '.join( x.id for x in dao.get_all_regions(self.mongo_client))
        raw_dict = {}
        #then try sending a valid tio tournament and see if it works
        with open('test/data/Justice4.tio') as f:
            raw_dict['data'] = f.read() #NO TRIM BB
       # raw_dict['tournament_name'] = "Justice4"
        raw_dict['type'] = "tio"
        raw_dict['bracket'] = 'Bracket'
        the_data = json.dumps(raw_dict)
        response = self.app.post('/norcal/tournaments', data=the_data, content_type='application/json')
        self.assertEquals(response.status_code, 503, msg=response.data)

    def test_put_session(self):
        # TODO: refactor to use dao
        result = self.users_col.find({"username": "gar"})
        self.assertTrue(result.count() == 1, msg=result)
        username = "gar"
        passwd = "rip"
        raw_dict = {'username': username,
                    'password': passwd}
        the_data = json.dumps(raw_dict)
        response = self.app.put('/users/session', data=the_data, content_type='application/json')

        self.assertEquals(response.status_code, 200, msg=response.headers)
        self.assertTrue('Set-Cookie' in response.headers.keys(), msg=str(response.headers))
        cookie_string = response.headers['Set-Cookie']
        my_cookie = cookie_string.split('"')[1] #split sessionID out of cookie string
        result = self.sessions_col.find({"session_id": my_cookie})
        self.assertTrue(result.count() == 1, msg=str(result))

    def test_put_session_bad_creds(self):
        username = "gar"
        passwd = "stillworksongarpr"
        raw_dict = {}
        raw_dict['username'] = username
        raw_dict['password'] = passwd
        the_data = json.dumps(raw_dict)
        response = self.app.put('/users/session', data=the_data, content_type='application/json')
        self.assertEquals(response.status_code, 403, msg=response.data)

    def test_put_session_bad_user(self): #this test is to make sure we dont have username enumeration (up to a timing attack anyway)
        username = "evilgar"
        passwd = "stillworksongarpr"
        raw_dict = {}
        raw_dict['username'] = username
        raw_dict['password'] = passwd
        the_data = json.dumps(raw_dict)
        response = self.app.put('/users/session', data=the_data, content_type='application/json')
        self.assertEquals(response.status_code, 403, msg=response.data)

    @patch('server.get_user_from_request')
    def test_delete_finalized_tournament(self, mock_get_user_from_access_token):
        mock_get_user_from_access_token.return_value = self.user
        tournament = self.norcal_dao.get_all_tournaments(regions=['norcal'])[0]
        response = self.app.delete('/norcal/tournaments/' + str(tournament.id))
        self.assertEquals(response.status_code, 200)
        self.assertTrue(self.norcal_dao.get_tournament_by_id(tournament.id) is None, msg=self.norcal_dao.get_tournament_by_id(tournament.id))

    @patch('server.get_user_from_request')
    def test_delete_pending_tournament(self, mock_get_user_from_access_token):
        mock_get_user_from_access_token.return_value = self.user
        tournament = self.norcal_dao.get_all_pending_tournaments(regions=['norcal'])[0]
        response = self.app.delete('/norcal/tournaments/' + str(tournament.id))
        self.assertEquals(response.status_code, 200, msg=response.status_code)
        self.assertTrue(self.norcal_dao.get_pending_tournament_by_id(tournament.id) is None, msg=self.norcal_dao.get_pending_tournament_by_id(tournament.id))

    def test_delete_pending_tournament_unauth(self):
        tournament = self.norcal_dao.get_all_pending_tournaments(regions=['norcal'])[0]
        response = self.app.delete('/norcal/tournaments/' + str(tournament.id))
        self.assertEquals(response.status_code, 403, msg=response.status_code)

    def test_delete_finalized_tournament_unauth(self):
        tournament = self.norcal_dao.get_all_tournaments(regions=['norcal'])[0]
        response = self.app.delete('/norcal/tournaments/' + str(tournament.id))
        self.assertEquals(response.status_code, 403)
