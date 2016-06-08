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
        self.players = []

        self.raw_dict = None
        self.get_raw()

    def get_raw(self):
        if self.raw_dict == None:
            self.raw_dict = {}
            
            base_url = TOURNAMENT_URL % self.tournament_id
            url = base_url + DUMP_SETTINGS
            
            self.raw_dict['smashgg'] = self._check_for_200(requests.get(url)).json()
        return self.raw_dict

    def get_matches(self):
        matches = []
        sets = self.get_raw()['smashgg']['entities']['sets']
        for set in sets:
            winner_id = set['winnerId']
            loser_id = set['loserId']
            match = MatchResult(winner_id, loser_id)
            matches.append(match)
        return matches

    def get_player_by_id(self, id):
        if self.players is None or len(self.players) == 0:
            self.get_players()

        for player in self.players:
            if id == int(player.smashgg_id):
                return player

    def get_players(self):
        if self.players is None or len(self.players) == 0:
            self.get_smashgg_players()

        tags = []
        for player in self.players:
            tags.append(str(player.smash_tag).strip())
        return tags


    def get_smashgg_players(self):
        self.players = []
        seeds = self.get_raw()['smashgg']['entities']['seeds']
        for seed in seeds:
            this_player = seed['mutations']['players']
            for player_id in this_player:
                id = player_id

            try:
                tag = this_player[id]['gamerTag'].strip()
                name = this_player[id]['name'].strip()
                region = this_player[id]['region'].strip()
            except:
                print self.log('Data for player ' + id + ' not found')
                continue

            player = SmashGGPlayer(id, name, tag, region)
            self.players.append(player)
        return self.players

    def _check_for_200(self, response):
        response.raise_for_status()
        return response

    def log(self, msg):
        return "    [SmashGG] " + msg

class SmashGGPlayer(object):
    def __init__(self, smashgg_id, name, smash_tag, region):
        self.smashgg_id = smashgg_id
        self.name = name
        self.smash_tag = smash_tag
        self.region = region