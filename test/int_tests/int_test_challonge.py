from scraper.challonge import ChallongeScraper
import unittest

TOURNAMENT_ID = "TNE_Singles"

class IntTestChallongeScraper(unittest.TestCase):
    def test_challonge(self):
        scraper = ChallongeScraper(TOURNAMENT_ID)

        raw = scraper.get_raw()
        self.assertTrue('tournament' in raw)
        self.assertTrue('matches' in raw)
        self.assertTrue('participants' in raw)

        self.assertTrue('tournament' in raw['tournament'])
        self.assertEquals(len(raw['matches']), 126)
        self.assertEquals(len(raw['participants']), 64)
