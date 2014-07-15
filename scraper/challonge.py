import requests
import re
import os
import iso8601
from model import MatchResult
from bs4 import BeautifulSoup

CHALLONGE_API_KEY_PATH = 'challonge_api_key.txt'
BASE_CHALLONGE_API_URL = 'https://api.challonge.com/v1/tournaments'
TOURNAMENT_URL = os.path.join(BASE_CHALLONGE_API_URL, '%s.json')
PARTICIPANTS_URL = os.path.join(BASE_CHALLONGE_API_URL, '%s', 'participants.json')
MATCHES_URL = os.path.join(BASE_CHALLONGE_API_URL, '%s', 'matches.json')

# http://api.challonge.com/v1
class ChallongeScraper(object):
    def __init__(self, tournament_id):
        self.tournament_id = tournament_id

        with open(CHALLONGE_API_KEY_PATH) as f:
            for line in f:
                self.api_key = line.strip()

        self.api_key_dict = {'api_key': self.api_key}

    def get_raw(self):
        raw_dict = {}

        url = TOURNAMENT_URL % self.tournament_id
        raw_dict['tournament'] = self._check_for_200(requests.get(url, params=self.api_key_dict)).json()

        url = MATCHES_URL % self.tournament_id
        raw_dict['matches'] = self._check_for_200(requests.get(url, params=self.api_key_dict)).json()

        url = PARTICIPANTS_URL % self.tournament_id
        raw_dict['participants'] = self._check_for_200(requests.get(url, params=self.api_key_dict)).json()

        return raw_dict

    def get_name(self):
        url = TOURNAMENT_URL % self.tournament_id
        json_response = requests.get(url, params=self.api_key_dict).json()
        return json_response['tournament']['name'].strip()

    def get_date(self):
        url = TOURNAMENT_URL % self.tournament_id
        json_response = requests.get(url, params=self.api_key_dict).json()
        return iso8601.parse_date(json_response['tournament']['created_at'])

    def get_matches(self):
        matches_url = MATCHES_URL % self.tournament_id
        matches_json_response = requests.get(matches_url, params=self.api_key_dict).json()

        participants_url = PARTICIPANTS_URL % self.tournament_id
        participants_json_response = requests.get(participants_url, params=self.api_key_dict).json()

        player_map = dict((p['participant']['id'], p['participant']['name']) 
                          for p in participants_json_response)

        matches = []
        for m in matches_json_response:
            m = m['match']
            winner_id = m['winner_id']
            loser_id = m['loser_id']
            winner = player_map[winner_id]
            loser = player_map[loser_id]
            match_result = MatchResult(winner=winner, loser=loser)
            matches.append(match_result)

        return matches

    def get_players(self):
        # participant
        url = PARTICIPANTS_URL % self.tournament_id
        json_response = requests.get(url, params=self.api_key_dict).json()

        return [p['participant']['name'] for p in json_response]

    def _check_for_200(self, response):
        if response.status_code != 200:
            raise Exception('Received status code of %d' % response.status_code)

        return response

