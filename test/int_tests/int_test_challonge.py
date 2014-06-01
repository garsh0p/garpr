from scraper.challonge import ChallongeScraper
import unittest

URL = "http://challonge.com/TNE_Singles"

class IntTestChallongeScraper(unittest.TestCase):
    def test_challonge(self):
        scraper = ChallongeScraper(URL)
        self.assertEquals(scraper.get_name(), "The Next Episode")
        self.assertEquals(len(scraper.get_matches()), 126)
