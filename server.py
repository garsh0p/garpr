from flask import Flask, request
from flask.ext import restful
from flask.ext.restful import reqparse
from flask.ext.cors import CORS
from dao import Dao
from bson.json_util import dumps
from bson.objectid import ObjectId
import sys
import rankings
from pymongo import MongoClient
import requests
import os
from config.config import Config
import facebook
from datetime import datetime
from model import MatchResult

DEBUG_TOKEN_URL = 'https://graph.facebook.com/debug_token?input_token=%s&access_token=%s'

# parse config file
config_full_path = os.path.join(os.path.dirname(__file__), 'config/config.ini')
config = Config(config_file_path=config_full_path)

mongo_client = MongoClient(host=config.get_mongo_url())

app = Flask(__name__)
cors = CORS(app, origins='*', headers=['Authorization', 'Content-Type'])
api = restful.Api(app)

player_list_get_parser = reqparse.RequestParser()
player_list_get_parser.add_argument('alias', type=str)

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
tournament_put_parser.add_argument('date', type=int)
tournament_put_parser.add_argument('players', type=list)
tournament_put_parser.add_argument('matches', type=list)
tournament_put_parser.add_argument('regions', type=list)

class InvalidAccessToken(Exception):
    pass

def convert_object_id(json_dict):
    json_dict['id'] = str(json_dict['_id'])
    del json_dict['_id']

def convert_object_id_list(json_dict_list):
    for j in json_dict_list:
        convert_object_id(j)

def _get_user_id_from_facebook_access_token(access_token):
    '''Calls Facebook's debug_token endpoint to validate the token. Returns the user id if validation passes,
    otherwise throws an exception.'''
    url = DEBUG_TOKEN_URL % (access_token, config.get_fb_app_token())
    r = requests.get(url)
    json_data = r.json()['data']

    if json_data['app_id'] != config.get_fb_app_id() or not json_data['is_valid']:
        raise InvalidAccessToken('Facebook access token is invalid')

    return json_data['user_id']

def get_user_from_access_token(headers, dao):
    access_token = headers['Authorization']
    user_id = _get_user_id_from_facebook_access_token(access_token)
    user = dao.get_or_create_user_by_id(user_id)

    # populate the user's full name if it's blank
    if not user.full_name:
        graph = facebook.GraphAPI(access_token)
        profile = graph.get_object('me')
        user.full_name = profile['name']
        dao.update_user(user)

    return user

def is_user_admin_for_region(user, region):
    return region in user.admin_regions

def is_user_admin_for_regions(user, regions):
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
    def get(self, region):
        args = player_list_get_parser.parse_args()
        dao = Dao(region, mongo_client=mongo_client)
        return_dict = {}

        if args['alias'] is not None:
            return_dict['players'] = []
            db_player = dao.get_player_by_alias(args['alias'])
            if db_player:
                return_dict['players'].append(db_player.get_json_dict())
        else:
            return_dict['players'] = [p.get_json_dict() for p in dao.get_all_players()]

        convert_object_id_list(return_dict['players'])

        # remove extra fields
        for player in return_dict['players']:
            del player['regions']
            del player['aliases']
            del player['ratings']

        return return_dict

class PlayerResource(restful.Resource):
    def get(self, region, id):
        dao = Dao(region, mongo_client=mongo_client)
        player = dao.get_player_by_id(ObjectId(id))

        return_dict = player.get_json_dict()
        convert_object_id(return_dict)

        return return_dict

    def put(self, region, id):
        dao = Dao(region, mongo_client=mongo_client)
        player = dao.get_player_by_id(ObjectId(id))

        if not player:
            return "No player found with that region/id.", 400

        # TODO auth for this needs to be different, otherwise an admin can tag with their region and then edit everything
        user = get_user_from_access_token(request.headers, dao)
        if not is_user_admin_for_regions(user, player.regions):
            return 'Permission denied', 403

        args = player_put_parser.parse_args()

        if args['name']:
            player.name = args['name']
        if args['aliases']:
            for a in args['aliases']:
                if not isinstance(a, unicode):
                    return "each alias must be a string", 400
            new_aliases = [a.lower() for a in args['aliases']]
            if player.name.lower() not in new_aliases:
                return "aliases must contain the players name!", 400
            player.aliases = new_aliases
        if args['regions']:
            for a in args['regions']:
                if not isinstance(a, unicode):
                    return "each region must be a string", 400
            player.regions = args['regions']

        dao.update_player(player)

class PlayerRegionResource(restful.Resource):
    def put(self, region, id, region_to_change):
        dao = Dao(region, mongo_client=mongo_client)
        user = get_user_from_access_token(request.headers, dao)
        if not is_user_admin_for_region(user, region_to_change):
            return 'Permission denied', 403

        player = dao.get_player_by_id(ObjectId(id))
        if not region_to_change in player.regions:
            player.regions.append(region_to_change)
            dao.update_player(player)

        return_dict = dao.get_player_by_id(player.id).get_json_dict()
        convert_object_id(return_dict)
        return return_dict

    def delete(self, region, id, region_to_change):
        dao = Dao(region, mongo_client=mongo_client)
        user = get_user_from_access_token(request.headers, dao)
        if not is_user_admin_for_region(user, region_to_change):
            return 'Permission denied', 403

        player = dao.get_player_by_id(ObjectId(id))
        if region_to_change in player.regions:
            player.regions.remove(region_to_change)
            dao.update_player(player)

        return_dict = dao.get_player_by_id(player.id).get_json_dict()
        convert_object_id(return_dict)
        return return_dict

class TournamentListResource(restful.Resource):
    def get(self, region):
        dao = Dao(region, mongo_client=mongo_client)
        return_dict = {}
        return_dict['tournaments'] = [t.get_json_dict() for t in dao.get_all_tournaments(regions=[region])]
        convert_object_id_list(return_dict['tournaments'])

        for t in return_dict['tournaments']:
            t['date'] = t['date'].strftime("%x")

            # remove extra fields
            del t['raw']
            del t['matches']
            del t['players']
            del t['type']

        return return_dict

def convert_tournament_to_response(tournament, dao):
    return_dict = tournament.get_json_dict()
    convert_object_id(return_dict)

    return_dict['date'] = return_dict['date'].strftime("%x")

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

    return return_dict

class TournamentResource(restful.Resource):
    def get(self, region, id):
        dao = Dao(region, mongo_client=mongo_client)
        tournament = dao.get_tournament_by_id(ObjectId(id))
        return convert_tournament_to_response(tournament, dao)

    def put(self, region, id):
        dao = Dao(region, mongo_client=mongo_client)
        tournament = dao.get_tournament_by_id(ObjectId(id))
        if not tournament:
            return "No tournament found with that id.", 400

        # TODO auth for this needs to be different, otherwise an admin can tag with their region and then edit everything
        user = get_user_from_access_token(request.headers, dao)
        if not is_user_admin_for_regions(user, tournament.regions):
            return 'Permission denied', 403

        args = tournament_put_parser.parse_args()

        #TODO: should we do validation that matches and players are compatible here?
        if args['name']:
            tournament.name = args['name']
        if args['date']:
            tournament.date = datetime.fromordinal(args['date'])
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

        dao.update_tournament(tournament)
        
class TournamentRegionResource(restful.Resource):
    def put(self, region, id, region_to_change):
        dao = Dao(region, mongo_client=mongo_client)
        user = get_user_from_access_token(request.headers, dao)
        if not is_user_admin_for_region(user, region_to_change):
            return 'Permission denied', 403

        tournament = dao.get_tournament_by_id(ObjectId(id))
        if not region_to_change in tournament.regions:
            tournament.regions.append(region_to_change)
            dao.update_tournament(tournament)

        return convert_tournament_to_response(dao.get_tournament_by_id(tournament.id), dao)

    def delete(self, region, id, region_to_change):
        dao = Dao(region, mongo_client=mongo_client)
        user = get_user_from_access_token(request.headers, dao)
        if not is_user_admin_for_region(user, region_to_change):
            return 'Permission denied', 403

        tournament = dao.get_tournament_by_id(ObjectId(id))
        if region_to_change in tournament.regions:
            tournament.regions.remove(region_to_change)
            dao.update_tournament(tournament)

        return convert_tournament_to_response(dao.get_tournament_by_id(tournament.id), dao)

class RankingsResource(restful.Resource):
    def get(self, region):
        dao = Dao(region, mongo_client=mongo_client)
        args = rankings_get_parser.parse_args()

        if args['generateNew'] is not None and args['generateNew'] == 'true':
            rankings.generate_ranking(dao)

        return_dict = dao.get_latest_ranking().get_json_dict()
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

class MatchesResource(restful.Resource):
    def get(self, region, id):
        dao = Dao(region, mongo_client=mongo_client)
        args = matches_get_parser.parse_args()
        return_dict = {}

        player = dao.get_player_by_id(ObjectId(id))
        return_dict['player'] = {'id': str(player.id), 'name': player.name}
        player_list = [player]

        opponent_id = args['opponent']
        if opponent_id is not None:
            opponent = dao.get_player_by_id(ObjectId(args['opponent']))
            return_dict['opponent'] = {'id': str(opponent.id), 'name': opponent.name}
            player_list.append(opponent)

        match_list = []
        return_dict['matches'] = match_list
        return_dict['wins'] = 0
        return_dict['losses'] = 0

        tournaments = dao.get_all_tournaments(players=player_list)
        for tournament in tournaments:
            for match in tournament.matches:
                if (opponent_id is not None and match.contains_players(player.id, opponent.id)) or \
                        (opponent_id is None and match.contains_player(player.id)):
                    match_dict = {}
                    match_dict['tournament_id'] = str(tournament.id)
                    match_dict['tournament_name'] = tournament.name
                    match_dict['tournament_date'] = tournament.date.strftime("%x")
                    match_dict['opponent_id'] = str(match.get_opposing_player_id(player.id))
                    match_dict['opponent_name'] = dao.get_player_by_id(ObjectId(match_dict['opponent_id'])).name

                    if match.did_player_win(player.id):
                        match_dict['result'] = 'win'
                        return_dict['wins'] += 1
                    else:
                        match_dict['result'] = 'lose'
                        return_dict['losses'] += 1

                    match_list.append(match_dict)

        return return_dict

class CurrentUserResource(restful.Resource):
    def get(self):
        # TODO region doesn't matter, remove hardcode
        dao = Dao('norcal', mongo_client=mongo_client)
        user = get_user_from_access_token(request.headers, dao)
        return_dict = user.get_json_dict()

        return_dict['id'] = return_dict['_id']
        del return_dict['_id']

        return return_dict

api.add_resource(RegionListResource, '/regions')

api.add_resource(PlayerListResource, '/<string:region>/players')
api.add_resource(PlayerResource, '/<string:region>/players/<string:id>')
api.add_resource(PlayerRegionResource, '/<string:region>/players/<string:id>/region/<string:region_to_change>')

api.add_resource(MatchesResource, '/<string:region>/matches/<string:id>')

api.add_resource(TournamentListResource, '/<string:region>/tournaments')
api.add_resource(TournamentResource, '/<string:region>/tournaments/<string:id>')
api.add_resource(TournamentRegionResource, '/<string:region>/tournaments/<string:id>/region/<string:region_to_change>')

api.add_resource(RankingsResource, '/<string:region>/rankings')

api.add_resource(CurrentUserResource, '/users/me')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(sys.argv[1]), debug=(sys.argv[2] == 'True'))

