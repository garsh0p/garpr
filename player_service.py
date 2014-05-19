from flask import Flask
from flask.ext.restful import Api, Resource, reqparse
from pymongo import MongoClient
from bson.objectid import ObjectId

mongo_client = MongoClient('localhost')
col = mongo_client.players.players

app = Flask(__name__)
api = Api(app)

#parser = reqparse.RequestParser()
#parser.add_argument()

def convert_player_id(player):
    player['id'] = str(player['_id'])
    del player['_id']
    return player

class PlayerList(Resource):
    def get(self):
        players = [player for player in col.find()]
        for player in players:
            convert_player_id(player)
        return players

    def post(self):
        return {}

class Player(Resource):
    def get(self, player_id):
        return convert_player_id(col.find_one({'_id': ObjectId(player_id)}))

    def post(self):

api.add_resource(Player, '/<string:player_id>')
api.add_resource(PlayerList, '/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
