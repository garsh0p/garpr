from scraper.challonge import ChallongeScraper
import unittest

TOURNAMENT_ID = "sfgamenight8"

class IntTestChallongeScraper(unittest.TestCase):
    def test_challonge(self):
        scraper = ChallongeScraper(TOURNAMENT_ID)
        print scraper.get_name()
        print scraper.get_date()
        print scraper.get_players()
        matches = scraper.get_matches()
        for m in matches:
            print m
