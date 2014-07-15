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

    def load_all_files(self):
        """Returns a list of each file as a string"""
        files = []
        for i in xrange(0, NUM_FILES):
            with open(FILE_TEMPLATE % (i + 1)) as f:
                files.append(f.read())
        return files

    def create_mock_response(self, text):
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.text = text
        return mock_response

    @mock.patch('scraper.challonge.requests.get')
    def test_get_name(self, mock_get):
        '''
        mock_response = self.create_mock_response(self.files[0])
        mock_get.return_value = mock_response

        self.assertEquals(self.scraper.get_name(), "The Next Episode")

        mock_get.assert_called_once_with(URL)
        self.assertFalse(mock_response.called)
        
        # make sure we cached the response
        self.assertEquals(self.scraper.get_name(), "The Next Episode")
        mock_get.assert_called_once_with(URL)
        self.assertFalse(mock_response.called)
        '''
        print self.scraper.get_name()

    @mock.patch('scraper.challonge.requests.get')
    def test_get_matches(self, mock_get):
        def get_return_values(url):
            if url[-1].isdigit():
                return self.create_mock_response(self.files[int(url[-1]) - 1])
            # if we retrieve /log, return the last page
            else:
                return self.create_mock_response(self.files[-1])

        mock_get.side_effect = get_return_values

        matches = self.scraper.get_matches()
        self.assertEquals(len(matches), 126)

        self.assertTrue(matches[0].contains_players("Bizzarro Flame", "Kira"))
        self.assertEquals(matches[0].winner, "Bizzarro Flame")

        self.assertTrue(matches[-1].contains_players("Fly Amanita", "OXY_Westballz"))
        self.assertEquals(matches[-1].winner, "Fly Amanita")

        self.assertEquals(mock_get.call_count, 10)

        # make sure we cached the response
        matches = self.scraper.get_matches()
        self.assertEquals(len(matches), 126)
        self.assertEquals(mock_get.call_count, 10)

    @mock.patch('scraper.challonge.requests.get')
    def test_get_players(self, mock_get):
        def get_return_values(url):
            if url[-1].isdigit():
                return self.create_mock_response(self.files[int(url[-1]) - 1])
            # if we retrieve /log, return the last page
            else:
                return self.create_mock_response(self.files[-1])

        mock_get.side_effect = get_return_values

        players = self.scraper.get_players()

        self.assertEquals(len(players), 64)
        self.assertTrue('Gar' in players)

    @mock.patch('scraper.challonge.requests.get')
    def test_non_200_response(self, mock_get):
        mock_response = mock.Mock()
        mock_response.status_code = 400
        mock_get.return_value = mock_response

        self.assertRaises(Exception, self.scraper.get_name)
