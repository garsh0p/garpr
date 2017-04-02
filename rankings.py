from bson.objectid import ObjectId
from datetime import datetime, timedelta

import trueskill

import model
import rating_calculators


def generate_ranking(
        dao,
        now=datetime.now(),
        day_limit=60,
        num_tourneys=2,
        tournament_qualified_day_limit=999,
        tournament_to_diff=None):
    tournaments = dao.get_all_tournaments(regions=[dao.region_id])
    ranking_to_diff_against = None
    if tournament_to_diff:
        tournaments_for_diff = []
        for tournament in tournaments:
            tournaments_for_diff.append(tournament)
            if tournament.id == tournament_to_diff.id:
                break

        ranking_to_diff_against = _create_ranking_from_tournament_list(
            dao, tournaments_for_diff, tournament_to_diff.date, day_limit, num_tourneys, tournament_qualified_day_limit, None)


    dao.insert_ranking(_create_ranking_from_tournament_list(
        dao, tournaments, now, day_limit, num_tourneys, tournament_qualified_day_limit, ranking_to_diff_against))


def _create_ranking_from_tournament_list(
        dao,
        tournaments,
        now,
        day_limit,
        num_tourneys,
        tournament_qualified_day_limit,
        ranking_to_diff_against):
    player_date_map = {}
    player_id_to_player_map = {}

    tournament_qualified_date = (now - timedelta(days=tournament_qualified_day_limit))
    print('Qualified Date: ' + str(tournament_qualified_date))

    for tournament in tournaments:
        if tournament_qualified_date <= tournament.date:
            print 'Processing:', tournament.name.encode('utf-8'), str(tournament.date)
            for player_id in tournament.players:
                player_date_map[player_id] = tournament.date

            # TODO add a default rating entry when we add it to the map
            for match in tournament.matches:
                if match.excluded is True:
                    print('match excluded:')
                    print('Tournament: ' + str(tournament.name))
                    print(str(match))
                    continue

                if match.winner not in player_id_to_player_map:
                    db_player = dao.get_player_by_id(match.winner)
                    db_player.ratings[dao.region_id] = model.Rating()
                    player_id_to_player_map[match.winner] = db_player

                if match.loser not in player_id_to_player_map:
                    db_player = dao.get_player_by_id(match.loser)
                    db_player.ratings[dao.region_id] = model.Rating()
                    player_id_to_player_map[match.loser] = db_player

                winner = player_id_to_player_map[match.winner]
                loser = player_id_to_player_map[match.loser]

                rating_calculators.update_trueskill_ratings(
                    dao.region_id, winner=winner, loser=loser)

    print 'Checking for player inactivity...'
    rank = 1
    players = player_id_to_player_map.values()
    sorted_players = sorted(
        players,
        key=lambda player: (trueskill.expose(player.ratings[dao.region_id].trueskill_rating()), player.name),
        reverse=True)
    ranking = []
    for player in sorted_players:
        player_last_active_date = player_date_map.get(player.id)
        if _is_player_inactive(dao, player, tournaments, player_last_active_date, now, day_limit, num_tourneys):
            pass  # do nothing, skip this player
        else:
            ranking.append(model.RankingEntry(
                rank=rank,
                player=player.id,
                rating=trueskill.expose(player.ratings[dao.region_id].trueskill_rating()),
                previous_rank=ranking_to_diff_against.get_ranking_for_player_id(player.id) if ranking_to_diff_against else None))
            rank += 1

    print 'Updating players...'
    for i, p in enumerate(players, start=1):
        dao.update_player(p)
        # TODO: log somewhere later
        # print 'Updated player %d of %d' % (i, len(players))

    print 'Returning new ranking...'
    return model.Ranking(
        id=ObjectId(),
        region=dao.region_id,
        time=now,
        tournaments=[t.id for t in tournaments],
        ranking=ranking)


def _is_player_inactive(dao, player, tournaments, player_last_active_date, now, day_limit, num_tourneys):
    if (player_last_active_date is None or
        dao.region_id not in player.regions):
      return True

    tournaments_for_player = [
        tournament for tournament in tournaments if
        tournament.contains_player(player) and tournament.date >= (now - timedelta(days=day_limit))]

    return len(tournaments_for_player) < num_tourneys
