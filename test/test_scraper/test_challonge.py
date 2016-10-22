import unittest
from mock import patch, Mock
import scraper.challonge
from scraper.challonge import ChallongeScraper
import requests
import json
from datetime import datetime
import pytz
from model import AliasMatch

TEMPLATE_CONFIG_FILE_PATH = 'config/config.ini.template'
TEMPLATE_API_KEY = 'API_KEY'
TOURNAMENT_ID = 'faketournament'

TOURNAMENT_JSON_FILE = 'test/test_scraper/data/tournament.json'

# there are 3 extra matches at the end that have a null winner and/or loser
# these should be ignored
MATCHES_JSON_FILE = 'test/test_scraper/data/matches.json'

# Shroomed has a null name field but a valid username field
# MIOM | SFAT has spaces before and after
PARTICIPANTS_JSON_FILE = 'test/test_scraper/data/participants.json'

class TestChallongeScraper(unittest.TestCase):
    @patch('scraper.challonge.requests', spec=requests)
    def setUp(self, mock_requests):
        mock_tournament_response = Mock(spec=requests.Response)
        mock_matches_response = Mock(spec=requests.Response)
        mock_participants_response = Mock(spec=requests.Response)

        with open(TOURNAMENT_JSON_FILE) as f:
            self.tournament_json_dict = json.load(f)

        with open(MATCHES_JSON_FILE) as f:
            self.matches_json_dict = json.load(f)

        with open(PARTICIPANTS_JSON_FILE) as f:
            self.participants_json_dict = json.load(f)

        mock_tournament_response.status_code = 200
        mock_matches_response.status_code = 200
        mock_participants_response.status_code = 200

        mock_tournament_response.json.return_value = self.tournament_json_dict
        mock_matches_response.json.return_value = self.matches_json_dict
        mock_participants_response.json.return_value = self.participants_json_dict

        expected_tournament_url = scraper.challonge.TOURNAMENT_URL % TOURNAMENT_ID;
        expected_matches_url = scraper.challonge.MATCHES_URL % TOURNAMENT_ID;
        expected_participants_url = scraper.challonge.PARTICIPANTS_URL % TOURNAMENT_ID;

        mock_requests_return_values = {
                (expected_tournament_url, TEMPLATE_API_KEY): mock_tournament_response,
                (expected_matches_url, TEMPLATE_API_KEY): mock_matches_response,
                (expected_participants_url, TEMPLATE_API_KEY): mock_participants_response
        }
        mock_requests.get.side_effect = lambda url, **kwargs: mock_requests_return_values[(url, kwargs['params']['api_key'])]

        self.scraper = ChallongeScraper(TOURNAMENT_ID, TEMPLATE_CONFIG_FILE_PATH)

    def test_get_raw(self):
        raw = self.scraper.get_raw()

        self.assertEquals(len(raw.keys()), 3)
        self.assertEquals(raw['tournament'], self.tournament_json_dict)
        self.assertEquals(raw['matches'], self.matches_json_dict)
        self.assertEquals(raw['participants'], self.participants_json_dict)

    def test_get_name(self):
        self.assertEquals(self.scraper.get_name(), 'SF Game Night 21')

    def test_get_date(self):
        self.assertEquals(self.scraper.get_date().replace(tzinfo=None), datetime(2014, 10, 14, 20, 39, 30))

    def test_get_matches(self):
        matches = self.scraper.get_matches()
        self.assertEquals(len(matches), 81)
        self.assertEquals(matches[0], AliasMatch(winner='Tiamat', loser='Sharkboi'))
        self.assertEquals(matches[-1], AliasMatch(winner='Shroomed', loser='GC | Silentwolf'))
        self.assertEquals(matches[-2], AliasMatch(winner='GC | Silentwolf', loser='Shroomed'))
        self.assertEquals(matches[-3], AliasMatch(winner='GC | Silentwolf', loser='MIOM | SFAT'))

        # make sure none of the matches have a None
        for m in matches:
            self.assertIsNotNone(m.winner)
            self.assertIsNotNone(m.loser)

    def test_get_player(self):
        players = self.scraper.get_players()
        self.assertEquals(len(players), 41)
        self.assertTrue('Shroomed' in players)
        self.assertTrue('MIOM | SFAT' in players)
