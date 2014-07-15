import unittest
from scraper.tio import TioScraper

FILEPATH = "test/scraper/data/1.tio"
BRACKET_NAME = "singles bracket"

class TestTioScraper(unittest.TestCase):
    def setUp(self):
        self.scraper = TioScraper(FILEPATH, BRACKET_NAME)

    def test_get_name(self):
        self.assertEquals(self.scraper.get_name(), 'norcal monthlies #2')

    def test_get_date(self):
        self.assertTrue(self.scraper.get_date().startswith('03/16/2014'))

    def test_get_matches(self):
        matches = self.scraper.get_matches()
        self.assertEquals(len(matches), 46)

    def test_get_players(self):
        players = self.scraper.get_players()
        self.assertEquals(len(players), 24)
