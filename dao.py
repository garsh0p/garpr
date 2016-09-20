from datetime import timedelta

import base64
import hashlib
import os
import pymongo
import re

from config.config import Config

import model as M

config = Config()

ITERATION_COUNT = 100000

DATABASE_NAME = config.get_db_name()
PLAYERS_COLLECTION_NAME = 'players'
TOURNAMENTS_COLLECTION_NAME = 'tournaments'
RANKINGS_COLLECTION_NAME = 'rankings'
REGIONS_COLLECTION_NAME = 'regions'
USERS_COLLECTION_NAME = 'users'
PENDING_TOURNAMENTS_COLLECTION_NAME = 'pending_tournaments'
MERGES_COLLECTION_NAME = 'merges'
SESSIONS_COLLECTION_NAME = 'sessions'

special_chars = re.compile("[^\w\s]*")


# make sure all the exceptions here are properly caught, or the server code
# knows about them.


class InvalidRegionsException(Exception):
    # safe, only used from script
    pass


class DuplicateAliasException(Exception):
    # safe, only used in dead code
    pass


class DuplicateUsernameException(Exception):
    # safe, only used from script
    pass


class InvalidNameException(Exception):
    # safe only used in dead code
    pass


def gen_password(password):
    # more bytes of randomness? i think 16 bytes is sufficient for a salt
    salt = base64.b64encode(os.urandom(16))
    hashed_password = base64.b64encode(hashlib.pbkdf2_hmac(
        'sha256', password, salt, ITERATION_COUNT))

    return salt, hashed_password


def verify_password(password, salt, hashed_password):
    the_hash = base64.b64encode(hashlib.pbkdf2_hmac(
        'sha256', password, salt, ITERATION_COUNT))
    return (the_hash and the_hash == hashed_password)


# TODO create RegionSpecificDao object rn we pass in norcal for a buncha
# things we dont need to
class Dao(object):

    # here lies some serious abuse of magic methods, here be dragons
    # use __new__ so that we can return None
    def __new__(cls, region_id, mongo_client, database_name=DATABASE_NAME):
        all_region_ids = [r.id for r in Dao.get_all_regions(
            mongo_client, database_name=database_name)]
        if region_id and region_id not in all_region_ids:
            return None
        # this is how we call __init__
        return super(Dao, cls).__new__(cls, region_id, mongo_client, database_name)

    def __init__(self, region_id, mongo_client, database_name=DATABASE_NAME):
        self.players_col = mongo_client[database_name][PLAYERS_COLLECTION_NAME]
        self.tournaments_col = mongo_client[
            database_name][TOURNAMENTS_COLLECTION_NAME]
        self.rankings_col = mongo_client[
            database_name][RANKINGS_COLLECTION_NAME]
        self.users_col = mongo_client[database_name][USERS_COLLECTION_NAME]
        self.pending_tournaments_col = mongo_client[
            database_name][PENDING_TOURNAMENTS_COLLECTION_NAME]
        self.merges_col = mongo_client[database_name][MERGES_COLLECTION_NAME]
        self.sessions_col = mongo_client[
            database_name][SESSIONS_COLLECTION_NAME]
        self.mongo_client = mongo_client
        self.region_id = region_id

    @classmethod
    def insert_region(cls, region, mongo_client, database_name=DATABASE_NAME):
        return mongo_client[database_name][REGIONS_COLLECTION_NAME].insert(region.dump(context='db'))

    # sorted by display name
    @classmethod
    def get_all_regions(cls, mongo_client, database_name=DATABASE_NAME):
        regions = [M.Region.load(r, context='db') for r in mongo_client[
            database_name][REGIONS_COLLECTION_NAME].find()]
        return sorted(regions, key=lambda r: r.display_name)

    def get_player_by_id(self, id):
        '''id must be an ObjectId'''
        return M.Player.load(self.players_col.find_one({'_id': id}), context='db')

    def get_player_by_alias(self, alias):
        '''Converts alias to lowercase'''
        return M.Player.load(self.players_col.find_one({
            'aliases': {'$in': [alias.lower()]},
            'regions': {'$in': [self.region_id]},
            'merged': False
        }), context='db')

    def get_players_by_alias_from_all_regions(self, alias):
        '''Converts alias to lowercase'''
        return [M.Player.load(p, context='db') for p in self.players_col.find({
            'aliases': {'$in': [alias.lower()]},
            'merged': False
        })]

    def get_player_id_map_from_player_aliases(self, aliases):
        '''Given a list of player aliases, returns a list of player aliases/id pairs for the current
        region. If no player can be found, the player id field will be set to None.'''
        player_alias_to_player_id_map = []

        for alias in aliases:
            id = None
            player = self.get_player_by_alias(alias)
            if player is not None:
                id = player.id

            player_alias_to_player_id_map.append(M.AliasMapping(
                player_alias=alias,
                player_id=id
            ))

        return player_alias_to_player_id_map

    def get_all_players(self, all_regions=False, include_merged=False):
        '''Sorts by name in lexographical order.'''
        mongo_request = {}
        if not all_regions:
            mongo_request['regions'] = {'$in': [self.region_id]}
        if not include_merged:
            mongo_request['merged'] = False
        return [M.Player.load(p, context='db')
                for p in self.players_col.find(mongo_request).sort([('name', 1)])]

    def insert_player(self, player):
        return self.players_col.insert(player.dump(context='db'))

    def delete_player(self, player):
        return self.players_col.remove({'_id': player.id})

    def update_player(self, player):
        return self.players_col.update({'_id': player.id}, player.dump(context='db'))

    # TODO bulk update
    def update_players(self, players):
        pass

    # unused, if you use this, make sure to surround it in a try block!
    def add_alias_to_player(self, player, alias):
        lowercase_alias = alias.lower()

        if lowercase_alias in player.aliases:
            raise DuplicateAliasException(
                '%s is already an alias for %s!' % (alias, player.name))

        player.aliases.append(lowercase_alias)

        return self.update_player(player)

    # unused, if you use this, make sure to surround it in a try block!
    def update_player_name(self, player, name):
        # ensure this name is already an alias
        if not name.lower() in player.aliases:
            raise InvalidNameException(
                'Player %s does not have %s as an alias already, cannot change name.'
                % (player, name))

        player.name = name
        return self.update_player(player)

    def insert_pending_tournament(self, pending_tournament):
        return self.pending_tournaments_col.insert(pending_tournament.dump(context='db'))

    def update_pending_tournament(self, tournament):
        return self.pending_tournaments_col.update({'_id': tournament.id}, tournament.dump(context='db'))

    def delete_pending_tournament(self, pending_tournament):
        return self.pending_tournaments_col.remove({'_id': pending_tournament.id})

    def get_all_pending_tournament_jsons(self, regions=None):
        query_dict = {'regions': {'$in': regions}} if regions else {}
        return self.pending_tournaments_col.find(query_dict).sort([('date', 1)])

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

        pending_tournaments = [t for t in self.pending_tournaments_col.find(
            query_dict, fields_dict).sort([('date', 1)])]

        # manually add an empty raw field
        for pending_tournament in pending_tournaments:
            pending_tournament['raw'] = ''

        return [M.PendingTournament.load(t, context='db') for t in pending_tournaments]

    def get_pending_tournament_by_id(self, id):
        '''id must be an ObjectId'''
        return M.PendingTournament.load(self.pending_tournaments_col.find_one({'_id': id}),
                                        context='db')

    def insert_tournament(self, tournament):
        return self.tournaments_col.insert(tournament.dump(context='db'))

    # all uses of this MUST use a try/except block!
    def update_tournament(self, tournament):
        return self.tournaments_col.update({'_id': tournament.id}, tournament.dump(context='db'))

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

        tournaments = [t for t in self.tournaments_col.find(
            query_dict, fields_dict).sort([('date', 1)])]

        # manually add an empty raw field
        for tournament in tournaments:
            tournament['raw'] = ''

        return [M.Tournament.load(t, context='db') for t in tournaments]

    def get_tournament_by_id(self, id):
        '''id must be an ObjectId'''
        return M.Tournament.load(self.tournaments_col.find_one({'_id': id}), context='db')

    # gets potential merge targets from all regions
    # basically, get players who have an alias similar to the given alias
    def get_players_with_similar_alias(self, alias):
        alias_lower = alias.lower()

        # here be regex dragons
        re_test_1 = '([1-9]+\s+[1-9]+\s+)(.+)'  # to match '1 1 slox'
        re_test_2 = '(.[1-9]+.[1-9]+\s+)(.+)'  # to match 'p1s1 slox'

        alias_set_1 = re.split(re_test_1, alias_lower)
        alias_set_2 = re.split(re_test_2, alias_lower)

        similar_aliases = [
            alias_lower,
            alias_lower.replace(" ", ""),  # remove spaces
            # remove special characters
            re.sub(special_chars, '', alias_lower),
            # remove everything before the last special character; hopefully
            # removes crew/sponsor tags
            re.split(special_chars, alias_lower)[-1].strip()
        ]

        # regex nonsense to deal with pool prefixes
        # prevent index OOB errors when dealing with tags that don't split well
        if len(alias_set_1) == 4:
            similar_aliases.append(alias_set_1[2].strip())
        if len(alias_set_2) == 4:
            similar_aliases.append(alias_set_2[2].strip())

        # add suffixes of the string
        alias_words = alias_lower.split()
        similar_aliases.extend([' '.join(alias_words[i:])
                                for i in xrange(len(alias_words))])

        # uniqify
        similar_aliases = list(set(similar_aliases))

        ret = self.players_col.find({'aliases': {'$in': similar_aliases},
                                     'merged': False})
        return [M.Player.load(p, context='db') for p in ret]

    # inserts and merges players!
    # TODO: add support for pending merges
    def insert_merge(self, the_merge):
        self.merge_players(the_merge)
        return self.merges_col.insert(the_merge.dump(context='db'))

    def get_merge(self, merge_id):
        info = self.merges_col.find_one({'_id': merge_id})
        return M.Merge.load(info, context='db')

    def get_all_merges(self):
        return [M.Merge.load(m, context='db') for m in self.merges_col.find().sort([('time', 1)])]

    def undo_merge(self, the_merge):
        self.unmerge_players(the_merge)
        self.merges_col.remove({'_id': the_merge.id})

    def merge_players(self, merge):
        if merge is None:
            raise TypeError("merge cannot be none")

        source = self.get_player_by_id(merge.source_player_obj_id)
        target = self.get_player_by_id(merge.target_player_obj_id)

        if source is None or target is None:
            raise TypeError("source or target can't be none!")

        # check if already merged
        if source.merged:
            raise ValueError("source is already merged")

        if target.merged:
            raise ValueError("target is already merged")

        print 'source:', source
        print 'target:', target
        if (source.id in target.merge_children) or (target.id in source.merge_children):
            raise ValueError("source and target already merged")

        # check if these two players have ever played each other
        # (can't merge players who've played each other)
        # TODO: reduce db calls for this
        for tournament_id in self.get_all_tournament_ids():
            tournament = self.get_tournament_by_id(tournament_id)
            if source.id in tournament.players and target.id in tournament.players:
                raise ValueError("source and target have played each other")

        # update target and source players
        target.aliases = list(set(source.aliases + target.aliases))
        target.regions = list(set(source.regions + target.regions))

        target.merge_children = target.merge_children + source.merge_children
        source.merge_parent = target.id
        source.merged = True

        self.update_player(source)
        self.update_player(target)

        # replace source with target in all tournaments that contain source
        # TODO: reduce db calls for this (index tournaments by players)
        for tournament_id in self.get_all_tournament_ids():
            tournament = self.get_tournament_by_id(tournament_id)
            tournament.replace_player(
                player_to_remove=source, player_to_add=target)
            self.update_tournament(tournament)

    def unmerge_players(self, merge):
        source = self.get_player_by_id(merge.source_player_obj_id)
        target = self.get_player_by_id(merge.target_player_obj_id)

        if source is None or target is None:
            raise TypeError("source or target can't be none!")

        if source.merge_parent != target.id:
            raise ValueError("source not merged into target")

        if target.merged:
            raise ValueError("target has been merged; undo that merge first")

        # TODO: unmerge aliases and regions
        # (probably best way to do this is to store which aliases and regions were merged in the merge Object)
        source.merge_parent = None
        source.merged = False
        target.merge_children = [
            child for child in target.merge_children if child not in source.merge_children]

        self.update_player(source)
        self.update_player(target)

        # unmerge source from target
        # TODO: reduce db calls for this (index tournaments by players)
        for tournament_id in self.get_all_tournament_ids():
            tournament = self.get_tournament_by_id(tournament_id)

            if target.id in tournament.players:
                print "unmerging tournament", tournament
                # check if original id now belongs to source
                if any([child in tournament.orig_ids for child in source.merge_children]):
                    # replace target with source in tournament
                    tournament.replace_player(
                        player_to_remove=target, player_to_add=source)
                    self.update_tournament(tournament)

    def insert_ranking(self, ranking):
        return self.rankings_col.insert(ranking.dump(context='db'))

    def get_latest_ranking(self):
        return M.Ranking.load(
            self.rankings_col.find({'region': self.region_id}).sort(
                'time', pymongo.DESCENDING)[0],
            context='db')

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
            num_tourneys = 6

        # special case for LI
        if self.region_id == "li":
            day_limit = 90
            num_tourneys = 4

        qualifying_tournaments = [x for x in self.get_all_tournaments(
            players=[player], regions=[self.region_id]) if x.date >= (now - timedelta(days=day_limit))]
        if len(qualifying_tournaments) >= num_tourneys:
            return False
        return True

    # session management

    # throws an exception, which is okay because this is called from just
    # create_user
    def insert_user(self, user):
        # validate that no user with same username exists currently
        if self.users_col.find_one({'username': user.username}):
            raise DuplicateUsernameException(
                "already a user with that username in the db, exiting")

        return self.users_col.insert(user.dump(context='db'))

    # throws invalidRegionsException, which is okay, as this is only used by a
    # script
    def create_user(self, username, password, regions):
        valid_regions = [
            region.id for region in Dao.get_all_regions(self.mongo_client)]

        for region in regions:
            if region not in valid_regions:
                print 'Invalid region name:', region

        regions = [region for region in regions if region in valid_regions]
        if len(regions) == 0:
            raise InvalidRegionsException("No valid region for new user")

        salt, hashed_password = gen_password(password)
        the_user = M.User(id="userid--" + username,
                          admin_regions=regions,
                          username=username,
                          salt=salt,
                          hashed_password=hashed_password)

        return self.insert_user(the_user)

    def change_passwd(self, username, password):
        salt, hashed_password = gen_password(password)

        # modifies the users password, or returns None if it couldnt find the
        # user
        return self.users_col.find_and_modify(
            query={'username': username},
            update={"$set": {'hashed_password': hashed_password, 'salt': salt}})

    def get_all_users(self):
        return [M.User.load(u, context='db') for u in self.users_col.find()]

    def get_user_by_id_or_none(self, id):
        result = self.users_col.find({"_id": id})
        if result.count() == 0:
            return None
        assert result.count() == 1, "WE HAVE MULTIPLE USERS WITH THE SAME UID"
        return M.User.load(result[0], context='db')

    def get_user_by_username_or_none(self, username):
        result = self.users_col.find({"username": username})
        if result.count() == 0:
            return None
        assert result.count() == 1, "WE HAVE MULTIPLE USERS WITH THE SAME USERNAME"
        return M.User.load(result[0], context='db')

    def get_user_by_session_id_or_none(self, session_id):
        # mongo magic here, go through and get a user by session_id if they
        # exist, otherwise return none
        result = self.sessions_col.find({"session_id": session_id})
        if result.count() == 0:
            return None
        assert result.count() == 1, "WE HAVE MULTIPLE MAPPINGS FOR THE SAME SESSION_ID"
        user_id = result[0]["user_id"]
        return self.get_user_by_id_or_none(user_id)

    # FOR INTERNAL USE ONLY #
    # XXX: this method must NEVER be publicly routeable, or you have
    # session-hijacking
    def get_session_id_by_user_or_none(self, User):
        results = self.sessions_col.find()
        for session_mapping in results:
            if session_mapping.user_id == User.user_id:
                return session_mapping.session_id
        return None
    # END OF YELLING #

    def check_creds_and_get_session_id_or_none(self, username, password):
        result = self.users_col.find({"username": username})
        if result.count() == 0:
            return None
        assert result.count() == 1, "WE HAVE DUPLICATE USERNAMES IN THE DB"
        user = M.User.load(result[0], context='db')
        assert user, "mongo has stopped being consistent, abort ship"

        # timing oracle on this... good luck
        if verify_password(password, user.salt, user.hashed_password):
            session_id = base64.b64encode(os.urandom(128))
            self.update_session_id_for_user(user.id, session_id)
            return session_id
        else:
            return None

    def update_session_id_for_user(self, user_id, session_id):
        # lets force people to have only one session at a time
        self.sessions_col.remove({"user_id": user_id})
        session_mapping = M.Session(session_id=session_id,
                                    user_id=user_id)
        self.sessions_col.insert(session_mapping.dump(context='db'))

    def logout_user_or_none(self, session_id):
        user = self.get_user_by_session_id_or_none(session_id)
        if user:
            self.sessions_col.remove({"user_id": user.id})
            return True
        return None
