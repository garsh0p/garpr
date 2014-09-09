from flask import Flask
from flask.ext import restful
from flask.ext.restful import reqparse
from dao import Dao
from bson.json_util import dumps
from bson.objectid import ObjectId
import sys

app = Flask(__name__)
api = restful.Api(app)

matches_get_parser = reqparse.RequestParser()
matches_get_parser.add_argument('player', type=str)
matches_get_parser.add_argument('opponent', type=str)

def convert_object_id(json_dict):
    json_dict['_id'] = str(json_dict['_id'])

def convert_object_id_list(json_dict_list):
    for j in json_dict_list:
        convert_object_id(j)

class PlayerListResource(restful.Resource):
    def get(self, region):
        dao = Dao(region)
        return_dict = {}
        return_dict['players'] = [p.get_json_dict() for p in dao.get_all_players()]
        convert_object_id_list(return_dict['players'])

        # remove extra fields
        for player in return_dict['players']:
            del player['exclude']
            del player['aliases']
            del player['rating']

        return return_dict

class PlayerResource(restful.Resource):
    def get(self, region, id):
        dao = Dao(region)
        player = dao.get_player_by_id(ObjectId(id))

        return_dict = player.get_json_dict()
        convert_object_id(return_dict)

        return return_dict

class TournamentListResource(restful.Resource):
    def get(self, region):
        dao = Dao(region)
        return_dict = {}
        return_dict['tournaments'] = [t.get_json_dict() for t in dao.get_all_tournaments()]
        convert_object_id_list(return_dict['tournaments'])

        for t in return_dict['tournaments']:
            t['date'] = str(t['date'])

            # remove extra fields
            del t['raw']
            del t['matches']
            del t['players']
            del t['type']

        return return_dict

class TournamentResource(restful.Resource):
    def get(self, region, id):
        dao = Dao(region)
        tournament = dao.get_tournament_by_id(ObjectId(id))

        return_dict = tournament.get_json_dict()
        convert_object_id(return_dict)

        return_dict['date'] = str(return_dict['date'])

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

class RankingsResource(restful.Resource):
    def get(self, region):
        dao = Dao(region)

        return_dict = dao.get_latest_ranking().get_json_dict()
        del return_dict['_id']
        return_dict['time'] = str(return_dict['time'])
        return_dict['tournaments'] = [str(t) for t in return_dict['tournaments']]

        for r in return_dict['ranking']:
            r['name'] = dao.get_player_by_id(r['player']).name
            r['player'] = str(r['player'])

        return return_dict

class MatchesResource(restful.Resource):
    def get(self, region):
        dao = Dao(region)
        args = matches_get_parser.parse_args()
        return_dict = {}

        player = dao.get_player_by_id(ObjectId(args['player']))
        return_dict['player'] = {'id': str(player.id), 'name': player.name}
        player_list = [player]

        opponent_id = args['opponent']
        if opponent_id is not None:
            opponent = dao.get_player_by_id(ObjectId(args['opponent']))
            return_dict['opponent'] = {'id': str(opponent.id), 'name': opponent.name}
            player_list.append(opponent)

        match_list = []
        return_dict['matches'] = match_list

        tournaments = dao.get_all_tournaments(players=player_list)
        for tournament in tournaments:
            for match in tournament.matches:
                if (opponent_id is not None and match.contains_players(player.id, opponent.id)) or \
                        (opponent_id is None and match.contains_player(player.id)):
                    match_dict = {}
                    match_dict['tournament_id'] = str(tournament.id)
                    match_dict['tournament_name'] = tournament.name
                    match_dict['tournament_date'] = tournament.date.strftime("%x")
                    match_dict['result'] = 'win' if match.did_player_win(player.id) else 'lose'
                    match_list.append(match_dict)

                # if we're looking up all matches for a player, we need to add the opponent's info to each match
                if opponent_id is None and match.contains_player(player.id):
                    match_dict['opponent_id'] = str(match.get_opposing_player_id(player.id))
                    match_dict['opponent_name'] = dao.get_player_by_id(ObjectId(match_dict['opponent_id'])).name

        return return_dict

api.add_resource(PlayerListResource, '/<string:region>/players')
api.add_resource(PlayerResource, '/<string:region>/players/<string:id>')
api.add_resource(TournamentListResource, '/<string:region>/tournaments')
api.add_resource(TournamentResource, '/<string:region>/tournaments/<string:id>')
api.add_resource(RankingsResource, '/<string:region>/rankings')
api.add_resource(MatchesResource, '/<string:region>/matches')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(sys.argv[1]), debug=(sys.argv[2] == 'True'))

