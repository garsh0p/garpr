from flask import Flask
from flask.ext import restful
from dao import Dao
from bson.json_util import dumps

app = Flask(__name__)
api = restful.Api(app)

def convert_object_id(json_dict):
    json_dict['_id'] = str(json_dict['_id'])

def convert_object_id_list(json_dict_list):
    for j in json_dict_list:
        convert_object_id(j)

class PlayersResource(restful.Resource):
    def get(self, region):
        dao = Dao(region)
        return_dict = {}
        return_dict['players'] = [p.get_json_dict() for p in dao.get_all_players()]
        convert_object_id_list(return_dict['players'])
        return return_dict

class TournamentsResource(restful.Resource):
    def get(self, region):
        dao = Dao(region)
        return_dict = {}
        return_dict['tournaments'] = [t.get_json_dict() for t in dao.get_all_tournaments()]
        convert_object_id_list(return_dict['tournaments'])

        # remove all raw file dumps and convert datetimes to string
        for t in return_dict['tournaments']:
            del t['raw']
            t['date'] = str(t['date'])

        return return_dict

class RankingsResource(restful.Resource):
    def get(self, region):
        dao = Dao(region)

        return_dict = dao.get_latest_ranking().get_json_dict()
        del return_dict['_id']
        return_dict['time'] = str(return_dict['time'])
        return_dict['tournaments'] = [str(t) for t in return_dict['tournaments']]

        return return_dict

api.add_resource(PlayersResource, '/<string:region>/players')
api.add_resource(TournamentsResource, '/<string:region>/tournaments')
api.add_resource(RankingsResource, '/<string:region>/rankings')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5100, debug=True)

