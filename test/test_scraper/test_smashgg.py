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

TEST_TOURNAMENT_ID = 11226
TEST_PLAYER_ID = 13932

class TestSmashGGScraper(unittest.TestCase):
    def setUp(self):
        self.tournament = SmashGGScraper(TEST_TOURNAMENT_ID)

    def test_tournament_creation(self):
        players = self.tournament.get_smashgg_players()
        player = self.tournament.get_player_by_id(TEST_PLAYER_ID)
        tags = self.tournament.get_players()

    def test_get_player_by_id(self):
        player = self.tournament.get_player_by_id(TEST_PLAYER_ID)
        self.assertEqual(player.name, 'Jose Angel Aldama')
        self.assertEqual(player.smash_tag, 'Lucky')
        self.assertEqual(player.region, 'SoCal')

    def test_get_players(self):
        self.assertEqual(len(self.tournament.get_players()), 29)

    def test_get_matches(self):
        self.assertEqual(len(self.tournament.get_matches()), 47)

