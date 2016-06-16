from ConfigParser import ConfigParser

DEFAULT_CONFIG_PATH = './config/config.ini'

class Config(object):
    def __init__(self, config_file_path=DEFAULT_CONFIG_PATH):
        self.config = ConfigParser()
        self.config.read(config_file_path)

    def get_mongo_url(self):
        return 'mongodb://%s:%s@%s/%s' % (
                self.get_db_user(),
                self.get_db_password(),
                self.get_db_host(),
                self.get_auth_db_name())

    def get_environment_name(self):
        return self.config.get('environment', 'name')

    def get_environment_web_port(self):
        return self.config.get('environment', 'web_port')

    def get_environment_api_port(self):
        return self.config.get('environment', 'api_port')

    def get_db_host(self):
        return self.config.get('database', 'host')

    def get_auth_db_name(self):
        return self.config.get('database', 'auth_db')

    def get_db_name(self):
        return self.config.get('database', 'db')

    def get_db_user(self):
        return self.config.get('database', 'user')

    def get_db_password(self):
        return self.config.get('database', 'password')

    def get_challonge_api_key(self):
        return self.config.get('challonge', 'api_key')

    def get_fb_app_id(self):
        return self.config.get('facebook', 'app_id')

    def get_fb_app_token(self):
        return self.config.get('facebook', 'app_token')
