import click
from scraper.challonge import ChallongeScraper
from model import *
from dao import Dao
import rankings
from pymongo import MongoClient
import getpass
from ConfigParser import ConfigParser

DEFAULT_RATING = TrueskillRating()

def parse_config():
    config = ConfigParser()
    config.read('config/config.ini')
    return config

@click.command()
@click.option('--region', '-r', help='Region name', prompt=True)
@click.argument('path')
def bulk_import(path, region):
    config = parse_config()
    username = config.get('database', 'user')
    host = config.get('database', 'host')
    auth_db = config.get('database', 'auth_db')
    password = getpass.getpass()

    mongo_client = MongoClient(host='mongodb://%s:%s@%s/%s' % (username, password, host, auth_db))
    dao = Dao(region, mongo_client=mongo_client, new=True)

    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                print line
                scraper = ChallongeScraper(line)
                import_players(scraper, dao)
                import_tournament(scraper, dao)

    rankings.generate_ranking(dao)

def import_players(scraper, dao):
    for player in scraper.get_players():
        db_player = dao.get_player_by_alias(player)
        if db_player == None:
            print " " + player
            player_to_add = Player(player, [player.lower()], DEFAULT_RATING, False)
            dao.add_player(player_to_add)

def import_tournament(scraper, dao):
    tournament = Tournament.from_scraper('challonge', scraper, dao)
    dao.insert_tournament(tournament)

if __name__ == '__main__':
    bulk_import()
