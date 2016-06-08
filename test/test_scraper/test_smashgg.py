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

TEST_TOURNAMENT_ID_1 = 11226
TEST_TOURNAMENT_ID_2 = 70949
TEST_PLAYER_ID_1 = 13932
TEST_PLAYER_ID_2 = 4442

class TestSmashGGScraper(unittest.TestCase):
    def setUp(self):
        self.tournament1 = SmashGGScraper(TEST_TOURNAMENT_ID_1)
        self.tournament2 = SmashGGScraper(TEST_TOURNAMENT_ID_2)

    def test_tournament_creation(self):
        players = self.tournament1.get_smashgg_players()
        player = self.tournament1.get_player_by_id(TEST_PLAYER_ID_1)
        tags = self.tournament1.get_players()

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

