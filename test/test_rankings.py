import unittest
import mongomock
from dao import Dao
from bson.objectid import ObjectId
from model import *
from datetime import datetime
import rankings
from mock import patch

delta = .001

class TestRankings(unittest.TestCase):
    def setUp(self):
        self.region = 'test'
        self.mongo_client = mongomock.MongoClient()
        self.dao = Dao(self.region, mongo_client=self.mongo_client, new=True)

        self.player_1_id = ObjectId()
        self.player_2_id = ObjectId()
        self.player_3_id = ObjectId()
        self.player_4_id = ObjectId()
        self.player_5_id = ObjectId()
        self.player_1 = Player('gaR', ['gar', 'garr'], TrueskillRating(), False, id=self.player_1_id)
        self.player_2 = Player('sfat', ['sfat', 'miom | sfat'], TrueskillRating(), False, id=self.player_2_id)
        self.player_3 = Player('mango', ['mango'], 
                               TrueskillRating(trueskill_rating=trueskill.Rating(mu=2, sigma=3)), 
                               True, id=self.player_3_id)
        self.player_4 = Player('shroomed', ['shroomed'], TrueskillRating(), False, id=self.player_4_id)
        self.player_5 = Player('pewpewu', ['pewpewu'], TrueskillRating(), False, id=self.player_5_id)

        self.players = [self.player_1, self.player_2, self.player_3, self.player_4, self.player_5]

        self.tournament_id_1 = ObjectId()
        self.tournament_type_1 = 'tio'
        self.tournament_raw_1 = 'raw1'
        self.tournament_date_1 = datetime(2013, 10, 16)
        self.tournament_name_1 = 'tournament 1'
        self.tournament_players_1 = [self.player_1_id, self.player_2_id, self.player_3_id, self.player_4_id]
        self.tournament_matches_1 = [
                MatchResult(winner=self.player_1_id, loser=self.player_2_id),
                MatchResult(winner=self.player_3_id, loser=self.player_4_id)
        ]

        # tournament 2 is earlier than tournament 1, but inserted after
        self.tournament_id_2 = ObjectId()
        self.tournament_type_2 = 'challonge'
        self.tournament_raw_2 = 'raw2'
        self.tournament_date_2 = datetime(2013, 10, 10)
        self.tournament_name_2 = 'tournament 2'
        self.tournament_players_2 = [self.player_5_id, self.player_2_id, self.player_3_id, self.player_4_id]
        self.tournament_matches_2 = [
                MatchResult(winner=self.player_5_id, loser=self.player_2_id),
                MatchResult(winner=self.player_3_id, loser=self.player_4_id)
        ]

        self.tournament_1 = Tournament(self.tournament_type_1,
                                       self.tournament_raw_1,
                                       self.tournament_date_1, 
                                       self.tournament_name_1,
                                       self.tournament_players_1,
                                       self.tournament_matches_1,
                                       id=self.tournament_id_1)

        self.tournament_2 = Tournament(self.tournament_type_2,
                                       self.tournament_raw_2,
                                       self.tournament_date_2, 
                                       self.tournament_name_2,
                                       self.tournament_players_2,
                                       self.tournament_matches_2,
                                       id=self.tournament_id_2)

        self.tournament_ids = [self.tournament_id_1, self.tournament_id_2]
        self.tournaments = [self.tournament_1, self.tournament_2]

        for player in self.players:
            self.dao.add_player(player)

        for tournament in self.tournaments:
            self.dao.insert_tournament(tournament)

    # all tournaments are within the active range and will be included
    @patch('rankings.datetime', spec=True)
    def test_generate_rankings(self, mock_datetime):
        now = datetime(2013, 10, 17)
        mock_datetime.now.return_value = now

        # assert rankings before they get reset
        self.assertEquals(self.dao.get_player_by_id(self.player_1_id).rating, self.player_1.rating)
        self.assertEquals(self.dao.get_player_by_id(self.player_2_id).rating, self.player_2.rating)
        self.assertEquals(self.dao.get_player_by_id(self.player_3_id).rating, self.player_3.rating)
        self.assertEquals(self.dao.get_player_by_id(self.player_4_id).rating, self.player_4.rating)
        self.assertEquals(self.dao.get_player_by_id(self.player_5_id).rating, self.player_5.rating)

        rankings.generate_ranking(self.dao)

        # assert rankings after ranking calculation
        self.assertAlmostEquals(self.dao.get_player_by_id(self.player_1_id).rating.trueskill_rating.mu, 
                                28.458, delta=delta)
        self.assertAlmostEquals(self.dao.get_player_by_id(self.player_1_id).rating.trueskill_rating.sigma, 
                                7.201, delta=delta)
        self.assertAlmostEquals(self.dao.get_player_by_id(self.player_2_id).rating.trueskill_rating.mu, 
                                18.043, delta=delta)
        self.assertAlmostEquals(self.dao.get_player_by_id(self.player_2_id).rating.trueskill_rating.sigma, 
                                6.464, delta=delta)
        self.assertAlmostEquals(self.dao.get_player_by_id(self.player_3_id).rating.trueskill_rating.mu, 
                                31.230, delta=delta)
        self.assertAlmostEquals(self.dao.get_player_by_id(self.player_3_id).rating.trueskill_rating.sigma, 
                                6.523, delta=delta)
        self.assertAlmostEquals(self.dao.get_player_by_id(self.player_4_id).rating.trueskill_rating.mu, 
                                18.770, delta=delta)
        self.assertAlmostEquals(self.dao.get_player_by_id(self.player_4_id).rating.trueskill_rating.sigma, 
                                6.523, delta=delta)
        self.assertAlmostEquals(self.dao.get_player_by_id(self.player_5_id).rating.trueskill_rating.mu, 
                                29.396, delta=delta)
        self.assertAlmostEquals(self.dao.get_player_by_id(self.player_5_id).rating.trueskill_rating.sigma, 
                                7.171, delta=delta)

        ranking = self.dao.get_latest_ranking()
        self.assertEquals(ranking.time, now)
        self.assertEquals(set(ranking.tournaments), set(self.tournament_ids))

        ranking_list = ranking.ranking
        
        # the ranking should not have any excluded players
        self.assertEquals(len(ranking_list), 4)
        
        entry = ranking_list[0]
        self.assertEquals(entry.rank, 1)
        self.assertEquals(entry.player, self.player_5_id)
        self.assertAlmostEquals(entry.rating, 7.881, delta=delta)

        entry = ranking_list[1]
        self.assertEquals(entry.rank, 2)
        self.assertEquals(entry.player, self.player_1_id)
        self.assertAlmostEquals(entry.rating, 6.857, delta=delta)

        entry = ranking_list[2]
        self.assertEquals(entry.rank, 3)
        self.assertEquals(entry.player, self.player_4_id)
        self.assertAlmostEquals(entry.rating, -.800, delta=delta)

        entry = ranking_list[3]
        self.assertEquals(entry.rank, 4)
        self.assertEquals(entry.player, self.player_2_id)
        self.assertAlmostEquals(entry.rating, -1.349, delta=delta)

    # players that only played in the first tournament will be excluded for inactivity
    @patch('rankings.datetime', spec=True)
    def test_generate_rankings_excluded_for_inactivity(self, mock_datetime):
        now = datetime(2013, 11, 25)
        mock_datetime.now.return_value = now

        rankings.generate_ranking(self.dao)

        ranking = self.dao.get_latest_ranking()

        ranking_list = ranking.ranking
        self.assertEquals(len(ranking_list), 3)

        entry = ranking_list[0]
        self.assertEquals(entry.rank, 1)
        self.assertEquals(entry.player, self.player_1_id)
        self.assertAlmostEquals(entry.rating, 6.857, delta=delta)

        entry = ranking_list[1]
        self.assertEquals(entry.rank, 2)
        self.assertEquals(entry.player, self.player_4_id)
        self.assertAlmostEquals(entry.rating, -.800, delta=delta)

        entry = ranking_list[2]
        self.assertEquals(entry.rank, 3)
        self.assertEquals(entry.player, self.player_2_id)
        self.assertAlmostEquals(entry.rating, -1.349, delta=delta)
