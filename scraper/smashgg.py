import requests
import re
import os
import iso8601
from model import MatchResult
from bs4 import BeautifulSoup
from config import config

BASE_SMASHGG_API_URL = "https://api.smash.gg/phase_group/"
TOURNAMENT_URL       = os.path.join(BASE_SMASHGG_API_URL, '%s')
DUMP_SETTINGS        = "?expand[0]=sets&expand[1]=seeds&expand[2]=entrants&expand[3]=matches"

class SmashGGScraper(object):
    def __init__(self, tournament_id):
        self.tournament_id = tournament_id
        self.raw_dict = None
        self.get_raw()
        
    def get_raw(self):
        if self.raw_dict == None:
            self.raw_dict = {}
            
            base_url = TOURNAMENT_URL % self.tournament_id
            url =   os.path.join(base_url, DUMP_SETTINGS)
            
            self.raw_dict['smashgg'] = self.check_for_200(requests.get(url)).json()
        return self.raw_dict    
        
    def _check_for_200(self, response):
        response.raise_for_status()
        return response