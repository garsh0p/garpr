import iso8601
import os
import requests
import parse

from config import config
from model import AliasMatch


BASE_CHALLONGE_API_URL = 'https://api.challonge.com/v1/tournaments'
TOURNAMENT_URL = os.path.join(BASE_CHALLONGE_API_URL, '%s.json')
PARTICIPANTS_URL = os.path.join(
    BASE_CHALLONGE_API_URL, '%s', 'participants.json')
MATCHES_URL = os.path.join(BASE_CHALLONGE_API_URL, '%s', 'matches.json')

# http://api.challonge.com/v1


class ChallongeScraper(object):

    def __init__(self, tournament_id, config_file_path=config.DEFAULT_CONFIG_PATH):
        self.tournament_id = tournament_id
        self.config = config.Config(config_file_path=config_file_path)
        self.api_key = self.config.get_challonge_api_key()
        self.api_key_dict = {'api_key': self.api_key}

        self.raw_dict = None
        self.get_raw()

    def get_raw(self):
        if self.raw_dict is None:
            self.raw_dict = {}

            url = TOURNAMENT_URL % self.tournament_id
            self.raw_dict['tournament'] = self._check_for_200(
                requests.get(url, params=self.api_key_dict)).json()

            url = MATCHES_URL % self.tournament_id
            self.raw_dict['matches'] = self._check_for_200(
                requests.get(url, params=self.api_key_dict)).json()

            url = PARTICIPANTS_URL % self.tournament_id
            self.raw_dict['participants'] = self._check_for_200(
                requests.get(url, params=self.api_key_dict)).json()

        return self.raw_dict

    def get_url(self):
        return self.get_raw()['tournament']['tournament']['full_challonge_url']

    def get_name(self):
        return self.get_raw()['tournament']['tournament']['name'].strip()

    def get_date(self):
        return iso8601.parse_date(self.get_raw()['tournament']['tournament']['created_at'])

    def get_matches(self):
        # sometimes challonge seems to use the "group_player_ids" parameter of "participant" instead
        # of the "id" parameter of "participant" in the "matches" api.
        # not sure exactly when this happens, but the following code checks for both
        player_map = dict()
        for p in self.get_raw()['participants']:
            if p['participant'].get('name'):
                player_name = p['participant']['name'].strip()
            else:
                player_name = p['participant'].get('username', '<unknown>').strip()
            player_map[p['participant'].get('id')] = player_name
            if p['participant'].get('group_player_ids'):
                for gpid in p['participant']['group_player_ids']:
                    player_map[gpid] = player_name

        matches = []
        for m in self.get_raw()['matches']:
            m = m['match']

            set_count = m['scores_csv']
            winner_id = m['winner_id']
            loser_id = m['loser_id']
            if winner_id is not None and loser_id is not None:
                winner = player_map[winner_id]
                loser = player_map[loser_id]
                match_result = AliasMatch(winner=winner, loser=loser)
                matches.append(match_result)
        return matches

    def get_players(self):
        return [p['participant']['name'].strip()
                if p['participant']['name'] else p['participant']['username'].strip()
                for p in self.get_raw()['participants']]

    def _check_for_200(self, response):
        response.raise_for_status()
        return response
