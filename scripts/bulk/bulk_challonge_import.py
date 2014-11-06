import click
from scraper.challonge import ChallongeScraper
from model import *
from dao import Dao
import rankings
from pymongo import MongoClient

DEFAULT_RATING = TrueskillRating()

# TODO define mongo_client
@click.command()
@click.option('--region', '-r', help='Region name', prompt=True)
@click.argument('path')
def bulk_import(path, region):
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                print line
                scraper = ChallongeScraper(line)
                dao = Dao(region, mongo_client=mongo_client, new=True)
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
