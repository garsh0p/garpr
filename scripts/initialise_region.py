import click
from model import *
from dao import Dao
from config.config import Config
from pymongo import MongoClient

@click.command()
@click.option('--regionid', '-id', help='a string with which to identify your region', prompt=True)
@click.option('--displayname', '-n', help='The name seen by user', prompt=True)

def initialise_region(regionid, displayname):
    con = Config()
    print(con.get_mongo_url())
    mongo_client = MongoClient(host=con.get_mongo_url())

    region = Region(regionid,displayname)
    Dao.insert_region(region, mongo_client=mongo_client)
    click.echo("Region inserted successfully")

if __name__ == '__main__':
    initialise_region()
