import requests
import re
import os
import iso8601
from model import MatchResult
from model import Player
from bs4 import BeautifulSoup
from config import config

BASE_SMASHGG_API_URL = "https://api.smash.gg/phase_group/"
TOURNAMENT_URL = os.path.join(BASE_SMASHGG_API_URL, '%s')
DUMP_SETTINGS = "?expand[0]=sets&expand[1]=seeds&expand[2]=entrants&expand[3]=matches"

class SmashGGScraper(object):
    def __init__(self, tournament_id):
        self.tournament_id = tournament_id
        self.raw_dict = None
        self.get_raw()

    def get_raw(self):
        if self.raw_dict == None:
            self.raw_dict = {}
            
            base_url = TOURNAMENT_URL % self.tournament_id
            url = base_url + DUMP_SETTINGS
            
            self.raw_dict['smashgg'] = self._check_for_200(requests.get(url)).json()
        return self.raw_dict

    def get_players(self):
        players = []
        seeds = self.get_raw()['smashgg']['entities']['seeds']
        for seed in seeds:
            this_player = seed['mutations']['players']
            for player_id in this_player:
                id = player_id

            try:
                tag = this_player[id]['gamerTag'].strip()
            except:
                print 'No smashtag found for ID: ' + str(id.strip())
                continue

            #COLLECT ADDITIONAL INFORMATION PROVIDED BY API
            #MAYBE USE LATER ON
            #THIS NEEDS BETTER ERR HANDLING / LOGGING
            try:
                name = this_player[id]['name'].strip()
                region = this_player[id]['region'].strip()
            except:
                print 'Data for player ' + id + ' not found'

            #player = Player(tag, [], {}, region, 0)
            players.append(tag)
        return players

    def _check_for_200(self, response):
        response.raise_for_status()
        return response