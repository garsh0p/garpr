import click
from scraper.tio import TioScraper
from scraper.challonge import ChallongeScraper
from model import *
from dao import Dao
import rankings
from ConfigParser import ConfigParser
from pymongo import MongoClient
import getpass
from bson.objectid import ObjectId

DEFAULT_RATING = {}

def parse_config():
    config = ConfigParser()
    config.read('config/config.ini')
    return config

def get_dao(region):
    config = parse_config()
    username = config.get('database', 'user')
    host = config.get('database', 'host')
    auth_db = config.get('database', 'auth_db')
    password = getpass.getpass()

    mongo_client = MongoClient(host='mongodb://%s:%s@%s/%s' % (username, password, host, auth_db))
    return Dao(region, mongo_client=mongo_client)

# import pending tournaments
def import_tournament_from_tio_filestream(region, stream, bracket, name):
    dao = get_dao(region)
    scraper = TioScraper(stream.read(), bracket)
    pending = PendingTournament.from_scraper(type, scraper, region)
    if name:
        pending.name = name

    return dao.insert_pending_tournament(pending)

def import_tournament_from_challonge(region, path, name):
    dao = get_dao(region)
    scraper = ChallongeScraper(path)
    pending = PendingTournament.from_scraper(type, scraper, region)
    if name:
        pending.name = name

    return dao.insert_pending_tournament(pending)

def get_pending_tournaments(region):
    dao = get_dao(region)
    return dao.get_all_pending_tournament_jsons([region])

def finalize_tournament(region, pending_tournament):
    dao = get_dao(region)
    if not pending_tournament.are_all_aliases_mapped():
        raise Exception("Not all aliases for the pending tournament have been mapped to an id.")
    tournament = Tournament.from_pending_tournament(pending_tournament)
    dao.insert_tournament(tournament)
    rankings.generate_ranking(dao)

