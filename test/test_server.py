import unittest
import server
from mock import patch, Mock
import mongomock
from dao import Dao
from scraper.tio import TioScraper
from model import *
import json
import rankings
from bson.objectid import ObjectId
import requests
from datetime import datetime

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

        self.norcal_region = Region('norcal', 'Norcal')
        self.texas_region = Region('texas', 'Texas')
        Dao.insert_region(self.norcal_region, self.mongo_client)
        Dao.insert_region(self.texas_region, self.mongo_client)

        self.norcal_dao = Dao(NORCAL_REGION_NAME, mongo_client=self.mongo_client)
        self.texas_dao = Dao(TEXAS_REGION_NAME, mongo_client=self.mongo_client)

        self._import_files()

        now = datetime(2014, 11, 1)
        rankings.generate_ranking(self.norcal_dao, now=now)
        rankings.generate_ranking(self.texas_dao, now=now)

    def _import_files(self):
        for f in NORCAL_FILES:
            scraper = TioScraper(f[0], f[1])
            self._import_players(scraper, self.norcal_dao)
            player_map = self.norcal_dao.get_player_id_map_from_player_aliases(scraper.get_players())
            self.norcal_dao.insert_tournament(Tournament.from_scraper('tio', scraper, player_map, self.norcal_dao.region_id))

        for f in TEXAS_FILES:
            scraper = TioScraper(f[0], f[1])
            self._import_players(scraper, self.texas_dao)
            player_map = self.texas_dao.get_player_id_map_from_player_aliases(scraper.get_players())
            self.texas_dao.insert_tournament(Tournament.from_scraper('tio', scraper, player_map, self.texas_dao.region_id))

    def _import_players(self, scraper, dao):
        for player in scraper.get_players():
            db_player = dao.get_player_by_alias(player)
            if db_player is None:
                db_player = Player(
                        player, 
                        [player.lower()], 
                        {dao.region_id: TrueskillRating()},
                        [dao.region_id])
                dao.insert_player(db_player)

    def test_get_region_list(self):
        data = self.app.get('/regions').data

        expected_region_dict = {
                'regions': [
                    {'id': 'norcal', 'display_name': 'Norcal'},
                    {'id': 'texas', 'display_name': 'Texas'}
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
                expected_keys = set(['id', 'name'])
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
        expected_keys = set(['id', 'name'])
        self.assertEquals(set(json_player.keys()), expected_keys)
        self.assertEquals(ObjectId(json_player['id']), player.id)

    def test_get_player_list_case_insensitive(self):
        player = self.norcal_dao.get_player_by_alias('gar')

        data = self.app.get('/norcal/players?alias=GAR').data
        json_data = json.loads(data)
        self.assertEquals(len(json_data['players']), 1)

        json_player = json_data['players'][0]
        expected_keys = set(['id', 'name'])
        self.assertEquals(set(json_player.keys()), expected_keys)
        self.assertEquals(ObjectId(json_player['id']), player.id)

    def test_get_player_list_with_bad_alias(self):
        data = self.app.get('/norcal/players?alias=BADALIAS').data
        json_data = json.loads(data)
        self.assertEquals(len(json_data['players']), 0)

    def test_get_player(self):
        player = self.norcal_dao.get_player_by_alias('gar')
        data = self.app.get('/norcal/players/' + str(player.id)).data
        json_data = json.loads(data)

        self.assertEquals(len(json_data.keys()), 5)
        self.assertEquals(json_data['id'], str(player.id))
        self.assertEquals(json_data['name'], 'gar')
        self.assertEquals(json_data['aliases'], ['gar'])
        self.assertEquals(json_data['regions'], ['norcal'])
        self.assertTrue(json_data['ratings']['norcal']['mu'] > 25.9)
        self.assertTrue(json_data['ratings']['norcal']['sigma'] > 3.89)

        player = self.texas_dao.get_player_by_alias('wobbles')
        data = self.app.get('/texas/players/' + str(player.id)).data
        json_data = json.loads(data)

        self.assertEquals(len(json_data.keys()), 5)
        self.assertEquals(json_data['id'], str(player.id))
        self.assertEquals(json_data['name'], 'Wobbles')
        self.assertEquals(json_data['aliases'], ['wobbles'])
        self.assertEquals(json_data['regions'], ['texas'])
        self.assertTrue(json_data['ratings']['texas']['mu'] > 44.5)
        self.assertTrue(json_data['ratings']['texas']['sigma'] > 3.53)

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

    def test_get_tournament(self):
        tournament = self.norcal_dao.get_all_tournaments(regions=['norcal'])[0]
        data = self.app.get('/norcal/tournaments/' + str(tournament.id)).data
        json_data = json.loads(data)

        self.assertEquals(len(json_data.keys()), 7)
        self.assertEquals(json_data['id'], str(tournament.id))
        self.assertEquals(json_data['name'], 'BAM: 4 stocks is not a lead')
        self.assertEquals(json_data['type'], 'tio')
        self.assertEquals(json_data['date'], str(tournament.date))
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
        self.assertEquals(len(match.keys()), 4)
        self.assertEquals(match['winner_id'], str(db_match.winner))
        self.assertEquals(match['winner_name'], self.norcal_dao.get_player_by_id(ObjectId(match['winner_id'])).name)
        self.assertEquals(match['loser_id'], str(db_match.loser))
        self.assertEquals(match['loser_name'], self.norcal_dao.get_player_by_id(ObjectId(match['loser_id'])).name)
        match = json_data['matches'][-1]
        db_match = tournament.matches[-1]
        self.assertEquals(len(match.keys()), 4)
        self.assertEquals(match['winner_id'], str(db_match.winner))
        self.assertEquals(match['winner_name'], self.norcal_dao.get_player_by_id(ObjectId(match['winner_id'])).name)
        self.assertEquals(match['loser_id'], str(db_match.loser))
        self.assertEquals(match['loser_name'], self.norcal_dao.get_player_by_id(ObjectId(match['loser_id'])).name)

        # sanity tests for another region
        tournament = self.texas_dao.get_all_tournaments()[0]
        data = self.app.get('/texas/tournaments/' + str(tournament.id)).data
        json_data = json.loads(data)

        self.assertEquals(len(json_data.keys()), 7)
        self.assertEquals(json_data['id'], str(tournament.id))
        self.assertEquals(json_data['name'], 'FX Biweekly 6')
        self.assertEquals(json_data['type'], 'tio')
        self.assertEquals(json_data['date'], str(tournament.date))
        self.assertEquals(json_data['regions'], ['texas'])
        self.assertEquals(len(json_data['players']), len(tournament.players))
        self.assertEquals(len(json_data['matches']), len(tournament.matches))

    def test_get_rankings(self):
        data = self.app.get('/norcal/rankings').data
        json_data = json.loads(data)
        db_ranking = self.norcal_dao.get_latest_ranking()

        self.assertEquals(len(json_data.keys()), 4)
        self.assertEquals(json_data['time'], str(db_ranking.time))
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
        self.assertTrue(ranking_entry['rating'] > 33.2)
        ranking_entry = json_data['ranking'][-1]
        db_ranking_entry = db_ranking.ranking[-1]
        self.assertEquals(len(ranking_entry.keys()), 4)
        self.assertEquals(ranking_entry['rank'], db_ranking_entry.rank)
        self.assertEquals(ranking_entry['id'], str(db_ranking_entry.player))
        self.assertEquals(ranking_entry['name'], self.norcal_dao.get_player_by_id(db_ranking_entry.player).name)
        self.assertTrue(ranking_entry['rating'] > -3.86)

    # TODO write this test, or delete the endpoint
    def test_get_rankings_generate_new(self):
        pass

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

    @patch('server.requests', spec=requests)
    def test_get_user_from_access_token(self, mock_requests):
        user_id = 'asdf'
        user = User(user_id, ['norcal'])
        auth_header = 'auth'

        mock_response = Mock(spec=requests.Response)
        mock_response.json.return_value = {
            'data': {
                'app_id': server.fb_app_id,
                'is_valid': True,
                'user_id': user_id
            }
        }

        mock_requests.get.return_value = mock_response

        mock_dao = Mock(spec=Dao)
        mock_dao.get_or_create_user_by_id.return_value = user
        
        retrieved_user = server.get_user_from_access_token({'Authorization': auth_header}, mock_dao)
        self.assertEquals(retrieved_user.id, user.id)
        self.assertEquals(retrieved_user.admin_regions, user.admin_regions)

        expected_url = server.DEBUG_TOKEN_URL % (auth_header, server.fb_app_token)
        mock_requests.get.assert_called_once_with(expected_url)

        mock_dao.get_or_create_user_by_id.assert_called_once_with(user_id)

    @patch('server.requests', spec=requests)
    def test_get_user_from_access_token_invalid_app_id(self, mock_requests):
        user_id = 'asdf'
        auth_header = 'auth'

        mock_response = Mock(spec=requests.Response)
        mock_response.json.return_value = {
            'data': {
                'app_id': 'bad app id',
                'is_valid': True,
            }
        }

        mock_requests.get.return_value = mock_response

        with self.assertRaises(server.InvalidAccessToken):
            server.get_user_from_access_token({'Authorization': auth_header}, None)

        expected_url = server.DEBUG_TOKEN_URL % (auth_header, server.fb_app_token)
        mock_requests.get.assert_called_once_with(expected_url)

    @patch('server.requests', spec=requests)
    def test_get_user_from_access_token_invalid_response(self, mock_requests):
        user_id = 'asdf'
        auth_header = 'auth'

        mock_response = Mock(spec=requests.Response)
        mock_response.json.return_value = {
            'data': {
                'app_id': server.fb_app_id,
                'is_valid': False
            }
        }

        mock_requests.get.return_value = mock_response

        with self.assertRaises(server.InvalidAccessToken):
            server.get_user_from_access_token({'Authorization': auth_header}, None)

        expected_url = server.DEBUG_TOKEN_URL % (auth_header, server.fb_app_token)
        mock_requests.get.assert_called_once_with(expected_url)
