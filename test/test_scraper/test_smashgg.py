import unittest
import requests
import json
import pytz
import scraper.smashgg
from mock import patch, Mock
from datetime import datetime
from model import MatchResult
from scraper.smashgg import SmashGGPlayer
from scraper.smashgg import SmashGGScraper
TEST_URL_1 = 'https://smash.gg/tournament/htc-throwdown/brackets/10448/2096/6529'
TEST_URL_2 = 'https://smash.gg/tournament/tiger-smash-4/brackets/11097/21317/70949'
TEST_TOURNAMENT_ID_1 = 11226
TEST_TOURNAMENT_ID_2 = 70949
TEST_PLAYER_ID_1 = 13932
TEST_PLAYER_ID_2 = 4442

class TestSmashGGScraper(unittest.TestCase):
    def setUp(self):
        self.tournament1 = SmashGGScraper(TEST_TOURNAMENT_ID_1)
        self.tournament2 = SmashGGScraper(TEST_TOURNAMENT_ID_2)

    def test_get_tournament_id_from_url1(self):
        self.assertEqual(SmashGGScraper.get_tournament_id_from_url(TEST_URL_1), 6529)

    def test_get_tournament_id_from_url2(self):
        self.assertEqual(SmashGGScraper.get_tournament_id_from_url(TEST_URL_2), 70949)

    def test_get_player_by_id1(self):
        player = self.tournament1.get_player_by_id(TEST_PLAYER_ID_1)
        self.assertEqual(player.name, 'Jose Angel Aldama')
        self.assertEqual(player.smash_tag, 'Lucky')
        self.assertEqual(player.region, 'SoCal')

    def test_get_player_by_id2(self):
        player = self.tournament2.get_player_by_id(TEST_PLAYER_ID_2)
        self.assertEqual(player.name, 'Sami Muhanna')
        self.assertEqual(player.smash_tag, 'Druggedfox')
        self.assertEqual(player.region, 'GA')

    def test_get_players1(self):
        self.assertEqual(len(self.tournament1.get_players()), 32)

    def test_get_players2(self):
        self.assertEquals(len(self.tournament2.get_players()), 24)

    def test_get_matches1(self):
        self.assertEqual(len(self.tournament1.get_matches()), 47)

    def test_get_matches2(self):
        self.assertEquals(len(self.tournament2.get_matches()), 46)

