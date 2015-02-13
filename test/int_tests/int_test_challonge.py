from scraper.challonge import ChallongeScraper
import unittest
import iso8601

TOURNAMENT_ID = "TNE_Singles"
scraper = ChallongeScraper(TOURNAMENT_ID)

class IntTestChallongeScraper(unittest.TestCase):
    def test_get_raw(self):
        raw = scraper.get_raw()
        self.assertTrue('tournament' in raw)
        self.assertTrue('matches' in raw)
        self.assertTrue('participants' in raw)

        self.assertTrue('tournament' in raw['tournament'])
        self.assertEquals(len(raw['matches']), 126)
        self.assertEquals(len(raw['participants']), 64)

    def test_get_name(self):
        self.assertEquals(scraper.get_name(), "The Next Episode")

    def test_get_date(self):
        self.assertEquals(scraper.get_date(), iso8601.parse_date("2014-03-23 17:28:34.647000-04:00"))

    def test_get_matches(self):
        self.assertEquals(len(scraper.get_matches()), 126)

    def test_get_players(self):
        self.assertEquals(len(scraper.get_players()), 64)
