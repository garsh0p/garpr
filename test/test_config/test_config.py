import unittest
from config.config import Config

TEMPLATE_CONFIG_FILE = 'config/config.ini.template'

class TestConfig(unittest.TestCase):
    def setUp(self):
        self.config = Config(TEMPLATE_CONFIG_FILE)

    def test_get_mongo_url(self):
        self.assertEquals(self.config.get_mongo_url(), 'mongodb://USER:PASSWORD@HOSTNAME/AUTH_DB')

    def test_get_db_host(self):
        self.assertEquals(self.config.get_db_host(), 'HOSTNAME')

    def test_get_auth_db_name(self):
        self.assertEquals(self.config.get_auth_db_name(), 'AUTH_DB')

    def test_get_db_user(self):
        self.assertEquals(self.config.get_db_user(), 'USER')

    def test_get_db_password(self):
        self.assertEquals(self.config.get_db_password(), 'PASSWORD')

    def test_challonge_api_key(self):
        self.assertEquals(self.config.get_challonge_api_key(), 'API_KEY')

    def test_get_fb_app_id(self):
        self.assertEquals(self.config.get_fb_app_id(), 'FB_APP_ID')

    def test_get_fb_app_token(self):
        self.assertEquals(self.config.get_fb_app_token(), 'FB_APP_TOKEN')
