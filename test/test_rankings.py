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
        self.region_id = 'norcal'
        self.region = Region(id=self.region_id,
                             display_name='Norcal')

        self.mongo_client = mongomock.MongoClient()
        Dao.insert_region(self.region, self.mongo_client)

        self.dao = Dao(self.region_id, mongo_client=self.mongo_client)

        self.player_1_id = ObjectId()
        self.player_2_id = ObjectId()
        self.player_3_id = ObjectId()
        self.player_4_id = ObjectId()
        self.player_5_id = ObjectId()
        self.player_1 = Player(
                name='gaR',
                aliases=['gar', 'garr'],
                ratings={'norcal': Rating(), 'texas': Rating()},
                regions=['norcal', 'texas'],
                id=self.player_1_id)
        self.player_2 = Player(
                name='sfat',
                aliases=['sfat', 'miom | sfat'],
                ratings={'norcal': Rating()},
                regions=['norcal'],
                id=self.player_2_id)
        self.player_3 = Player(
                name='mango',
                aliases=['mango'],
                ratings={'norcal': Rating(mu=2, sigma=3)},
                regions=['socal'],
                id=self.player_3_id)
        self.player_4 = Player(
                name='shroomed',
                aliases=['shroomed'],
                ratings={'norcal': Rating()},
                regions=['norcal'],
                id=self.player_4_id)
        self.player_5 = Player(
                name='pewpewu',
                aliases=['pewpewu'],
                ratings={'norcal': Rating()},
                regions=['norcal'],
                id=self.player_5_id)

        self.players = [self.player_1, self.player_2, self.player_3, self.player_4, self.player_5]

        self.tournament_id_1 = ObjectId()
        self.tournament_type_1 = 'tio'
        self.tournament_raw_1 = 'raw1'
        self.tournament_date_1 = datetime(2013, 10, 16)
        self.tournament_name_1 = 'tournament 1'
        self.tournament_players_1 = [self.player_1_id, self.player_2_id, self.player_3_id, self.player_4_id]
        self.tournament_matches_1 = [
                Match(winner=self.player_1_id, loser=self.player_2_id),
                Match(winner=self.player_3_id, loser=self.player_4_id)
        ]
        self.tournament_regions_1 = ['norcal']

        # tournament 2 is earlier than tournament 1, but inserted after
        self.tournament_id_2 = ObjectId()
        self.tournament_type_2 = 'challonge'
        self.tournament_raw_2 = 'raw2'
        self.tournament_date_2 = datetime(2013, 10, 10)
        self.tournament_name_2 = 'tournament 2'
        self.tournament_players_2 = [self.player_5_id, self.player_2_id, self.player_3_id, self.player_4_id]
        self.tournament_matches_2 = [
                Match(winner=self.player_5_id, loser=self.player_2_id),
                Match(winner=self.player_3_id, loser=self.player_4_id)
        ]
        self.tournament_regions_2 = ['norcal', 'texas']

        self.tournament_1 = Tournament(
                    type=self.tournament_type_1,
                    raw=self.tournament_raw_1,
                    date=self.tournament_date_1,
                    name=self.tournament_name_1,
                    players=self.tournament_players_1,
                    matches=self.tournament_matches_1,
                    regions=self.tournament_regions_1,
                    id=self.tournament_id_1)

        self.tournament_2 = Tournament(
                    type=self.tournament_type_2,
                    raw=self.tournament_raw_2,
                    date=self.tournament_date_2,
                    name=self.tournament_name_2,
                    players=self.tournament_players_2,
                    matches=self.tournament_matches_2,
                    regions=self.tournament_regions_2,
                    id=self.tournament_id_2)

        self.tournament_ids = [self.tournament_id_1, self.tournament_id_2]
        self.tournaments = [self.tournament_1, self.tournament_2]

        for player in self.players:
            self.dao.insert_player(player)

        for tournament in self.tournaments:
            self.dao.insert_tournament(tournament)

    # all tournaments are within the active range and will be included
    def test_generate_rankings(self):
        now = datetime(2013, 10, 17)

        # assert rankings before they get reset
        self.assertEquals(self.dao.get_player_by_id(self.player_1_id).ratings, self.player_1.ratings)
        self.assertEquals(self.dao.get_player_by_id(self.player_2_id).ratings, self.player_2.ratings)
        self.assertEquals(self.dao.get_player_by_id(self.player_3_id).ratings, self.player_3.ratings)
        self.assertEquals(self.dao.get_player_by_id(self.player_4_id).ratings, self.player_4.ratings)
        self.assertEquals(self.dao.get_player_by_id(self.player_5_id).ratings, self.player_5.ratings)

        rankings.generate_ranking(self.dao, now=now, day_limit=30, num_tourneys=1)

        # assert rankings after ranking calculation
        self.assertAlmostEquals(self.dao.get_player_by_id(self.player_1_id).ratings['norcal'].mu,
                                28.458, delta=delta)
        self.assertAlmostEquals(self.dao.get_player_by_id(self.player_1_id).ratings['norcal'].sigma,
                                7.201, delta=delta)
        self.assertAlmostEquals(self.dao.get_player_by_id(self.player_2_id).ratings['norcal'].mu,
                                18.043, delta=delta)
        self.assertAlmostEquals(self.dao.get_player_by_id(self.player_2_id).ratings['norcal'].sigma,
                                6.464, delta=delta)
        self.assertAlmostEquals(self.dao.get_player_by_id(self.player_3_id).ratings['norcal'].mu,
                                31.230, delta=delta)
        self.assertAlmostEquals(self.dao.get_player_by_id(self.player_3_id).ratings['norcal'].sigma,
                                6.523, delta=delta)
        self.assertAlmostEquals(self.dao.get_player_by_id(self.player_4_id).ratings['norcal'].mu,
                                18.770, delta=delta)
        self.assertAlmostEquals(self.dao.get_player_by_id(self.player_4_id).ratings['norcal'].sigma,
                                6.523, delta=delta)
        self.assertAlmostEquals(self.dao.get_player_by_id(self.player_5_id).ratings['norcal'].mu,
                                29.396, delta=delta)
        self.assertAlmostEquals(self.dao.get_player_by_id(self.player_5_id).ratings['norcal'].sigma,
                                7.171, delta=delta)

        # player 1's rating for other regions should not have changed
        self.assertAlmostEquals(self.dao.get_player_by_id(self.player_1_id).ratings['texas'].mu,
                                25, delta=delta)
        self.assertAlmostEquals(self.dao.get_player_by_id(self.player_1_id).ratings['texas'].sigma,
                                8.333, delta=delta)

        ranking = self.dao.get_latest_ranking()
        self.assertEquals(ranking.region, self.region_id)
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
    def test_generate_rankings_excluded_for_inactivity(self):
        now = datetime(2013, 11, 25)

        rankings.generate_ranking(self.dao, now=now, day_limit=45, num_tourneys=1)

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
        self.assertAlmostEquals(entry.rating, -.800, delta=delta, msg="" + str(entry.player))

        entry = ranking_list[2]
        self.assertEquals(entry.rank, 3)
        self.assertEquals(entry.player, self.player_2_id)
        self.assertAlmostEquals(entry.rating, -1.349, delta=delta)

    def test_generate_rankings_diff_against_tournament(self):
        now = datetime(2013, 11, 25)

        rankings.generate_ranking(self.dao, now=now, day_limit=45, num_tourneys=1, tournament_to_diff=self.tournament_2)

        ranking = self.dao.get_latest_ranking()

        ranking_list = ranking.ranking
        self.assertEquals(len(ranking_list), 3)

        entry = ranking_list[0]
        self.assertEquals(entry.rank, 1)
        self.assertEquals(entry.player, self.player_1_id)
        self.assertAlmostEquals(entry.rating, 6.857, delta=delta)
        self.assertEquals(entry.previous_rank, None)

        entry = ranking_list[1]
        self.assertEquals(entry.rank, 2)
        self.assertEquals(entry.player, self.player_4_id)
        self.assertAlmostEquals(entry.rating, -.800, delta=delta, msg="" + str(entry.player))
        self.assertEquals(entry.previous_rank, 2)

        entry = ranking_list[2]
        self.assertEquals(entry.rank, 3)
        self.assertEquals(entry.player, self.player_2_id)
        self.assertAlmostEquals(entry.rating, -1.349, delta=delta)
        self.assertEquals(entry.previous_rank, 3)
