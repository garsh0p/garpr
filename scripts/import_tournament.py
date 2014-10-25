import click
from scraper.tio import TioScraper
from scraper.challonge import ChallongeScraper
from model import *
from dao import Dao
import rankings

DEFAULT_RATING = TrueskillRating()

@click.command()
@click.option('--type', '-t', help='tio or challonge', type=click.Choice(['challonge', 'tio']), prompt=True)
@click.option('--bracket', '-b', help='Bracket name (for tio)')
@click.option('--region', '-r', help='Region name', prompt=True)
@click.argument('path')
def import_tournament(type, path, bracket, region):
    if type == 'tio':
        scraper = TioScraper(path, bracket)
    elif type =='challonge':
        scraper = ChallongeScraper(path)
    else:
        click.echo("Illegal type")

    dao = Dao(region)

    import_players(scraper, dao)

    tournament = Tournament.from_scraper(type, scraper, dao)
    dao.insert_tournament(tournament)

    click.echo("Generating new ranking...")
    rankings.generate_ranking(dao)

    click.echo("Done!")

def import_players(scraper, dao):
    for player in scraper.get_players():
        db_player = dao.get_player_by_alias(player)
        if db_player == None:
            click.echo("%s does not exist in the database." % player)

            add_new = click.confirm("Add this player as a new player?", default=True)
            if add_new:
                name = click.prompt("Enter name", default=player)
                alias_set = set()
                alias_set.add(name.lower())
                alias_set.add(player.lower())

                db_player = dao.get_player_by_alias(name)
                if db_player:
                    click.echo("%s already exists, adding %s as an alias." % (name, player))
                    dao.add_alias_to_player(db_player, player)
                    continue

                player_to_add = Player(name, list(alias_set), DEFAULT_RATING, False)
                dao.add_player(player_to_add)
            else:
                player_to_add_alias_to = None
                while not player_to_add_alias_to:
                    alias = click.prompt("Enter a player who is referred to by this alias")
                    player_to_add_alias_to = dao.get_player_by_alias(alias)

                dao.add_alias_to_player(player_to_add_alias_to, player)
        else:
            click.echo("Found player: %s" % db_player)

if __name__ == '__main__':
    import_tournament()
