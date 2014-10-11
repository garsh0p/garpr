import unittest
from scraper.tio import TioScraper
from dateutil import parser

FILEPATH = "test/scraper/data/1.tio"
BRACKET_NAME = "singles bracket"

class TestTioScraper(unittest.TestCase):
    def setUp(self):
        self.scraper = TioScraper(FILEPATH, BRACKET_NAME)

    def test_get_raw(self):
        self.assertTrue(len(self.scraper.get_raw()) > 0)

    def test_get_name(self):
        self.assertEquals(self.scraper.get_name(), 'norcal monthlies #2')

    def test_get_date(self):
        self.assertEquals(self.scraper.get_date(), parser.parse('2014-03-16 00:00:00'))

    def test_get_matches(self):
        matches = self.scraper.get_matches()
        self.assertEquals(len(matches), 46)

    def test_get_players(self):
        players = self.scraper.get_players()
        self.assertEquals(len(players), 24)
