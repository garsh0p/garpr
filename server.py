from flask import Flask, request, Response, jsonify
from flask.ext import restful
from flask.ext.restful import reqparse
from flask.ext.cors import CORS
from werkzeug.datastructures import FileStorage
from dao import Dao
from bson import json_util
from bson.objectid import ObjectId
import sys
import rankings
import tournament_import_service as tournament_import
from pymongo import MongoClient
import requests
import os
from config.config import Config
import facebook
from datetime import datetime
from model import MatchResult, Tournament, PendingTournament, Merge, User, Player
import re
from scraper.tio import TioScraper
from scraper.challonge import ChallongeScraper
from scraper.smashgg import SmashGGScraper
import alias_service
from StringIO import StringIO
import Cookie
from Cookie import CookieError

TYPEAHEAD_PLAYER_LIMIT = 20
BASE_REGION = 'newjersey'

# parse config file
config = Config()

mongo_client = MongoClient(host=config.get_mongo_url())
print "parsed config: ", config.get_mongo_url()

app = Flask(__name__)
api = restful.Api(app)

player_list_get_parser = reqparse.RequestParser()
player_list_get_parser.add_argument('alias', type=str)
player_list_get_parser.add_argument('query', type=str)
player_list_get_parser.add_argument('all', type=bool)

tournament_list_get_parser = reqparse.RequestParser()
tournament_list_get_parser.add_argument('includePending', type=str)

matches_get_parser = reqparse.RequestParser()
matches_get_parser.add_argument('opponent', type=str)

rankings_get_parser = reqparse.RequestParser()
rankings_get_parser.add_argument('generateNew', type=str)

player_put_parser = reqparse.RequestParser()
player_put_parser.add_argument('name', type=str)
player_put_parser.add_argument('aliases', type=list)
player_put_parser.add_argument('regions', type=list)

tournament_put_parser = reqparse.RequestParser()
tournament_put_parser.add_argument('name', type=str)
tournament_put_parser.add_argument('date', type=str)
tournament_put_parser.add_argument('players', type=list)
tournament_put_parser.add_argument('matches', type=list)
tournament_put_parser.add_argument('regions', type=list)
tournament_put_parser.add_argument('pending', type=bool)

merges_put_parser = reqparse.RequestParser()
merges_put_parser.add_argument('source_player_id', type=str)
merges_put_parser.add_argument('target_player_id', type=str)

tournament_import_parser = reqparse.RequestParser()
tournament_import_parser.add_argument('tournament_name', type=str, required=True, help="Tournament must have a name.")
tournament_import_parser.add_argument('bracket_type', type=str, required=True, help="Bracket must have a type.")
tournament_import_parser.add_argument('challonge_url', type=str)
tournament_import_parser.add_argument('tio_file', type=str)
tournament_import_parser.add_argument('tio_bracket_name', type=str)

pending_tournament_put_parser = reqparse.RequestParser()
pending_tournament_put_parser.add_argument('name', type=str)
pending_tournament_put_parser.add_argument('players', type=list)
pending_tournament_put_parser.add_argument('matches', type=list)
pending_tournament_put_parser.add_argument('regions', type=list)
pending_tournament_put_parser.add_argument('alias_to_id_map', type=list)

session_put_parser = reqparse.RequestParser()
session_put_parser.add_argument('username', type=str)
session_put_parser.add_argument('password', type=str)

session_delete_parser = reqparse.RequestParser()
session_delete_parser.add_argument('session_id', location='cookies', type=str)

#TODO: major refactor to move auth code to a decorator

class InvalidAccessToken(Exception):
    pass

def is_allowed_origin(origin):
    dragon = r"http(s)?:\/\/(stage\.|www\.)?(notgarpr\.com|192\.168\.33\.1(0)?|njssbm\.com)(\:[\d]*)?$"
    return re.match(dragon, origin)

def convert_object_id(json_dict):
    json_dict['id'] = str(json_dict['_id'])
    del json_dict['_id']

def convert_object_id_list(json_dict_list):
    for j in json_dict_list:
        convert_object_id(j)

def get_user_from_request(request, dao):
    session_id = request.cookies.get('session_id')
    print "session: %s" % session_id
    return dao.get_user_by_session_id_or_none(session_id)

def is_user_admin_for_region(user, region):
    if not region:
        return False
    if not user.admin_regions:
        return False
    if "".join(region) in user.admin_regions:
        return True
    return False

def is_user_admin_for_regions(user, regions):
    '''
    returns true is user is an admin for ANY of the regions
    '''
    if len(set(regions).intersection(user.admin_regions)) == 0:
        return False
    else:
        return True

class RegionListResource(restful.Resource):
    def get(self):
        regions_dict = {'regions': [r.get_json_dict() for r in Dao.get_all_regions(mongo_client)]}

        for region in regions_dict['regions']:
            region['id'] = region['_id']
            del region['_id']

        return regions_dict

class PlayerListResource(restful.Resource):
    def _player_matches_query(self, player, query):
        player_name = player.name.lower()
        query = query.lower()

        # try matching the full name first
        if player_name == query:
            return True

        # if query is >= 3 chars, allow substring matching
        # this is to allow players with very short names to appear for small search terms
        if len(query) >= 3 and query in player_name:
            return True

        # split the player name on common dividers and try to match against each part starting from the beginning
        # split on: . | space
        tokens = re.split('\.|\|| ', player_name)
        for token in tokens:
            if token:
                if token.startswith(query):
                    return True

        # no match
        return False

    def _get_players_matching_query(self, players, query):
        matching_players = []

        for player in players:
            if self._player_matches_query(player, query):
                matching_players.append(player)

        # move exact matches to the front so that short names are guaranteed to appear
        for i in xrange(len(matching_players)):
            player = matching_players[i]
            if player.name.lower() == query:
                matching_players.insert(0, matching_players.pop(i))

        matching_players = matching_players[:TYPEAHEAD_PLAYER_LIMIT]

        return matching_players

    def get(self, region):
        args = player_list_get_parser.parse_args()
        dao = Dao(region, mongo_client=mongo_client)
        if not dao:
            return 'Dao not found', 404
        return_dict = {}

        # single player matching alias within region
        if args['alias']:
            return_dict['players'] = []
            db_player = dao.get_player_by_alias(args['alias'])
            if db_player:
                return_dict['players'].append(db_player.get_json_dict())
        # search multiple players by name across all regions
        elif args['query']:
            all_players = dao.get_all_players(all_regions=True) #TODO: none checks on below list comprehensions
            return_dict['players'] = [p.get_json_dict() for p in self._get_players_matching_query(all_players, args['query'])]
        # get all players in all regions
        elif args['all']:
            all_players = dao.get_all_players(all_regions=True)
            return_dict['players'] = [p.get_json_dict() for p in sorted(all_players, key=lambda player : player.name.lower())]
        # all players within region
        else:
            print 'test'
            return_dict['players'] = [p.get_json_dict() for p in sorted(dao.get_all_players(), key=lambda player : player.name.lower())]

        convert_object_id_list(return_dict['players'])

        # TODO: write convert_player_to_response function
        # remove extra fields
        for player in return_dict['players']:
            del player['aliases']
            del player['ratings']

            player['merge_parent'] = str(player['merge_parent'])
            player['merge_children'] = [str(child) for child in player['merge_children']]


        return return_dict

class PlayerResource(restful.Resource):
    def get(self, region, id):
        dao = Dao(region, mongo_client=mongo_client)
        if not dao:
            return 'Dao not found', 404
        player = None
        try:
            player = dao.get_player_by_id(ObjectId(id))
        except:
            return 'Invalid ObjectID', 400
        if not player:
            return 'Player not found', 404

        return_dict = player.get_json_dict()
        convert_object_id(return_dict)
        if not return_dict['merge_parent'] is None:
            return_dict['merge_parent'] = str(return_dict['merge_parent'])
        return_dict['merge_children'] = [str(child) for child in return_dict['merge_children']]

        return return_dict

    def put(self, region, id):
        dao = Dao(region, mongo_client=mongo_client)
        if not dao:
            return 'Dao not found', 404
        player = None
        try:
            player = dao.get_player_by_id(ObjectId(id))
        except:
            return 'Invalid ObjectID', 400
        if not player:
            return "No player found with that region/id.", 404

        # TODO auth for this needs to be different, otherwise an admin can tag with their region and then edit everything
        user = get_user_from_request(request, dao)
        if not user:
            return 'Permission denied', 403

        # remove auth for now (for players not part of any regions)
        # I think possibly we should remove admin_regions or at least
        # figure out how we want them to work;
        # if not is_user_admin_for_regions(user, player.regions):
        #     return 'Permission denied', 403

        args = player_put_parser.parse_args()

        if args['name']:
            player.name = args['name']
        if args['aliases'] is not None:
            for a in args['aliases']:
                if not isinstance(a, unicode):
                    return "each alias must be a string", 400
            new_aliases = [a.lower() for a in args['aliases']]
            if player.name.lower() not in new_aliases:
                return "aliases must contain the players name!", 400
            player.aliases = new_aliases
        if args['regions'] is not None:
            for a in args['regions']:
                if not isinstance(a, unicode):
                    return "each region must be a string", 400
            player.regions = args['regions']

        dao.update_player(player)

        # TODO: add canonical way to responsify objects
        return_dict = player.get_json_dict()
        convert_object_id(return_dict)
        if not return_dict['merge_parent'] is None:
            return_dict['merge_parent'] = str(return_dict['merge_parent'])
        return_dict['merge_children'] = [str(child) for child in return_dict['merge_children']]

        return return_dict

class TournamentListResource(restful.Resource):
    def get(self, region):
        dao = Dao(region, mongo_client=mongo_client)
        if not dao:
            return 'Dao not found', 404
        include_pending_tournaments = False
        args = tournament_list_get_parser.parse_args()
        if args['includePending'] and args['includePending'] == 'true':
            user = get_user_from_request(request, dao)
            include_pending_tournaments = user and is_user_admin_for_region(user, region)

        tournaments = dao.get_all_tournaments(regions=[region])
        # if not tournaments:
        #     return 'Dao couldnt find any tournaments, not good man, not good', 404
        all_tournament_jsons = [t.get_json_dict() for t in tournaments]

        if include_pending_tournaments:
            # add a pending field for all existing tournaments
            for t in all_tournament_jsons:
                t['pending'] = False

            pending_tournaments = dao.get_all_pending_tournaments(regions=[region])
            if pending_tournaments:
                for p in pending_tournaments:
                    p = p.get_json_dict()
                    p['pending'] = True
                    del p['alias_to_id_map']
                    all_tournament_jsons.append(p)

        return_dict = {}
        return_dict['tournaments'] = all_tournament_jsons
        convert_object_id_list(return_dict['tournaments'])

        for t in return_dict['tournaments']:
            t['date'] = t['date'].strftime("%x") if t['date'] else '20XX'

            # remove extra fields
            del t['raw']
            del t['matches']
            del t['players']
            del t['type']
            if 'orig_ids' in t:
                del t['orig_ids']

        return return_dict

    def post(self, region):
        print "in tournamentList POST"
        dao = Dao(region, mongo_client=mongo_client)
        if not dao:
            return 'Dao not found', 404
        user = get_user_from_request(request, dao)
        if not user:
            return 'Permission denied', 403
        if not is_user_admin_for_region(user, region):
            return 'Permission denied', 403
        parser = reqparse.RequestParser()
        parser.add_argument('type', type=str, location='json')
        parser.add_argument('data', type=unicode, location='json')
        parser.add_argument('bracket', type=str, location='json')
        args = parser.parse_args()

        if args['data'] is None:
            return "data required", 400

        the_bytes = bytearray(args['data'], "utf8")

        if the_bytes[0] == 0xef:
            print "found magic numbers"
            return "magic numbers!", 503

        type = args['type']
        data = args['data']
        pending_tournament = None

        try:
            if type == 'tio':
                if args['bracket'] is None:
                    return "Missing bracket name", 400
                data_bytes = bytes(data)
                if data_bytes[0] == '\xef':
                    data = data[:3]
                scraper = TioScraper(data, args['bracket'])
            elif type == 'challonge':
                scraper = ChallongeScraper(data)
            elif type == 'smashgg':
                scraper = SmashGGScraper(data)
            else:
                return "Unknown type", 400
            pending_tournament = PendingTournament.from_scraper(type, scraper, region)
        except:
            return 'Scraper encountered an error', 400

        if not pending_tournament:
            return 'Scraper encountered an error', 400

        try:
            pending_tournament.alias_to_id_map = alias_service.get_alias_to_id_map_in_list_format(dao, pending_tournament.players)
        except:
            return 'Alias service encountered an error', 400

        try:
            new_id = dao.insert_pending_tournament(pending_tournament)
            return_dict = {
                'id': str(new_id)
            }
            return return_dict
        except:
            return 'Dao insert_pending_tournament encountered an error', 400

        return 'Unknown error!', 400

def convert_tournament_to_response(tournament, dao):
    return_dict = tournament.get_json_dict()
    convert_object_id(return_dict)

    return_dict['date'] = return_dict['date'].strftime("%x") if return_dict['date'] else '20XX'

    return_dict['players'] = [{
            'id': str(p),
            'name': dao.get_player_by_id(p).name
        } for p in return_dict['players']]

    return_dict['matches'] = [{
            'winner_id': str(m['winner']),
            'loser_id': str(m['loser']),
            'winner_name': dao.get_player_by_id(m['winner']).name,
            'loser_name': dao.get_player_by_id(m['loser']).name
        } for m in return_dict['matches']]

    # remove extra fields
    del return_dict['raw']
    del return_dict['orig_ids']

    return return_dict

def convert_pending_tournament_to_response(pending_tournament, dao):
    return_dict = pending_tournament.get_json_dict()
    convert_object_id(return_dict)

    return_dict['date'] = return_dict['date'].strftime("%x") if return_dict['date'] else '20XX'

    # stringify objectids
    for alias_item in return_dict['alias_to_id_map']:
        alias_item['player_id'] = str(alias_item['player_id']) if alias_item['player_id'] else None

    # remove extra fields
    del return_dict['raw']

    return return_dict

def convert_request_to_pending_tournament(data):
    alias_to_id_map = []
    for alias_item in data["alias_to_id_map"]:
        try:
            alias_item['player_id'] = ObjectId(alias_item['player_id']) if alias_item['player_id'] else None
        except:
            print 'Error converting player id to ObjectID'
    return data

class TournamentResource(restful.Resource):
    def get(self, region, id):
        dao = Dao(region, mongo_client=mongo_client)
        if not dao:
            return 'Dao not found', 404
        response = None
        tournament = None
        try:
            tournament = dao.get_tournament_by_id(ObjectId(id))
        except:
            return 'Invalid ObjectID', 400
        if tournament is not None:
            response = convert_tournament_to_response(tournament, dao)
        else:
            user = get_user_from_request(request, dao)
            pending_tournament = dao.get_pending_tournament_by_id(ObjectId(id)) #this usage is safe, if the ID was fake, we would have already blown the coop above
            if not pending_tournament:
                return 'Not found!', 404
            if not user:
                return 'Permission denied', 403
            if not is_user_admin_for_regions(user, pending_tournament.regions):
                return 'Permission denied', 403
            response = convert_pending_tournament_to_response(pending_tournament, dao)

        return response

    def put(self, region, id):
        dao = Dao(region, mongo_client=mongo_client)
        if not dao:
            return 'Dao not found', 404
        tournament = None

        args = tournament_put_parser.parse_args()

        try:
            if args['pending']:
                tournament = dao.get_pending_tournament_by_id(ObjectId(id))
                print tournament
            else:
                tournament = dao.get_tournament_by_id(ObjectId(id))
        except:
            return 'Invalid ObjectID', 400
        if not tournament:
            return "No tournament found with that id.", 404

        # TODO auth for this needs to be different, otherwise an admin can tag with their region and then edit everything
        user = get_user_from_request(request, dao)
        if not user:
            return 'Permission denied', 403
        if not is_user_admin_for_regions(user, tournament.regions):
            return 'Permission denied', 403


        #TODO: should we do validation that matches and players are compatible here?
        try:
            if args['name']:
                tournament.name = args['name']
            if args['date']:
                try:
                    tournament.date = datetime.strptime(args['date'].strip(), '%m/%d/%y')
                except:
                    return "Invalid date format", 400
            if args['players']:
                for p in args['players']:
                    if not isinstance(p, unicode):
                        return "each player must be a string", 400
                tournament.players = [ObjectId(i) for i in args['players']]
            if args['matches']:
                for d in args['matches']:
                    if not isinstance(d, dict):
                        return "matches must be a dict", 400
                    if (not isinstance(d['winner'], unicode)) or (not isinstance(d['loser'], unicode)):
                        return "winner and loser must be strings", 400
                #turn the list of dicts into list of matchresults
                matches = [MatchResult(winner=ObjectId(m['winner']), loser=ObjectId(m['loser'])) for m in args['matches']]
                tournament.matches = matches
            if args['regions']:
                for p in args['regions']:
                    if not isinstance(p, unicode):
                        return "each region must be a string", 400
                tournament.regions = args['regions']
        except:
            return 'Invalid ObjectID', 400

        try:
            if args['pending']:
                dao.update_pending_tournament(tournament)
            else:
                dao.update_tournament(tournament)
        except:
            return 'Update Tournament Error', 400

        if args['pending']:
            return convert_pending_tournament_to_response(dao.get_pending_tournament_by_id(tournament.id), dao)
        else:
            return convert_tournament_to_response(dao.get_tournament_by_id(tournament.id), dao)

    def delete(self, region, id):
        """ Deletes a tournament.
            Route restricted to admins for this region.
            Be VERY careful when using this """
        dao = Dao(region, mongo_client=mongo_client)
        if not dao:
            return 'Dao not found', 404
        user = get_user_from_request(request, dao)
        if not user:
            return 'Permission denied', 403

        tournament_to_delete = None
        try:
            tournament_to_delete = dao.get_pending_tournament_by_id(ObjectId(id))
        except:
            return 'Invalid ObjectID', 400
        if tournament_to_delete: #its a pending tournament
            if not is_user_admin_for_regions(user, tournament_to_delete.regions):
                return 'Permission denied', 403
            dao.delete_pending_tournament(tournament_to_delete)
        else:  #not a pending tournament, might be a finalized tournament
            tournament_to_delete = dao.get_tournament_by_id(ObjectId(id)) #ID must be valid if we got here
            if not tournament_to_delete: #can't find anything, whoops
                return "No tournament (pending or finalized) found with that id.", 404
            if not is_user_admin_for_regions(user, tournament_to_delete.regions):
                return 'Permission denied', 403
            resp = dao.delete_tournament(tournament_to_delete)

        return {"success": True}


class PendingTournamentListResource(restful.Resource):
    def get(self, region):
        print "pending tournament get!"
        dao = Dao(region, mongo_client=mongo_client)
        if not dao:
            return 'Dao not found', 404
        return_dict = {}
        the_tourney = None
        try:
            tournament_import.get_pending_tournaments(region, dao)
        except:
            return 'Error in get_pending_tournaments', 400
        if not the_tourney:
            return 'Not found', 404
        return_dict['pending_tournaments'] = the_tourney
        convert_object_id_list(return_dict['pending_tournaments'])

        for t in return_dict['pending_tournaments']:
            t['date'] = t['date'].strftime("%x") if t['date'] else '20XX'
            # whether all aliases have been mapped to players or not
            # necessary condition for the tournament to be ready to be finalized
            t['alias_mapping_finished'] = t.are_all_aliases_mapped()

            # remove extra fields
            del t['raw']
            del t['matches']
            del t['players']

        return return_dict


class PendingTournamentResource(restful.Resource):
    """
    Currently only updates the alias_to_id_map in the pending tournament
    """
    def put(self, region, id):
        print "in pending tournament put"

        dao = Dao(region, mongo_client=mongo_client)
        if not dao:
            return 'Dao not found', 404
        pending_tournament = None
        try:
            pending_tournament = dao.get_pending_tournament_by_id(ObjectId(id))
        except:
            return 'Invalid ObjectID', 400
        if not pending_tournament:
            return "No pending tournament found with that id.", 404

        user = get_user_from_request(request, dao)
        if not user:
            return 'Permission denied', 403
        if not is_user_admin_for_regions(user, pending_tournament.regions):
            return 'Permission denied', 403

        args = pending_tournament_put_parser.parse_args()
        print "Args", args
        data = convert_request_to_pending_tournament(args)
        if not data:
            return 'Request couldnt be converted to pending tournament', 400

        try:
            print "Incoming", data["alias_to_id_map"]
            print "DB", pending_tournament.alias_to_id_map
            for alias_item in data["alias_to_id_map"]:
                player_alias = alias_item["player_alias"]
                player_id = alias_item["player_id"]
                pending_tournament.set_alias_id_mapping(player_alias, player_id)
        except:
            print 'Error processing alias_to_id map'
            return 'Error processing alias_to_id map', 400

        try:
            dao.update_pending_tournament(pending_tournament)
            response = convert_pending_tournament_to_response(pending_tournament, dao)
            return response
        except:
            return 'Encountered an error inserting pending tournament', 400

class FinalizeTournamentResource(restful.Resource):
    """ Converts a pending tournament to a tournament.
        Works only if the PendingTournament's alias_to_id_map is completely filled out.
        Route restricted to admins for this region. """
    def post(self, region, id):
        print "finalize tournament post"
        dao = Dao(region, mongo_client=mongo_client)
        if not dao:
            return 'Dao not found', 404
        pending_tournament = None
        try:
            pending_tournament = dao.get_pending_tournament_by_id(ObjectId(id))
        except:
            return 'Invalid ObjectID', 400
        if not pending_tournament:
            return 'No pending tournament found with that id.', 400
        user = get_user_from_request(request, dao)
        if not user:
            return 'Permission denied', 403
        if not is_user_admin_for_regions(user, pending_tournament.regions):
            return 'Permission denied', 403

        new_player_names = []
        for mapping in pending_tournament.alias_to_id_map:
            if mapping["player_id"] == None:
                new_player_names.append(mapping["player_alias"])

        for player_name in new_player_names:
            player = Player.create_with_default_values(player_name, region)
            player_id = dao.insert_player(player)
            pending_tournament.set_alias_id_mapping(player_name, player_id)

        # validate players in this tournament
        for mapping in pending_tournament.alias_to_id_map:
            try:
                player_id = mapping["player_id"]
                # TODO: reduce queries to DB by batching
                player = dao.get_player_by_id(player_id)
                if player.merged:
                    return "Player {} has already been merged".format(player.name), 400
            except:
                return "Not all player ids are valid", 400


        try:
            dao.update_pending_tournament(pending_tournament)
            tournament = Tournament.from_pending_tournament(pending_tournament)
            tournament_id = dao.insert_tournament(tournament)
            dao.delete_pending_tournament(pending_tournament)
            return {"success": True, "tournament_id": str(tournament_id)}
        except ValueError:
            return 'Not all player aliases in this pending tournament have been mapped to player ids.', 400
        except:
            return 'Dao threw an error somewhere', 400

class RankingsResource(restful.Resource):
    def get(self, region):
        dao = Dao(region, mongo_client=mongo_client)
        if not dao:
            return 'Dao not found', 404
        return_dict = dao.get_latest_ranking().get_json_dict()
        if not return_dict:
            return 'Dao couldnt give us rankings', 400
        del return_dict['_id']
        return_dict['time'] = str(return_dict['time'])
        return_dict['tournaments'] = [str(t) for t in return_dict['tournaments']]

        ranking_list = []
        for r in return_dict['ranking']:
            player = dao.get_player_by_id(r['player'])
            if player:
                r['name'] = player.name
                r['id'] = str(r.pop('player'))
                ranking_list.append(r)

        return_dict['ranking'] = ranking_list

        return return_dict

    def post(self, region):
        dao = Dao(region, mongo_client=mongo_client)
        if not dao:
            return 'Dao not found', 404
        user = get_user_from_request(request, dao)
        if not user:
            return 'Permission denied', 403
        if not is_user_admin_for_region(user, region):
            return 'Permission denied', 403

        # we pass in now so we can mock it out in tests
        now = datetime.now()
        rankings.generate_ranking(dao, now=now)

        return self.get(region)

class MatchesResource(restful.Resource):
    def get(self, region, id):
        dao = Dao(region, mongo_client=mongo_client)
        if not dao:
            return 'Dao not found', 404
        args = matches_get_parser.parse_args()
        return_dict = {}

        player = None
        try:
            player = dao.get_player_by_id(ObjectId(id))
        except:
            return 'Invalid ObjectID', 400


        return_dict['player'] = {'id': str(player.id), 'name': player.name}
        player_list = [player]

        opponent_id = args['opponent']
        if opponent_id is not None:
            try:
                opponent = dao.get_player_by_id(ObjectId(args['opponent']))
                return_dict['opponent'] = {'id': str(opponent.id), 'name': opponent.name}
                player_list.append(opponent)
            except:
                return 'Invalid ObjectID', 400

        match_list = []
        return_dict['matches'] = match_list
        return_dict['wins'] = 0
        return_dict['losses'] = 0

        if player.merged:
            # no need to look up tournaments for merged players
            return return_dict

        tournaments = dao.get_all_tournaments(players=player_list)
        if not tournaments:
            return 'No tournaments found', 400
        for tournament in tournaments:
            for match in tournament.matches:
                if (opponent_id is not None and match.contains_players(player.id, opponent.id)) or \
                        (opponent_id is None and match.contains_player(player.id)):
                    match_dict = {}
                    match_dict['tournament_id'] = str(tournament.id)
                    match_dict['tournament_name'] = tournament.name
                    match_dict['tournament_date'] = tournament.date.strftime("%x")
                    match_dict['opponent_id'] = str(match.get_opposing_player_id(player.id))
                    try:
                        match_dict['opponent_name'] = dao.get_player_by_id(ObjectId(match_dict['opponent_id'])).name
                    except:
                        return 'Invalid ObjectID', 400
                    if match.did_player_win(player.id):
                        match_dict['result'] = 'win'
                        return_dict['wins'] += 1
                    else:
                        match_dict['result'] = 'lose'
                        return_dict['losses'] += 1

                    match_list.append(match_dict)

        return return_dict


class MergeListResource(restful.Resource):
    def get(self, region):
        dao = Dao(region, mongo_client=mongo_client)
        if not dao:
            return 'Dao not found', 404
        user = get_user_from_request(request, dao)

        if not user:
            return 'Permission denied', 403
        if not user.admin_regions:
            return "user is not an admin", 403

        return_dict = {}
        return_dict['merges'] = [m.get_json_dict() for m in dao.get_all_merges()]

        for merge in return_dict['merges']:
            # TODO: store names in merge object
            source_player = dao.get_player_by_id(merge['source_player_obj_id'])
            target_player = dao.get_player_by_id(merge['target_player_obj_id'])

            merge['source_player_name'] = source_player.name
            merge['target_player_name'] = target_player.name
            merge['requester_name'] = user.username;

            # cast objectIDs to strings
            merge['source_player_obj_id'] = str(merge['source_player_obj_id'])
            merge['target_player_obj_id'] = str(merge['target_player_obj_id'])
            merge['requester_user_id'] = str(merge['requester_user_id'])
            del merge['time']

        convert_object_id_list(return_dict['merges'])
        return return_dict



    def put(self, region):
        dao = Dao(region, mongo_client=mongo_client)
        if not dao:
            return 'Dao not found', 404
        user = get_user_from_request(request, dao)

        if not user:
            return 'Permission denied', 403
        if not user.admin_regions:
            return "user is not an admin", 403

        args = merges_put_parser.parse_args()
        try:
            print args
            source_player_id = ObjectId(args['source_player_id'])
            target_player_id = ObjectId(args['target_player_id'])
        except:
            return "invalid ids, that wasn't an ObjectID", 400
        # the above should validate that we have real objectIDs
        # now lets validate that both of those players exist
        player1 = dao.get_player_by_id(source_player_id)
        player2 = dao.get_player_by_id(target_player_id)

        if not player1:
            return "source_player not found", 400
        if not player2:
            return "target_player not found", 400
        if not is_user_admin_for_regions(user, player1.regions):
            return "Permission denied", 403
        if not is_user_admin_for_regions(user, player2.regions):
            return "Permission denied", 403

        #get curr time
        now = datetime.now()
        the_merge = Merge(user.id,
                          source_player_id,
                          target_player_id,
                          now,
                          id=ObjectId())
        try:
            dao.insert_merge(the_merge)
            return_dict = {'status': "success", 'id': str(the_merge.id)}
            return return_dict, 200
        except Exception as e:
            print 'error merging players: ' + str(e)
            return 'error merging players: ' + str(e), 400

class MergeResource(restful.Resource):
    def get(self, region, id):
        # TODO: decide if we want this
        pass

    def delete(self, region, id):
        dao = Dao(region, mongo_client=mongo_client)
        if not dao:
            return 'Dao not found', 404
        user = get_user_from_request(request, dao)

        if not user:
            return 'Permission denied', 403
        if not user.admin_regions:
            return "user is not an admin", 403

        try:
            merge_id = ObjectId(id)
        except:
            return "invalid ids, that wasn't an ObjectID", 400

        try:
            the_merge = dao.get_merge(merge_id)
            dao.undo_merge(the_merge)
            return "successfully undid merge", 200
        except Exception as e:
            print 'error merging players: ' + str(e)
            return 'error merging players: ' + str(e), 400

class SessionResource(restful.Resource):
    ''' logs a user in. i picked put over post because its harder to CSRF, not that CSRFing login actually matters'''
    def put(self):
        args = session_put_parser.parse_args() #parse args
        dao = Dao(None, mongo_client=mongo_client)
        if not dao:
            return 'Dao not found', 404
        session_id = dao.check_creds_and_get_session_id_or_none(args['username'], args['password'])
        if not session_id:
            return 'Permission denied', 403
        resp = jsonify({"status": "connected"})
        resp.set_cookie('session_id', session_id)
        return resp

    ''' logout, destroys session_id mapping on client and server side '''
    def delete(self):
        args = session_delete_parser.parse_args()
        dao = Dao(None, mongo_client=mongo_client)
        if not dao:
            return 'Dao not found', 404
        logout_success = dao.logout_user_or_none(args['session_id'])
        if not logout_success:
            return 'who is you', 404
        return 'logout success', 200, {'Set-Cookie': "session_id=deleted; expires=Thu, 01 Jan 1970 00:00:00 GMT"}

    def get(self):
        dao = Dao(None, mongo_client=mongo_client)
        if not dao:
            return 'Dao not found', 404
        user = get_user_from_request(request, dao)
        if not user:
            return 'you are not a real user', 400
        return_dict = user.clean_user
        return_dict['id'] = return_dict['_id']
        del return_dict['_id']

        return return_dict

@api.representation('text/plain')
class LoaderIOTokenResource(restful.Resource):
    def get(self):
        return Response(config.get_loaderio_token())

@app.after_request
def add_security_headers(resp):
    resp.headers['Strict-Transport-Security'] = "max-age=31536000; includeSubdomains"
    resp.headers['Content-Security-Policy'] = "default-src https: data: 'unsafe-inline' 'unsafe-eval'"
    resp.headers['X-Frame-Options'] = "DENY"
    resp.headers['X-XSS-Protection'] = "1; mode=block"
    resp.headers['X-Content-Type-Options'] = "nosniff"
    return resp

@app.after_request
def add_cors(resp):
    """ Ensure all responses have the CORS headers. This ensures any failures are also accessible
        by the client. """
    the_origin = request.headers.get('Origin','*')
    if not is_allowed_origin(the_origin):
        return resp
    resp.headers['Access-Control-Allow-Origin'] =  the_origin
    resp.headers['Access-Control-Allow-Credentials'] = 'true'
    resp.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS, GET, PUT, DELETE'
    resp.headers['Access-Control-Allow-Headers'] = request.headers.get('Access-Control-Request-Headers', 'Authorization' )
    resp.headers["Access-Control-Expose-Headers"] = "Set-Cookie"
    # set low for debugging
    if app.debug:
        resp.headers['Access-Control-Max-Age'] = '1'
    return resp


api.add_resource(MergeResource, '/<string:region>/merges/<string:id>')
api.add_resource(MergeListResource, '/<string:region>/merges')

api.add_resource(RegionListResource, '/regions')

api.add_resource(PlayerListResource, '/<string:region>/players')
api.add_resource(PlayerResource, '/<string:region>/players/<string:id>')

api.add_resource(MatchesResource, '/<string:region>/matches/<string:id>')

api.add_resource(TournamentListResource, '/<string:region>/tournaments')
api.add_resource(TournamentResource, '/<string:region>/tournaments/<string:id>')
api.add_resource(PendingTournamentResource, '/<string:region>/pending_tournaments/<string:id>')
api.add_resource(FinalizeTournamentResource, '/<string:region>/tournaments/<string:id>/finalize')

api.add_resource(PendingTournamentListResource, '/<string:region>/tournaments/pending')
api.add_resource(RankingsResource, '/<string:region>/rankings')

api.add_resource(SessionResource, '/users/session')

api.add_resource(LoaderIOTokenResource, '/{}/'.format(config.get_loaderio_token()))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(sys.argv[1]), debug=(sys.argv[2] == 'True'))
