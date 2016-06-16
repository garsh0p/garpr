from bson.objectid import ObjectId
from datetime import datetime, timedelta
from pymongo import MongoClient, DESCENDING

import base64
import hashlib
import re
import trueskill

from config.config import Config
from model import *

config = Config()

DEFAULT_RATING = TrueskillRating()
DATABASE_NAME = config.get_db_name()
PLAYERS_COLLECTION_NAME = 'players'
TOURNAMENTS_COLLECTION_NAME = 'tournaments'
RANKINGS_COLLECTION_NAME = 'rankings'
REGIONS_COLLECTION_NAME = 'regions'
USERS_COLLECTION_NAME = 'users'
PENDING_TOURNAMENTS_COLLECTION_NAME = 'pending_tournaments'
PENDING_MERGES_COLLECTION_NAME = 'pending_merges'
SESSIONS_COLLECTION_NAME = 'sessions'

special_chars = re.compile("[^\w\s]*")


class RegionNotFoundException(Exception):
    pass

class InvalidRegionsException(Exception):
    pass

class DuplicateAliasException(Exception):
    pass

class DuplicateUsernameException(Exception):
    pass

class InvalidNameException(Exception):
    pass

class UpdateTournamentException(Exception):
    pass

def gen_password(password):
    # more bytes of randomness? i think 16 bytes is sufficient for a salt
    salt = base64.b64encode(os.urandom(16))
    hashed_password = base64.b64encode(hashlib.pbkdf2_hmac('sha256', password, salt, ITERATION_COUNT))

    return salt, hashed_password

def verify_password(password, salt, hashed_password):
    the_hash = base64.b64encode(hashlib.pbkdf2_hmac('sha256', password, salt, ITERATION_COUNT))
    return (the_hash and the_hash==hashed_password)


#TODO create RegionSpecificDao object
# yeah rn we pass in norcal for a buncha things we dont need to
class Dao(object):
    def __init__(self, region_id, mongo_client, database_name=DATABASE_NAME):
        self.mongo_client = mongo_client
        self.region_id = region_id

        if region_id and region_id not in [r.id for r in Dao.get_all_regions(self.mongo_client, database_name=database_name)]:
            raise RegionNotFoundException("%s is not a valid region id!" % region_id)

        self.players_col = mongo_client[database_name][PLAYERS_COLLECTION_NAME]
        self.tournaments_col = mongo_client[database_name][TOURNAMENTS_COLLECTION_NAME]
        self.rankings_col = mongo_client[database_name][RANKINGS_COLLECTION_NAME]
        self.users_col = mongo_client[database_name][USERS_COLLECTION_NAME]
        self.pending_tournaments_col = mongo_client[database_name][PENDING_TOURNAMENTS_COLLECTION_NAME]
        self.pending_merges_col = mongo_client[database_name][PENDING_MERGES_COLLECTION_NAME]
        self.sessions_col = mongo_client[database_name][SESSIONS_COLLECTION_NAME]

    @classmethod
    def insert_region(cls, region, mongo_client, database_name=DATABASE_NAME):
        return mongo_client[database_name][REGIONS_COLLECTION_NAME].insert(region.get_json_dict())

    # sorted by display name
    @classmethod
    def get_all_regions(cls, mongo_client, database_name=DATABASE_NAME):
        regions = [Region.from_json(r) for r in mongo_client[database_name][REGIONS_COLLECTION_NAME].find()]
        return sorted(regions, key=lambda r: r.display_name)

    def get_player_by_id(self, id):
        '''id must be an ObjectId'''
        return Player.from_json(self.players_col.find_one({'_id': id}))

    def get_player_by_alias(self, alias):
        '''Converts alias to lowercase'''
        return Player.from_json(self.players_col.find_one({
            'aliases': {'$in': [alias.lower()]},
            'regions': {'$in': [self.region_id]}
        }))

    def get_players_by_alias_from_all_regions(self, alias):
        '''Converts alias to lowercase'''
        return [Player.from_json(p) for p in self.players_col.find({'aliases': {'$in': [alias.lower()]}})]

    def get_player_id_map_from_player_aliases(self, aliases):
        '''Given a list of player aliases, returns a list of player aliases/id pairs for the current
        region. If no player can be found, the player id field will be set to None.'''
        player_alias_to_player_id_map = []

        for alias in aliases:
            id = None
            player = self.get_player_by_alias(alias)
            if player is not None:
                id = player.id

            player_alias_to_player_id_map.append({
                'player_alias': alias,
                'player_id': id
            })

        return player_alias_to_player_id_map

    def get_all_players(self, all_regions=False):
        '''Sorts by name in lexographical order.'''
        if all_regions:
            return [Player.from_json(p) for p in self.players_col.find().sort([('name', 1)])]
        else:
            return [Player.from_json(p) for p in self.players_col.find({'regions': {'$in': [self.region_id]}}).sort([('name', 1)])]

    def insert_player(self, player):
        return self.players_col.insert(player.get_json_dict())

    def delete_player(self, player):
        return self.players_col.remove({'_id': player.id})

    def update_player(self, player):
        return self.players_col.update({'_id': player.id}, player.get_json_dict())

    # TODO bulk update
    def update_players(self, players):
        pass

    def add_alias_to_player(self, player, alias):
        lowercase_alias = alias.lower()

        if lowercase_alias in player.aliases:
            raise DuplicateAliasException('%s is already an alias for %s!' % (alias, player.name))

        player.aliases.append(lowercase_alias)

        return self.update_player(player)

    def update_player_name(self, player, name):
        # ensure this name is already an alias
        if not name.lower() in player.aliases:
            raise InvalidNameException(
                    'Player %s does not have %s as an alias already, cannot change name.'
                    % (player, name))

        player.name = name
        return self.update_player(player)
#jiang code
    def insert_pending_tournament(self, tournament):
        the_json = tournament.get_json_dict()
        return self.pending_tournaments_col.insert(the_json)

    def update_pending_tournament(self, tournament):
        return self.pending_tournaments_col.update({'_id': tournament.id}, tournament.get_json_dict())

    def get_all_pending_tournament_jsons(self, regions=None):
        query_dict = {'regions': {'$in': regions}} if regions else {}
        return self.pending_tournaments_col.find(query_dict).sort([('date', 1)])

    def insert_pending_tournament(self, pending_tournament):
        return self.pending_tournaments_col.insert(pending_tournament.get_json_dict())

    def update_pending_tournament(self, pending_tournament):
        # if len(pending_tournament.raw) == 0:
        #     raise UpdateTournamentException("Can't update a pending tournament with an empty 'raw' field because it will be overwritten!")
        return self.pending_tournaments_col.update({'_id': pending_tournament.id}, pending_tournament.get_json_dict())

    def delete_pending_tournament(self, pending_tournament):
        return self.pending_tournaments_col.remove({'_id': pending_tournament.id})

    def get_all_pending_tournaments(self, regions=None):
        '''players is a list of Players'''
        query_dict = {}
        query_list = []

        # don't pull the raw field because it takes too much memory
        fields_dict = {
                'raw': 0
        }

        if regions:
            query_list.append({'regions': {'$in': regions}})

        if query_list:
            query_dict['$and'] = query_list

        pending_tournaments = [t for t in self.pending_tournaments_col.find(query_dict, fields_dict).sort([('date', 1)])]

        # manually add an empty raw field
        for pending_tournament in pending_tournaments:
            pending_tournament['raw'] = ''

        return [PendingTournament.from_json(t) for t in pending_tournaments]


    def get_pending_tournament_by_id(self, id):
        '''id must be an ObjectId'''
        return PendingTournament.from_json(self.pending_tournaments_col.find_one({'_id': id}))

    def insert_tournament(self, tournament):
        return self.tournaments_col.insert(tournament.get_json_dict())

    def update_tournament(self, tournament):
        if len(tournament.raw) == 0:
            raise UpdateTournamentException("Can't update a tournament with an empty 'raw' field because it will be overwritten!")

        return self.tournaments_col.update({'_id': tournament.id}, tournament.get_json_dict())

    def delete_tournament(self, tournament):
        return self.tournaments_col.remove({'_id': tournament.id})

    def get_all_tournament_ids(self, players=None, regions=None):
        '''players is a list of Players'''
        query_dict = {}
        query_list = []

        if players:
            for player in players:
                query_list.append({'players': {'$in': [player.id]}})

        if regions:
            query_list.append({'regions': {'$in': regions}})

        if query_list:
            query_dict['$and'] = query_list

        return [t['_id'] for t in self.tournaments_col.find(query_dict, {'_id': 1}).sort([('date', 1)])]

    def get_all_tournaments(self, players=None, regions=None):
        '''players is a list of Players'''
        query_dict = {}
        query_list = []

        # don't pull the raw field because it takes too much memory
        fields_dict = {
                'raw': 0
        }

        if players:
            for player in players:
                query_list.append({'players': {'$in': [player.id]}})

        if regions:
            query_list.append({'regions': {'$in': regions}})

        if query_list:
            query_dict['$and'] = query_list

        tournaments = [t for t in self.tournaments_col.find(query_dict, fields_dict).sort([('date', 1)])]

        # manually add an empty raw field
        for tournament in tournaments:
            tournament['raw'] = ''

        return [Tournament.from_json(t) for t in tournaments]

    def get_tournament_by_id(self, id):
        '''id must be an ObjectId'''
        return Tournament.from_json(self.tournaments_col.find_one({'_id': id}))

    # gets potential merge targets from all regions
    # basically, get players who have an alias similar to the given alias
    def get_players_with_similar_alias(self, alias):
        alias_lower = alias.lower()

        #here be regex dragons
        re_test_1 = '([1-9]+.[1-9]+.)(.+)' # to match '1 1 slox'
        re_test_2 = '(.[1-9]+.[1-9]+.)(.+)' # to match 'p1s1 slox'

        alias_set_1 = re.split(re_test_1, alias_lower)
        alias_set_2 = re.split(re_test_2, alias_lower)

        similar_aliases = set([
            alias_lower,
            alias_lower.replace(" ", ""), # remove spaces
            re.sub(special_chars, '', alias_lower), # remove special characters
            # remove everything before the last special character; hopefully removes crew/sponsor tags
            re.split(special_chars, alias_lower)[-1].strip()
        ])

        # regex nonsense to deal with pool prefixes
        # prevent index OOB errors when dealing with tags that don't split well
        if len(alias_set_1) == 4:
            similar_aliases.update(alias_set_1[2])
            similar_aliases.update(alias_set_1[2].strip())
        if len(alias_set_2) == 4:
            similar_aliases.update(alias_set_2[2])
            similar_aliases.update(alias_set_2[2].strip())


        #add suffixes of the string
        alias_words = alias_lower.split()
        similar_aliases.update([' '.join(alias_words[i:]) for i in xrange(len(alias_words))])

        ret = self.players_col.find({'aliases': {'$in': list(similar_aliases)}})
        return [Player.from_json(p) for p in ret]

    def insert_pending_merge(self, the_merge):
        return self.pending_merges_col.insert(the_merge.get_json_dict())

    def get_pending_merge(self, merge_id):
        info = self.pending_merges_col.find_one({'_id' : merge_id})
        return Merge.from_json(info)

    # TODO reduce db calls for this
    def merge_players(self, source=None, target=None):
        if source is None or target is None:
            raise TypeError("source or target can't be none!");

        if source == target:
            raise ValueError("source and target can't be the same!")

        target.merge_with_player(source)
        self.update_player(target)

        for tournament_id in self.get_all_tournament_ids():
            tournament = self.get_tournament_by_id(tournament_id)
            tournament.replace_player(player_to_remove=source, player_to_add=target)
            self.update_tournament(tournament)

        self.delete_player(source)

    def insert_ranking(self, ranking):
        return self.rankings_col.insert(ranking.get_json_dict())

    def get_latest_ranking(self):
        return Ranking.from_json(self.rankings_col.find({'region': self.region_id}).sort('time', DESCENDING)[0])

    # TODO add more tests
    def is_inactive(self, player, now, day_limit, num_tourneys):

        # TODO: handle special cases somewhere properly
        #       (probably in rankings.generate_ranking)

        # special case for Westchester
        if self.region_id == "westchester":
            day_limit = 1500
            num_tourneys = 1

        # special case for NYC
        if self.region_id == "nyc":
            day_limit = 90
            num_tourneys = 3

        qualifying_tournaments = [x for x in self.get_all_tournaments(players=[player], regions=[self.region_id]) if x.date >= (now - timedelta(days=day_limit))]
        if len(qualifying_tournaments) >= num_tourneys:
            return False
        return True


    # session management


    def insert_user(self, user):
        # validate that no user with same username exists currently
        if self.users_col.find_one({'username': user.username}):
            raise DuplicateUsernameException("already a user with that username in the db, exiting")

        return self.users_col.insert(user.get_json_dict())

    def create_user(self, username, password, regions):
        valid_regions = [region.id for region in Dao.get_all_regions(self.mongo_client)]

        for region in regions:
            if region not in valid_regions:
                print 'Invalid region name:', region

        regions = [region for region in regions if region in valid_regions]
        if len(regions) == 0:
            raise InvalidRegionsException("No valid region for new user")

        salt, hashed_password = gen_password(password)
        the_user = User("userid--" + username,
                        regions,
                        username,
                        salt,
                        hashed_password)

        return self.insert_user(the_user)

    def change_passwd(self, username, password):
        salt, hashed_password = gen_password(password)

        # modifies the users password, or returns None if it couldnt find the user
        return self.users_col.find_and_modify(query={'username': username}, update={"$set": {'hashed_password': hashed_password, 'salt': salt}})

    def get_all_users(self):
        return [User.from_json(u) for u in self.users_col.find()]

    def get_user_by_id_or_none(self, id):
        result = self.users_col.find({"_id": id})
        if result.count() == 0:
            return None
        assert result.count() == 1, "WE HAVE MULTIPLE USERS WITH THE SAME UID"
        return User.from_json(result[0])

    def get_user_by_username_or_none(self, username):
        result = self.users_col.find({"username": username})
        if result.count() == 0:
            return None
        assert result.count() == 1, "WE HAVE MULTIPLE USERS WITH THE SAME USERNAME"
        return User.from_json(result[0])

    def get_user_by_session_id_or_none(self, session_id):
        # mongo magic here, go through and get a user by session_id if they exist, otherwise return none
        result = self.sessions_col.find({"session_id": session_id})
        if result.count() == 0:
            return None
        assert result.count() == 1, "WE HAVE MULTIPLE MAPPINGS FOR THE SAME SESSION_ID"
        user_id = result[0]["user_id"]
        return self.get_user_by_id_or_none(user_id)

    #### FOR INTERNAL USE ONLY ####
    #XXX: this method must NEVER be publicly routeable, or you have session-hijacking
    def get_session_id_by_user_or_none(self, User):
        results = self.sessions_col.find()
        for session_mapping in results:
            if session_mapping.user_id == User.user_id:
                return session_mapping.session_id
        return None
    #### END OF YELLING #####


    def check_creds_and_get_session_id_or_none(self, username, password):
        result = self.users_col.find({"username": username})
        if result.count() == 0:
            return None
        assert result.count() == 1, "WE HAVE DUPLICATE USERNAMES IN THE DB"
        user = User.from_json(result[0])
        assert user, "mongo has stopped being consistent, abort ship"

         # timing oracle on this... good luck
        if verify_password(password, user.salt, user.hashed_password):
            session_id = base64.b64encode(os.urandom(128))
            self.update_session_id_for_user(user.id, session_id)
            return session_id
        else:
            return None

    def update_session_id_for_user(self, user_id, session_id):
        #lets force people to have only one session at a time
        result = self.sessions_col.remove({"user_id": user_id})
        session_mapping = SessionMapping(session_id, user_id)
        self.sessions_col.insert(session_mapping.get_json_dict())

    def logout_user_or_none(self, session_id):
        user = self.get_user_by_session_id_or_none(session_id)
        if user:
            self.sessions_col.remove({"user_id": user.id})
            return True
        return None
