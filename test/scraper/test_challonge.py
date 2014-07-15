import unittest
import mock
from scraper.challonge import ChallongeScraper

URL = "http://www.fakeurl.com/asdf"
FILE_TEMPLATE = "test/scraper/data/challonge_%d.html"
NUM_FILES = 9

class TestChallongeScraper(unittest.TestCase):
    def setUp(self):
        self.scraper = ChallongeScraper(URL)
        self.files = self.load_all_files()

    # TODO add tests working with raw
