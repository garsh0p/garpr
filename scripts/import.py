import click
from scraper.tio import TioScraper
from scraper.challonge import ChallongeScraper
from model import Tournament
import dao

@click.command()
@click.option('--type', '-t', help='tio or challonge', type=click.Choice(['challonge', 'tio']), prompt=True)
@click.option('--bracket', '-b', help='Bracket name (for tio)')
@click.argument('path')
def import_tournament(type, path, bracket):
    if type == 'tio':
        scraper = TioScraper(path, bracket)
    elif type =='challonge':
        scraper = ChallongeScraper(path)
    else:
        click.echo("Illegal type")

    tournament = Tournament(type, scraper)

    dao.insert_tournament(tournament.get_json_dict())

if __name__ == '__main__':
    import_tournament()
