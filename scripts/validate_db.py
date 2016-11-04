# script for db-wide data validation (for data validation checks that cannot
#   be handled by document-wide validation)
# this script is resource-intensive: should only be run once per day/week or
#   when significant modifications are made to model.py

import argparse
import os
import sys

from pymongo import MongoClient

# add root directory to python path
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../'))

from config.config import Config

import model as M

def validate(fix=False):
    config = Config()
    mongo_client = MongoClient(host=config.get_mongo_url())
    database_name = config.get_db_name()

    # db collections
    players_col = mongo_client[database_name][M.Player.collection_name]
    tournaments_col = mongo_client[database_name][M.Tournament.collection_name]
    rankings_col = mongo_client[database_name][M.Ranking.collection_name]
    users_col = mongo_client[database_name][M.User.collection_name]
    pending_tournaments_col = mongo_client[database_name][M.PendingTournament.collection_name]
    merges_col = mongo_client[database_name][M.Merge.collection_name]
    sessions_col = mongo_client[database_name][M.Session.collection_name]
    raw_files_col = mongo_client[database_name][M.RawFile.collection_name]
    regions_col = mongo_client[database_name][M.Region.collection_name]

    # get sets of ids for cross-referencing
    player_ids = set([p.get('_id') for p in players_col.find()])
    tournament_ids = set([t.get('_id') for t in tournaments_col.find()])
    ranking_ids = set([r.get('_id') for r in rankings_col.find()])
    user_ids = set([u.get('_id') for u in users_col.find()])
    pending_tournament_ids = set([pt.get('_id') for pt in pending_tournaments_col.find()])
    merge_ids = set([m.get('_id') for m in merges_col.find()])
    raw_file_ids = set([rf.get('_id')
        for rf in raw_files_col.find({}, {'data': 0})])
    region_ids = set([r.get('_id') for r in regions_col.find()])

    # Player checks
    for p in players_col.find():
        player = M.Player.load(p, context='db')
        error_header = '[ERROR player "{}" ({})]'.format(player.id, player.name)
        modified = False

        # check: player regions are all valid regions
        for r in player.regions:
            if r not in region_ids:
                print error_header, 'invalid region {}'.format(r)
        if fix:
            # fix: remove invalid regions from player regions
            if any([r not in region_ids for r in player.regions]):
                modified = True
                player.regions = [r for r in player.regions if r in region_ids]


        # check: ratings all have valid regions
        for r in player.ratings.keys():
            if r not in region_ids:
                print error_header, 'invalid rating region {}'.format(r)
                if fix:
                    # fix: remove rating from player
                    del player.ratings[r]
                    modified = True

        # check: merge_parent is real player if exists
        if player.merge_parent is not None:
            if player.merge_parent not in player_ids:
                print error_header, 'invalid merge_parent {}'.format(player.merge_parent)
                if fix:
                    # fix: set merge_parent to None, unset merged
                    player.merge_parent = None
                    player.merged = False

        # check: merge_children are real players
        for mc in player.merge_children:
            if mc not in player_ids:
                print error_header, 'invalid merge_child {}'.format(mc)
        if fix:
            # fix: remove child from merge_children
            if any([mc not in player_ids for mc in player.merge_children]):
                modified = True
                player.merge_children = [mc for mc in player.merge_children if mc in player_ids]

        if fix and modified:
            print error_header, 'fixing player..'
            players_col.update({'_id': player.id}, player.dump(context='db'))


    # Tournament checks
    for t in tournaments_col.find():
        tournament = M.Tournament.load(t, context='db')
        error_header = '[ERROR tournament "{}" ({})]'.format(tournament.id, tournament.name)
        modified = False

        # check: tournament empty
        if len(tournament.matches)==0 or len(tournament.players)==0:
            print error_header, 'tournament empty'

        # check: tournament regions are all valid regions
        for r in tournament.regions:
            if r not in region_ids:
                print error_header, 'invalid region {}'.format(r)
        if fix:
            # fix: remove invalid regions
            if any([r not in region_ids for r in tournament.regions]):
                modified = True
                tournament.regions = [r for r in tournament.regions if r in region_ids]

        # check: raw_id maps to real raw_file if exists
        if tournament.raw_id is not None:
            if tournament.raw_id not in raw_file_ids:
                print error_header, 'invalid raw_file_id {}'.format(tournament.raw_id)
                if fix:
                    # fix: set raw_id to None
                    modified = True
                    tournament.raw_id = None

        # check: all players are valid players
        for p in tournament.players:
            if p not in player_ids:
                print error_header, 'invalid player {}'.format(p)
                if fix:
                    # fix: FIX MANUALLY
                    print '[FIX] fix manually'

        # check: all original ids are valid players
        for p in tournament.orig_ids:
            if p not in player_ids:
                print error_header, 'invalid orig_id {}'.format(p)

        # TODO: check that orig_ids end up mapping to players?

    # Pending Tournament checks
    for pt in pending_tournaments_col.find():
        tournament = M.PendingTournament.load(pt, context='db')
        error_header = '[ERROR pending_tournament "{}" ({})]'.format(tournament.id, tournament.name)

        # check: tournament empty
        if len(tournament.matches)==0 or len(tournament.players)==0:
            print error_header, 'tournament empty'

        # check: tournament regions are all valid regions
        for r in tournament.regions:
            if r not in region_ids:
                print error_header, 'invalid region {}'.format(r)

        # check: raw_id maps to real raw_file if exists
        if tournament.raw_id is not None:
            if tournament.raw_id not in raw_file_ids:
                print error_header, 'invalid raw_file_id {}'.format(tournament.raw_id)


    # Ranking checks
    for r in rankings_col.find():
        ranking = M.Ranking.load(r, context='db')
        error_header = '[ERROR ranking ({})]'.format(ranking.id)
        modified = False

        # check: ranking region is valid region
        if ranking.region not in region_ids:
            print error_header, 'invalid region {}'.format(ranking.region)
            if fix:
                # fix: FIX MANUALLY
                print '[FIX] fix manually'

        # check: ranking tournaments are valid tournaments
        for t in ranking.tournaments:
            if t not in tournament_ids:
                print error_header, 'invalid tournament {}'.format(t)
        if fix:
            # fix: remove invalid tournaments from ranking
            if any([t not in tournament_ids for t in ranking.tournaments]):
                modified = True
                ranking.tournaments = [t for t in ranking.tournaments if t in tournament_ids]

        if fix and modified:
            print error_header, 'fixing ranking..'
            rankings_col.update({'_id': ranking.id}, ranking.dump(context='db'))


    # User checks
    for u in users_col.find():
        user = M.User.load(u, context='db')
        error_header = '[ERROR user "{}" ({})]'.format(user.username, user.id)
        modified = False

        # check: admin_regions are valid regions
        for r in user.admin_regions:
            if r not in region_ids:
                print error_header, 'invalid region {}'.format(r)
        if fix:
            # fix: remove invalid regions from admin_regions
            if any([r not in region_ids for r in user.admin_regions]):
                modified = True
                user.admin_regions = [r for r in user.admin_regions if r in region_ids]

        if fix and modified:
            print error_header, 'fixing user..'
            users_col.update({'_id': user.id}, user.dump(context='db'))

    # Session checks
    for s in sessions_col.find():
        session = M.Session.load(s, context='db')
        error_header = '[ERROR session ({})]'.format(session.session_id)

        # check: session user is valid user
        if session.user_id not in user_ids:
            print error_header, 'invalid user_id {}'.format(session.user_id)
            if fix:
                # fix: delete session
                print error_header, 'deleting session...'
                sessions_col.remove({'session_id': session.session_id})

    # Merge checks
    for m in merges_col.find():
        merge = M.Merge.load(m, context='db')
        error_header = '[ERROR merge ({})]'.format(merge.id)
        modified = False

        # check: requester is a valid user
        if merge.requester_user_id is not None and merge.requester_user_id not in user_ids:
            print error_header, 'invalid requester {}'.format(merge.requester_user_id)
            if fix:
                # fix: set requester to None
                merge.requester_user_id = None
                modified = True

        # check: source_player is a valid player
        if merge.source_player_obj_id not in player_ids:
            print error_header, 'invalid source player {}'.format(merge.source_player_obj_id)
            if fix:
                # fix: FIX MANUALLY
                print '[FIX] fix manually'

        # check: target_player is a valid player
        if merge.target_player_obj_id not in player_ids:
            print error_header, 'invalid target player {}'.format(merge.target_player_obj_id)
            if fix:
                # fix: FIX MANUALLY
                print '[FIX] fix manually'

        if fix and modified:
            print error_header, 'fixing merge..'
            merges_col.update({'_id': merge.id}, merge.dump(context='db'))

    # Fancier checks

    # check: no player with no tournaments
    pt_lists = {pid: [] for pid in player_ids}
    for t in tournaments_col.find():
        tournament = M.Tournament.load(t, context='db')
        for player in tournament.players:
            if player in player_ids:
                pt_lists[player].append(tournament.id)

    for p in players_col.find():
        player = M.Player.load(p, context='db')
        error_header = '[ERROR player "{}" ({})]'.format(player.id, player.name)
        if len(pt_lists[player.id]) == 0 and not player.merged:
            print error_header, 'player has no tournaments'
            if fix:
                print error_header, 'deleting player...'
                players_col.remove({'_id': player.id})

    print 'db validation complete'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--fix', help='fix errors in place',
                        action='store_true')
    args = parser.parse_args()

    if args.fix:
        validate(fix=True)
    else:
        validate()
