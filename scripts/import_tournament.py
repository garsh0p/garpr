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

@click.command()
@click.option('--type', '-t', help='tio or challonge', type=click.Choice(['challonge', 'tio']), prompt=True)
@click.option('--bracket', '-b', help='Bracket name (for tio)')
@click.option('--region', '-r', help='Region name', prompt=True)
@click.option('--name', '-n', help='Tournament name (override)')
@click.argument('path')
def import_tournament(type, path, bracket, region, name):
    config = parse_config()
    username = config.get('database', 'user')
    host = config.get('database', 'host')
    auth_db = config.get('database', 'auth_db')
    password = getpass.getpass()

    mongo_client = MongoClient(host='mongodb://%s:%s@%s/%s' % (username, password, host, auth_db))

    if type == 'tio':
        scraper = TioScraper(path, bracket)
    elif type =='challonge':
        scraper = ChallongeScraper(path)
    else:
        click.echo("Illegal type")

    dao = Dao(region, mongo_client=mongo_client)

    player_map = get_player_alias_to_id_map(scraper, dao)

    # TODO pass in a map of overrides for specific players
    tournament = Tournament.from_scraper(type, scraper, player_map, region)
    if name:
        tournament.name = name

    dao.insert_tournament(tournament)

    click.echo("Generating new ranking...")
    rankings.generate_ranking(dao)

    click.echo("Done!")

def get_player_alias_to_id_map(scraper, dao):
    player_map = dao.get_player_id_map_from_player_aliases(scraper.get_players())

    for alias, id in player_map.iteritems():
        print ''

        if id is None:
            click.echo("%s does not exist in the current region %s." % (alias, dao.region_id))

            db_player_list = dao.get_players_by_alias_from_all_regions(alias)

            # print out alias matches from other regions as suggestions list
            if db_player_list:
                for db_player in db_player_list:
                    click.echo(str(db_player))

            # prompt to add as new player or add alias to existing player
            add_new = click.confirm("Add this player as a new player?", default=True)
            if add_new:
                name = click.prompt("Enter name", default=alias)
                alias_set = set()
                alias_set.add(name.lower())
                alias_set.add(alias.lower())

                db_player = dao.get_player_by_alias(name)
                if db_player:
                    click.echo("%s already exists, adding %s as an alias." % (name, player))
                    dao.add_alias_to_player(db_player, player)
                    continue

                regions = []
                include_in_region = click.confirm("Associate with current region %s?" % dao.region_id, default=True)
                if include_in_region:
                    regions.append(dao.region_id)

                player_to_add = Player(name, list(alias_set), DEFAULT_RATING, regions)
                click.echo('Inserting player: %s' % player_to_add)
                new_player_id = dao.insert_player(player_to_add)
                player_map[alias] = new_player_id
            else:
                player_id_to_use = click.prompt("Enter this player's ID")

                db_player = dao.get_player_by_id(ObjectId(player_id_to_use))
                if db_player is None:
                    raise Exception('Player with id % not found!' % player_id_to_use)

                if not alias.lower() in db_player.aliases:
                    add_alias = click.confirm("Add %s as a new alias for player %s?" % (alias, db_player.name), default=True)
                    if add_alias:
                        dao.add_alias_to_player(db_player, alias)

                player_map[alias] = db_player.id

    return player_map

if __name__ == '__main__':
    import_tournament()
