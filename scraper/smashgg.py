import datetime
import requests
import os
from model import MatchResult
from garprLogging.log import Log

### SMASHGG URLS: https://smash.gg/tournament/<tournament-name>/brackets/<event-id>/<phase-id>/<phase-group-id>/
EVENT_URL = "https://api.smash.gg/event/%s?expand[0]=groups&expand[1]=entrants"
GROUP_URL = "https://api.smash.gg/phase_group/%s?expand[0]=sets&expand[1]=entrants&expand[2]=matches&expand[3]=seeds"

SET_TIME_PROPERTIES = ['startedAt', 'completedAt']

def check_for_200(response):
    """
    :param response: http response to check for correct http code
    :return: the body response from a successful http call
    """
    response.raise_for_status()
    return response

class SmashGGScraper(object):
    def __init__(self, path):
        """
        :param path: url to go to the bracket
        """
        self.path = path

        #GET IMPORTANT DATA FROM THE URL
        self.event_id = SmashGGScraper.get_tournament_event_id_from_url(self.path)
        self.name = SmashGGScraper.get_tournament_name_from_url(self.path)

        #DEFINE OUR TARGET URL ENDPOINT FOR THE SMASHGG API
        #AND INSTANTIATE THE DICTIONARY THAT HOLDS THE RAW
        # JSON DUMPED FROM THE API

        self.event_dict = SmashGGScraper.get_event_dict(self.event_id)
        self.group_ids = self.get_group_ids()
        self.group_dicts = [SmashGGScraper.get_group_dict(group_id) for group_id in self.group_ids]

        #DATA STRUCTURES THAT HOLD IMPORTANT THINGS
        self.get_smashgg_players()
        self.player_lookup = {player.entrant_id: player for player in self.players}

        self.date = datetime.datetime.now()
        self.get_smashgg_matches()


######### START OF SCRAPER API

    def get_raw(self):
        """
        :return: the JSON dump that the api call returns
        """
        return {'event': self.event_dict,
                'groups': self.group_dicts}

    def get_name(self):
        return self.name

    # The JSON scrape doesn't give us the Date of the tournament currently
    # Get date from earliest start time of a set
    def get_date(self):
        return self.date

    def get_players(self):
        """
        :return: the smash tags of every player who is in the given bracket
        """
        return sorted(list(set([player.smash_tag for player in self.players])))

    def get_matches(self):
        """
        :return: the list of MatchResult objects that represents every match
        played in the given bracket, including who won and who lost
        """

        return_matches = []
        for match in self.matches:
            winner = self.player_lookup.get(match.winner_id)
            loser = self.player_lookup.get(match.loser_id)

            if winner is None:
                print 'Error: id {} not found in player list'.format(match.winner_id)
                continue

            if loser is None:
                print 'Error: id {} not found in player list'.format(match.loser_id)
                continue

            return_match = MatchResult(winner.smash_tag, loser.smash_tag)
            return_matches.append(return_match)

        return return_matches

####### END OF SCRAPER API

    def get_smashgg_players(self):
        """
        :return: and edit the local list of SmashGGPlayer objects that encapsulate important information about
        the participants of the tournament, including their name, region, smashtag,
        tournament entrant id, and overall smashgg id
        """
        self.players = []
        entrants = self.event_dict['entities']['entrants']
        for player in entrants:
            tag             = player.get("name", None)
            name            = None  # these fields not contained in entrants
            state           = None  # these fields not contained in entrants
            country         = None  # these fields not contained in entrants
            region          = None  # these fields not contained in entrants
            entrant_id      = player.get("id", None)
            final_placement = player.get("final_placement", None)
            smashgg_id      = None

            for sid in player.get("participantIds", []):
                smashgg_id = sid

            player = SmashGGPlayer(smashgg_id=smashgg_id, entrant_id=entrant_id, name=name, smash_tag=tag, region=region,
                                   state=state, country=country, final_placement=final_placement)
            self.players.append(player)

    def get_smashgg_matches(self):
        """
        :return: a list of SmashGGMatch objects that encapsulate more data about the match
        than just the winner and loser. Could be useful for additional ranking metrics
        like how far into the tournament or how many matches were played.
        """
        self.matches = []
        for group_dict in self.group_dicts:
            for match in group_dict['entities']['sets']:
                winner_id = match['winnerId']
                loser_id = match['loserId']
                # CHECK FOR A BYE
                if loser_id is None:
                    continue

                round_name = match.get("fullRoundText", None)
                round_num = match.get("round", None)
                best_of = match.get("bestOf", None)

                for prop in SET_TIME_PROPERTIES:
                    cur_time = match.get(prop, None)
                    if cur_time:
                        self.date = min(self.date, datetime.datetime.fromtimestamp(cur_time))

                smashgg_match = SmashGGMatch(round_name, winner_id, loser_id, round_num, best_of)
                self.matches.append(smashgg_match)

    def get_group_ids(self):
        group_ids = [str(group['id']).strip() for group in self.event_dict['entities']['groups']]
        return list(set(group_ids))

    @staticmethod
    def get_tournament_event_id_from_url(url):
        splits = url.split('/')

        flag = False
        for split in splits:
            #IF THIS IS TRUE WE HAVE REACHED THE EVENT ID
            if flag is True:
                return int(split)

            #SET FLAG TRUE IF CURRENT WORD IS 'BRACKETS'
            #THE NEXT ELEMENT WILL BE OUR EVENT ID
            if 'brackets' in split:
                flag = True

    # Deprecated: now should get all phases from event
    @staticmethod
    def get_tournament_phase_id_from_url(url):
        """
        Parses a url and retrieves the unique id of the bracket in question
        :param url: url to parse the tournament id from
        :return: the unique id of the bracket in question
        """
        id = url[url.rfind('/') + 1:]
        return int(id)

    @staticmethod
    def get_tournament_name_from_url(url):
        """
        Parses a url and retrieves the name of the tournament in question
        :param url: url to parse the tournament name from
        :return: the name of the tournament in question
        """
        tStr = 'tournament/'
        startIndex = url.rfind(tStr) + len(tStr)
        name = url[startIndex: url.index('/', startIndex)]
        return name.replace('-', ' ')

    @staticmethod
    def get_event_dict(event_id):
        return check_for_200(requests.get(EVENT_URL % event_id)).json()

    @staticmethod
    def get_group_dict(group_id):
        return check_for_200(requests.get(GROUP_URL % group_id)).json()

class SmashGGPlayer(object):
    def __init__(self, smashgg_id, entrant_id, name, smash_tag, region, country, state, final_placement):
        """
        :param smashgg_id:      The Global id that a player is mapped to on the website
        :param entrant_id:      The id assigned to an entrant for the given tournament
        :param name:            The real name of the player
        :param smash_tag:       The Smash Tag of the player
        :param region:          The region the player belongs to
        :param country:
        :param state:
        :param final_placement:
        """
        self.smashgg_id = smashgg_id
        self.entrant_id = entrant_id
        self.name = name
        self.smash_tag = smash_tag
        self.region = region
        self.country = country
        self.state = state

        if self.name:
            self.name = self.name.encode('ascii', 'ignore').strip()
        if self.smash_tag:
            self.smash_tag = self.smash_tag.encode('ascii', 'ignore').strip()
        if self.region:
            self.region = self.region.encode('ascii', 'ignore').strip()
        if self.country:
            self.country = self.country.encode('ascii', 'ignore').strip()
        if self.state:
            self.state = self.state.encode('ascii', 'ignore').strip()

class SmashGGMatch(object):
    def __init__(self, roundName, winner_id, loser_id, roundNumber, bestOf):
        """
        :param winner_id: Entrant id of the winner of the match
        :param loser_id:  Entrant id of the loser of the match
        :param round:     Round of the bracket this match took place
        :param bestOf:    Best of this many matches
        """
        self.roundName = roundName
        self.winner_id = winner_id
        self.loser_id = loser_id
        self.roundNumber = roundNumber
        self.bestOf = bestOf

class SmashGGException(Exception):
    def __init__(self, message):
        self.message = message
