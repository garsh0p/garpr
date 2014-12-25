import unittest
from scraper.tio import TioScraper
from datetime import datetime
from model import MatchResult

# SFAT and Silentwolf have spaces before and after
FILEPATH = "test/test_scraper/data/1.tio"
BRACKET_NAME = "Singles"

class TestTioScraper(unittest.TestCase):
    def setUp(self):
        self.scraper = TioScraper.from_file(FILEPATH, BRACKET_NAME)

    def test_get_raw(self):
        self.assertTrue(len(self.scraper.get_raw()) > 0)

    def test_get_name(self):
        self.assertEquals(self.scraper.get_name(), 'BAM: i got 5 on it')

    def test_get_date(self):
        self.assertEquals(self.scraper.get_date(), datetime(2014, 10, 18))

    def test_get_matches(self):
        matches = self.scraper.get_matches()
        self.assertEquals(len(matches), 117)

        self.assertEquals(matches[0], MatchResult(winner='spookyman', loser='razr'))

        # grand finals set 2
        self.assertEquals(matches[-1], MatchResult(winner='GC|silent wolf', loser='MIOM|SFAT'))

        # grand finals set 1
        self.assertEquals(matches[-2], MatchResult(winner='MIOM|SFAT', loser='GC|silent wolf'))
    
        # losers finals
        self.assertEquals(matches[-3], MatchResult(winner='MIOM|SFAT', loser='shroomed'))

    def test_get_matches_invalid_bracket_name(self):
        with self.assertRaises(ValueError):
            self.scraper = TioScraper.from_file(FILEPATH, 'invalid bracket name')
            self.scraper.get_matches()

    def test_get_matches_one_grand_finals_set(self):
        self.scraper = TioScraper.from_file('test/test_scraper/data/2.tio', BRACKET_NAME)
        matches = self.scraper.get_matches()

        self.assertEquals(len(matches), 116)

        self.assertEquals(matches[0], MatchResult(winner='spookyman', loser='razr'))

        # grand finals set 1
        self.assertEquals(matches[-1], MatchResult(winner='GC|silent wolf', loser='MIOM|SFAT'))
    
        # losers finals
        self.assertEquals(matches[-2], MatchResult(winner='MIOM|SFAT', loser='shroomed'))

    def test_get_players(self):
        self.assertIsNone(self.scraper.players)
        players = self.scraper.get_players()
        self.assertEquals(len(players), 59)
        self.assertTrue('MIOM|SFAT' in players)
        self.assertTrue('GC|silent wolf' in players)

        # call it twice to make sure caching works
        self.assertIsNotNone(self.scraper.players)
        players = self.scraper.get_players()
        self.assertEquals(len(players), 59)
        self.assertTrue('MIOM|SFAT' in players)
        self.assertTrue('GC|silent wolf' in players)
