import mock
import unittest
import trueskill

from bson.objectid import ObjectId
from datetime import datetime

from model import AliasMapping, AliasMatch, Match, Player, PendingTournament, \
                 Ranking, RankingEntry, Rating, Region, Tournament, User

from scraper.challonge import ChallongeScraper


class TestRating(unittest.TestCase):

    def setUp(self):
        self.default_rating_a = Rating()
        self.default_rating_b = Rating()
        self.custom_rating = Rating(mu=2., sigma=3.)

        self.default_rating_a_json_dict = {
            'mu': self.default_rating_a.mu,
            'sigma': self.default_rating_a.sigma,
        }

    def test_trueskill_rating(self):
        self.assertEqual(trueskill.Rating(mu=2., sigma=3.),
                         self.custom_rating.trueskill_rating())

    def test_from_trueskill(self):
        self.assertEqual(Rating.from_trueskill(trueskill.Rating(mu=2., sigma=3.)),
                         self.custom_rating)
        self.assertEqual(Rating.from_trueskill(trueskill.Rating()),
                         self.default_rating_a)

    def test_dump(self):
        self.assertEqual(self.default_rating_a.dump(),
                         self.default_rating_a_json_dict)

    def test_load(self):
        self.assertEqual(Rating.load(self.default_rating_a_json_dict),
                         self.default_rating_a)


class TestMatch(unittest.TestCase):

    def setUp(self):
        self.winner = ObjectId()
        self.loser = ObjectId()
        self.other_player = ObjectId()

        self.match_id = 1
        self.match_id2 = 2
        self.excluded1 = False
        self.excluded2 = True

        self.match_result = Match(match_id=self.match_id, winner=self.winner,
                                  loser=self.loser, excluded=self.excluded1)
        self.other_match_result = Match(
            match_id=self.match_id2,
            winner=self.winner,
            loser=self.other_player,
            excluded=self.excluded2)

        self.match_result_json_dict = {
            'match_id': self.match_id,
            'winner': self.winner,
            'loser': self.loser,
            'excluded': self.excluded1
        }

    def test_contains_players(self):
        self.assertTrue(self.match_result.contains_players(
            self.winner, self.loser))
        self.assertTrue(self.match_result.contains_players(
            self.loser, self.winner))

        self.assertFalse(self.match_result.contains_players(
            self.loser, self.loser))
        self.assertFalse(self.match_result.contains_players(
            self.loser, self.other_player))

    def test_did_player_win(self):
        self.assertTrue(self.match_result.did_player_win(self.winner))
        self.assertFalse(self.match_result.did_player_win(self.loser))

    def test_get_opposing_player_id(self):
        self.assertEqual(self.match_result.get_opposing_player_id(
            self.winner), self.loser)
        self.assertEqual(self.match_result.get_opposing_player_id(
            self.loser), self.winner)
        self.assertIsNone(
            self.match_result.get_opposing_player_id(self.other_player))

    def test_dump(self):
        self.assertEqual(self.match_result.dump(
            context='db'), self.match_result_json_dict)

    def test_load(self):
        self.assertEqual(self.match_result, Match.load(
            self.match_result_json_dict, context='web'))

    def test_match_exclusion(self):
        pass

class TestPlayer(unittest.TestCase):

    def setUp(self):
        self.player_1_id = ObjectId()
        self.player_1_name = 'gaR'
        self.player_1_aliases = ['gar', 'garr', 'garpr']
        self.player_1_rating = {
            'norcal': Rating(),
            'texas': Rating(mu=10., sigma=1.)
        }
        self.player_1_regions = ['norcal', 'texas']

        self.player_2_id = ObjectId()
        self.player_2_name = 'MIOM | SFAT'
        self.player_2_aliases = ['miom | sfat', 'sfat', 'miom|sfat']
        self.player_2_rating = {'norcal': Rating(mu=30., sigma=2.)}
        self.player_2_regions = ['norcal', 'socal']

        self.player_1 = Player(name=self.player_1_name,
                               aliases=self.player_1_aliases,
                               ratings=self.player_1_rating,
                               regions=self.player_1_regions,
                               id=self.player_1_id)
        self.player_1_missing_id = Player(name=self.player_1_name,
                                          aliases=self.player_1_aliases,
                                          ratings=self.player_1_rating,
                                          regions=self.player_1_regions)
        self.player_2 = Player(name=self.player_2_name,
                               aliases=self.player_2_aliases,
                               ratings=self.player_2_rating,
                               regions=self.player_2_regions,
                               id=self.player_2_id)

        self.player_1_json_dict = {
            '_id': self.player_1_id,
            'name': self.player_1_name,
            'aliases': self.player_1_aliases,
            'ratings': {region: rating.dump() for region, rating in self.player_1_rating.iteritems()},
            'regions': self.player_1_regions,
            'merge_children': [self.player_1_id],
            'merge_parent': None,
            'merged': False,
        }

        self.player_1_json_dict_missing_id = {
            'name': self.player_1_name,
            'aliases': self.player_1_aliases,
            'ratings': {region: rating.dump() for region, rating in self.player_1_rating.iteritems()},
            'regions': self.player_1_regions,
            'merge_children': [None],
            'merge_parent': None,
            'merged': False,
        }

    def test_create_with_default_values(self):
        name = 'ASDF'
        region = 'r'

        player = Player.create_with_default_values(name, region)
        self.assertEqual(player.name, name)
        self.assertEqual(player.aliases, ['asdf'])
        self.assertEqual(player.ratings, {})
        self.assertEqual(player.regions, [region])

    def test_dump(self):
        self.assertEqual(self.player_1.dump(
            context='db'), self.player_1_json_dict)

    def test_load(self):
        self.assertEqual(self.player_1, Player.load(
            self.player_1_json_dict, context='db'))


class TestTournament(unittest.TestCase):

    def setUp(self):
        self.player_1_id = ObjectId()
        self.player_2_id = ObjectId()
        self.player_3_id = ObjectId()
        self.player_4_id = ObjectId()
        self.player_5_id = ObjectId()
        self.player_6_id = ObjectId()
        self.player_1 = Player(name='gar', id=self.player_1_id)
        self.player_2 = Player(name='sfat', id=self.player_2_id)
        self.player_3 = Player(name='shroomed', id=self.player_3_id)
        self.player_4 = Player(name='ppu', id=self.player_4_id)
        self.player_5 = Player(name='ss', id=self.player_5_id)
        self.player_6 = Player(name='hmw', id=self.player_6_id)
        self.match_1 = Match(winner=self.player_1_id, loser=self.player_2_id, match_id=1)
        self.match_2 = Match(winner=self.player_3_id, loser=self.player_4_id, match_id=2)

        self.alias_to_id_map = [
            AliasMapping(player_alias=self.player_2.name,
                         player_id=self.player_2_id),
            AliasMapping(player_alias=self.player_1.name,
                         player_id=self.player_1_id),
            AliasMapping(player_alias=self.player_3.name,
                         player_id=self.player_3_id),
            AliasMapping(player_alias=self.player_4.name,
                         player_id=self.player_4_id)
        ]

        self.id = ObjectId()
        self.type = 'tio'
        self.raw_id = ObjectId()
        self.date = datetime.now()
        self.name = 'tournament'
        self.url = "challonge.com/tournament"
        self.player_ids = [self.player_1_id, self.player_2_id,
                           self.player_3_id, self.player_4_id]
        self.players = [self.player_1, self.player_2,
                        self.player_3, self.player_4]
        self.matches = [self.match_1, self.match_2]
        self.regions = ['norcal', 'texas']

        self.tournament_json_dict = {
            '_id': self.id,
            'type': self.type,
            'raw_id': self.raw_id,
            'date': self.date,
            'name': self.name,
            'url': self.url,
            'players': self.player_ids,
            'orig_ids': self.player_ids,
            'matches': [m.dump(context='db') for m in self.matches],
            'regions': self.regions
        }
        self.tournament = Tournament(
            id=self.id,
            name=self.name,
            type=self.type,
            date=self.date,
            regions=self.regions,
            url=self.url,
            raw_id=self.raw_id,
            players=self.player_ids,
            orig_ids=self.player_ids,
            matches=self.matches)

    def test_replace_player(self):
        self.assertTrue(self.player_3_id in self.tournament.players)
        self.assertTrue(self.tournament.matches[
                        1].contains_player(self.player_3_id))

        self.assertFalse(self.player_5_id in self.tournament.players)
        for match in self.tournament.matches:
            self.assertFalse(match.contains_player(self.player_5_id))

        self.assertEqual(len(self.tournament.players), 4)

        self.tournament.replace_player(
            player_to_remove=self.player_3, player_to_add=self.player_5)

        self.assertFalse(self.player_3_id in self.tournament.players)
        for match in self.tournament.matches:
            self.assertFalse(match.contains_player(self.player_3_id))

        self.assertTrue(self.player_5_id in self.tournament.players)
        self.assertTrue(self.tournament.matches[
                        1].contains_player(self.player_5_id))

        self.assertEqual(len(self.tournament.players), 4)

    def test_replace_player_none(self):
        with self.assertRaises(TypeError):
            self.tournament.replace_player(player_to_add=self.player_1)

        with self.assertRaises(TypeError):
            self.tournament.replace_player(player_to_remove=self.player_1)

    def test_replace_player_invalid_player_to_remove(self):
        self.assertTrue(self.player_1_id in self.tournament.players)
        self.assertTrue(self.player_2_id in self.tournament.players)
        self.assertTrue(self.player_3_id in self.tournament.players)
        self.assertTrue(self.player_4_id in self.tournament.players)
        self.assertEqual(len(self.tournament.players), 4)

        self.tournament.replace_player(
            player_to_remove=self.player_5, player_to_add=self.player_6)

        self.assertTrue(self.player_1_id in self.tournament.players)
        self.assertTrue(self.player_2_id in self.tournament.players)
        self.assertTrue(self.player_3_id in self.tournament.players)
        self.assertTrue(self.player_4_id in self.tournament.players)
        self.assertEqual(len(self.tournament.players), 4)

    def test_contains_player(self):
        self.assertTrue(self.tournament.contains_player(self.player_1))
        self.assertTrue(self.tournament.contains_player(self.player_2))
        self.assertTrue(self.tournament.contains_player(self.player_3))
        self.assertTrue(self.tournament.contains_player(self.player_4))

    def test_does_not_contain_player(self):
        self.assertFalse(self.tournament.contains_player(self.player_5))

    def test_dump(self):
        self.assertEqual(self.tournament.dump(
            context='db'), self.tournament_json_dict)

    def test_load(self):
        tournament = Tournament.load(self.tournament_json_dict, context='db')
        self.assertEqual(tournament.id, self.id)
        self.assertEqual(tournament.type, self.type)
        self.assertEqual(tournament.raw_id, self.raw_id)
        self.assertEqual(tournament.date, self.date)
        self.assertEqual(tournament.name, self.name)
        self.assertEqual(tournament.matches, self.matches)
        self.assertEqual(tournament.players, self.player_ids)
        self.assertEqual(tournament.regions, self.regions)

    def test_validate_document(self):
        result, msg = self.tournament.validate_document()
        self.assertTrue(result)

    def test_validate_document_duplicate_players(self):
        self.tournament.players = [
            self.player_1_id, self.player_2_id,
            self.player_3_id, self.player_3_id]
        result, msg = self.tournament.validate_document()
        self.assertFalse(result)

    def test_from_pending_tournament(self):
        # we need MatchResults with aliases (instead of IDs)
        match_1 = AliasMatch(winner=self.player_1.name,
                             loser=self.player_2.name)
        match_2 = AliasMatch(winner=self.player_3.name,
                             loser=self.player_4.name)

        player_aliases = [p.name for p in self.players]
        matches = [match_1, match_2]
        pending_tournament = PendingTournament(
            name=self.name,
            type=self.type,
            date=self.date,
            raw_id=self.raw_id,
            regions=['norcal'],
            players=player_aliases,
            matches=matches,
            alias_to_id_map=self.alias_to_id_map)

        tournament = Tournament.from_pending_tournament(pending_tournament)

        self.assertIsNone(tournament.id)
        self.assertEqual(tournament.type, self.type)
        self.assertEqual(tournament.raw_id, self.raw_id)
        self.assertEqual(tournament.date, self.date)
        self.assertEqual(tournament.name, self.name)
        self.assertEqual(tournament.matches[0].winner, self.matches[0].winner)
        self.assertEqual(tournament.matches[0].loser, self.matches[0].loser)
        self.assertEqual(tournament.matches[1].winner, self.matches[1].winner)
        self.assertEqual(tournament.matches[1].loser, self.matches[1].loser)
        self.assertEqual(tournament.players, self.player_ids)
        self.assertEqual(tournament.regions, ['norcal'])

    def test_from_pending_tournament_throws_exception(self):
        # we need MatchResults with aliases (instead of IDs)
        match_1 = AliasMatch(winner=self.player_1.name,
                             loser=self.player_2.name)
        match_2 = AliasMatch(winner=self.player_3.name,
                             loser=self.player_4.name)

        player_aliases = [p.name for p in self.players]
        matches = [match_1, match_2]
        alias_to_id_map = [AliasMapping(player_alias=self.player_1.name,
                                        player_id=None)]
        pending_tournament = PendingTournament(
            name=self.name,
            type=self.type,
            date=self.date,
            regions=['norcal'],
            raw_id=self.raw_id,
            players=player_aliases,
            matches=matches,
            alias_to_id_map=alias_to_id_map)

        with self.assertRaises(Exception) as e:
            Tournament.from_pending_tournament(pending_tournament)

        self.assertTrue('Alias gar has no ID in map' in str(e.exception))


class TestPendingTournament(unittest.TestCase):

    def setUp(self):
        self.player_1_id = ObjectId()
        self.player_2_id = ObjectId()
        self.player_3_id = ObjectId()
        self.player_4_id = ObjectId()
        self.player_5_id = ObjectId()
        self.player_6_id = ObjectId()
        self.player_1 = Player(name='gar', id=self.player_1_id)
        self.player_2 = Player(name='sfat', id=self.player_2_id)
        self.player_3 = Player(name='shroomed', id=self.player_3_id)
        self.player_4 = Player(name='ppu', id=self.player_4_id)
        self.player_5 = Player(name='ss', id=self.player_5_id)
        self.player_6 = Player(name='hmw', id=self.player_6_id)
        self.match_1 = Match(winner=self.player_1_id, loser=self.player_2_id)
        self.match_2 = Match(winner=self.player_3_id, loser=self.player_4_id)
        self.match_1 = AliasMatch(
            winner=self.player_1.name, loser=self.player_2.name)
        self.match_2 = AliasMatch(
            winner=self.player_3.name, loser=self.player_4.name)

        self.alias_to_id_map = [
            AliasMapping(player_alias=self.player_1.name,
                         player_id=self.player_1_id),
            AliasMapping(player_alias=self.player_2.name,
                         player_id=self.player_2_id),
            AliasMapping(player_alias=self.player_3.name,
                         player_id=self.player_3_id),
            AliasMapping(player_alias=self.player_4.name,
                         player_id=self.player_4_id)
        ]

        self.id = ObjectId()
        self.type = 'tio'
        self.raw_id = ObjectId()
        self.date = datetime.now()
        self.name = 'tournament'
        self.players = [self.player_1.name, self.player_2.name,
                        self.player_3.name, self.player_4.name]
        self.matches = [self.match_1, self.match_2]
        self.regions = ['norcal', 'texas']
        self.url = 'http://challonge.com/test'

        self.pending_tournament_json_dict = {
            '_id': self.id,
            'type': self.type,
            'raw_id': self.raw_id,
            'date': self.date,
            'name': self.name,
            'players': self.players,
            'matches': [m.dump(context='db') for m in self.matches],
            'regions': self.regions,
            'alias_to_id_map': [am.dump(context='db') for am in self.alias_to_id_map],
            'url': self.url
        }
        self.pending_tournament = PendingTournament(
            id=self.id,
            name=self.name,
            type=self.type,
            date=self.date,
            regions=self.regions,
            url=self.url,
            raw_id=self.raw_id,
            players=self.players,
            matches=self.matches,
            alias_to_id_map=self.alias_to_id_map)

    def test_dump(self):
        self.assertEqual(self.pending_tournament.dump(
            context='db'), self.pending_tournament_json_dict)

    def test_load(self):
        pending_tournament = PendingTournament.load(
            self.pending_tournament_json_dict, context='db')
        self.assertEqual(pending_tournament.id, self.id)
        self.assertEqual(pending_tournament.type, self.type)
        self.assertEqual(pending_tournament.raw_id, self.raw_id)
        self.assertEqual(pending_tournament.date, self.date)
        self.assertEqual(pending_tournament.name, self.name)
        self.assertEqual(pending_tournament.matches, self.matches)
        self.assertEqual(pending_tournament.players, self.players)
        self.assertEqual(pending_tournament.regions, self.regions)
        self.assertEqual(pending_tournament.alias_to_id_map,
                         self.alias_to_id_map)

    def test_set_alias_id_mapping_new(self):
        self.assertEqual(len(self.pending_tournament.alias_to_id_map), 4)

        new_alias = 'new alias'
        new_object_id = ObjectId()
        self.pending_tournament.set_alias_id_mapping(new_alias, new_object_id)

        self.assertEqual(len(self.pending_tournament.alias_to_id_map), 5)
        mapping = self.pending_tournament.alias_to_id_map[4]
        self.assertEqual(mapping.player_alias, new_alias)
        self.assertEqual(mapping.player_id, new_object_id)

    def test_set_alias_id_mapping_existing(self):
        self.assertEqual(len(self.pending_tournament.alias_to_id_map), 4)

        new_object_id = ObjectId()
        self.pending_tournament.set_alias_id_mapping(
            self.player_1.name, new_object_id)

        self.assertEqual(len(self.pending_tournament.alias_to_id_map), 4)
        mapping = self.pending_tournament.alias_to_id_map[0]
        self.assertEqual(mapping.player_alias, self.player_1.name)
        self.assertEqual(mapping.player_id, new_object_id)

    def test_delete_alias_id_mapping(self):
        self.assertEqual(len(self.pending_tournament.alias_to_id_map), 4)
        deleted_mapping = self.pending_tournament.delete_alias_id_mapping(
            self.player_1.name)
        self.assertEqual(len(self.pending_tournament.alias_to_id_map), 3)
        self.assertFalse(
            deleted_mapping in self.pending_tournament.alias_to_id_map)

    def test_from_scraper(self):
        mock_scraper = mock.Mock(spec=ChallongeScraper)

        mock_scraper.get_players.return_value = self.players
        mock_scraper.get_matches.return_value = self.matches
        mock_scraper.get_raw.return_value = ''
        mock_scraper.get_date.return_value = self.date
        mock_scraper.get_name.return_value = self.name
        mock_scraper.get_url.return_value = ''

        pending_tournament, _ = PendingTournament.from_scraper(
            self.type, mock_scraper, 'norcal')

        self.assertEqual(pending_tournament.type, self.type)
        self.assertEqual(pending_tournament.date, self.date)
        self.assertEqual(pending_tournament.name, self.name)
        self.assertEqual(pending_tournament.matches, self.matches)
        self.assertEqual(pending_tournament.players, self.players)
        self.assertEqual(pending_tournament.regions, ['norcal'])


class TestRanking(unittest.TestCase):

    def setUp(self):
        self.ranking_id = ObjectId()
        self.region = 'norcal'
        self.time = datetime.now()
        self.tournaments = [ObjectId(), ObjectId()]
        self.ranking_entry_1 = RankingEntry(
            rank=1,
            player=ObjectId(),
            rating=20.5)
        self.ranking_entry_2 = RankingEntry(
            rank=2,
            player=ObjectId(),
            rating=19.3)
        self.rankings = [self.ranking_entry_1, self.ranking_entry_2]
        self.ranking = Ranking(
            id=self.ranking_id,
            region=self.region,
            time=self.time,
            tournaments=self.tournaments,
            ranking=self.rankings)

        self.ranking_json_dict = {
            '_id': self.ranking_id,
            'region': self.region,
            'time': self.time,
            'tournaments': self.tournaments,
            'ranking': [r.dump(context='db') for r in self.rankings]
        }

    def test_dump(self):
        self.assertEqual(self.ranking.dump(
            context='db'), self.ranking_json_dict)

    def test_load(self):
        ranking = Ranking.load(self.ranking_json_dict, context='db')
        self.assertEqual(ranking.id, self.ranking.id)
        self.assertEqual(ranking.region, self.ranking.region)
        self.assertEqual(ranking.time, self.ranking.time)
        self.assertEqual(ranking.tournaments, self.ranking.tournaments)
        self.assertEqual(ranking.ranking, self.ranking.ranking)

    def test_get_ranking_for_player_id(self):
      self.assertEqual(
          self.ranking_entry_1.rank,
          self.ranking.get_ranking_for_player_id(self.ranking_entry_1.player))
      self.assertEqual(
          self.ranking_entry_2.rank,
          self.ranking.get_ranking_for_player_id(self.ranking_entry_2.player))

    def test_get_ranking_for_player_id_not_found(self):
      self.assertIsNone(self.ranking.get_ranking_for_player_id(ObjectId()))


class TestRankingEntry(unittest.TestCase):

    def setUp(self):
        self.id_1 = ObjectId()
        self.ranking_entry = RankingEntry(
            rank=1,
            player=self.id_1,
            rating=20.5,
            previous_rank=2)
        self.ranking_entry_json_dict = {
            'rank': 1,
            'player': self.id_1,
            'rating': 20.5,
            'previous_rank': 2
        }

    def test_dump(self):
        self.assertEqual(self.ranking_entry.dump(
            context='db'), self.ranking_entry_json_dict)

    def test_load(self):
        ranking_entry = RankingEntry.load(
            self.ranking_entry_json_dict, context='db')
        self.assertEqual(ranking_entry.rank, self.ranking_entry.rank)
        self.assertEqual(ranking_entry.player, self.ranking_entry.player)
        self.assertEqual(ranking_entry.rating, self.ranking_entry.rating)
        self.assertEqual(ranking_entry.previous_rank, self.ranking_entry.previous_rank)


class TestRegion(unittest.TestCase):

    def setUp(self):
        self.id = 'norcal'
        self.display_name = 'Norcal'
        self.ranking_num_tourneys_attended=2
        self.ranking_activity_day_limit=60
        self.tournament_qualified_day_limit=999
        self.region = Region(id=self.id, display_name=self.display_name,
                             ranking_num_tourneys_attended=self.ranking_num_tourneys_attended,
                             ranking_activity_day_limit=self.ranking_activity_day_limit,
                             tournament_qualified_day_limit=self.tournament_qualified_day_limit)
        self.region_json_dict = {
            '_id': self.id,
            'display_name': self.display_name,
            'ranking_num_tourneys_attended': self.ranking_num_tourneys_attended,
            'ranking_activity_day_limit': self.ranking_activity_day_limit,
            'tournament_qualified_day_limit': self.tournament_qualified_day_limit
        }

    def test_dump(self):
        self.assertEqual(self.region.dump(context='db'), self.region_json_dict)

    def test_load(self):
        region = Region.load(self.region_json_dict, context='db')
        self.assertEqual(region.id, self.id)
        self.assertEqual(region.display_name, self.display_name)


class TestUser(unittest.TestCase):

    def setUp(self):
        self.id = '123abc'
        self.admin_regions = ['norcal', 'texas']
        self.username = 'ASDF fdsa'
        self.salt = 'nacl'
        self.hashed_password = 'browns'
        self.user = User(id=self.id,
                         admin_regions=self.admin_regions,
                         username=self.username,
                         salt=self.salt,
                         hashed_password=self.hashed_password)

        self.user_json_dict = {
            '_id': self.id,
            'username': self.username,
            'admin_regions': self.admin_regions,
            'salt': self.salt,
            'hashed_password': self.hashed_password
        }

    def test_dump(self):
        self.assertEqual(self.user.dump(context='db'), self.user_json_dict)

    def test_load(self):
        user = User.load(self.user_json_dict, context='db')
        self.assertEqual(user.id, self.id)
        self.assertEqual(user.username, self.username)
        self.assertEqual(user.admin_regions, self.admin_regions)
