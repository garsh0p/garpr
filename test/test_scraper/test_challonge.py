import unittest
from mock import patch
import scraper.challonge
from scraper.challonge import ChallongeScraper

URL = "http://www.fakeurl.com/asdf"
FILE_TEMPLATE = "test/scraper/data/challonge_%d.html"
NUM_FILES = 9

class TestChallongeScraper(unittest.TestCase):
    @patch('scraper.challonge.CHALLONGE_API_KEY_PATH', 'asdf')
    def setUp(self):
        print scraper.challonge.CHALLONGE_API_KEY_PATH
        self.scraper = ChallongeScraper(URL)
        self.files = self.load_all_files()

    def test_asdf(self):
        pass
