import unittest
import requests
import json
import pytz
import scraper.smashgg
from mock import patch, Mock
from datetime import datetime
from model import MatchResult
from scraper.smashgg import SmashGGScraper

TEST_TOURNAMENT_ID = 11226
TEST_PLAYER_ID = 13932

class TestSmashGGScraper(unittest.TestCase):
    '''def test_get_raw(self):'''

    def test_tournament_creation(self):
        tournament = SmashGGScraper(TEST_TOURNAMENT_ID)
        players = tournament.get_players()
        player = tournament.get_player_by_id(TEST_PLAYER_ID)




