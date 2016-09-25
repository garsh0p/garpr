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
def bulk_player_exclude(path, region):
    config = parse_config()
    username = config.get('database', 'user')
    host = config.get('database', 'host')
    auth_db = config.get('database', 'auth_db')
    password = getpass.getpass()

    mongo_client = MongoClient(host='mongodb://%s:%s@%s/%s' % (username, password, host, auth_db))
    dao = Dao(region, mongo_client=mongo_client)

    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                db_player = dao.get_player_by_alias(line)
                if db_player is None:
                    raise Exception('%s not found' % line)

                print line
                dao.exclude_player(db_player)

if __name__ == '__main__':
    bulk_player_exclude()
