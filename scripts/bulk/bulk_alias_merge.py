import click
import csv
from ConfigParser import ConfigParser
from pymongo import MongoClient
import getpass
from model import *
from dao import Dao

def parse_config():
    config = ConfigParser()
    config.read('config/config.ini')
    return config

@click.command()
@click.option('--region', '-r', help='Region name', prompt=True)
@click.argument('path')
def bulk_alias_merge(path, region):
    config = parse_config()
    username = config.get('database', 'user')
    host = config.get('database', 'host')
    auth_db = config.get('database', 'auth_db')
    password = getpass.getpass()

    mongo_client = MongoClient(host='mongodb://%s:%s@%s/%s' % (username, password, host, auth_db))
    dao = Dao(region, mongo_client=mongo_client)

    with open(path) as f:
        reader = csv.reader(f)
        for row in reader:
            target_alias = row[0]
            db_target = dao.get_player_by_alias(target_alias)
            for source_alias in row[1:]:
                source_alias = source_alias.strip()
                if source_alias:
                    db_source = dao.get_player_by_alias(source_alias)
                    print source_alias, '->', target_alias
                    dao.merge_players(source=db_source, target=db_target)

if __name__ == '__main__':
    bulk_alias_merge()
