from bson.objectid import ObjectId
from datetime import datetime

import trueskill

import model
import rating_calculators


def generate_ranking(dao, now=datetime.now(), day_limit=60, num_tourneys=2):
    player_date_map = {}
    player_id_to_player_map = {}

    tournaments = dao.get_all_tournaments(regions=[dao.region_id])
    for tournament in tournaments:
        print 'Processing:', tournament.name.encode('utf-8')

        for player_id in tournament.players:
            player_date_map[player_id] = tournament.date

        # TODO add a default rating entry when we add it to the map
        for match in tournament.matches:

            # don't count matches where either player is OOR
            winner = dao.get_player_by_id(match.winner)
            if dao.region_id not in winner.regions:
                continue
            loser = dao.get_player_by_id(match.loser)
            if dao.region_id not in loser.regions:
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
        key=lambda player: trueskill.expose(player.ratings[dao.region_id].trueskill_rating()), reverse=True)
    ranking = []
    for player in sorted_players:
        player_last_active_date = player_date_map.get(player.id)
        if player_last_active_date is None or \
                dao.is_inactive(player, now, day_limit, num_tourneys) or \
                dao.region_id not in player.regions:
            pass  # do nothing, skip this player
        else:
            ranking.append(model.RankingEntry(
                rank=rank,
                player=player.id, rating=trueskill.expose(player.ratings[dao.region_id].trueskill_rating())))
            rank += 1

    print 'Updating players...'
    for i, p in enumerate(players, start=1):
        dao.update_player(p)
        # TODO: log somewhere later
        # print 'Updated player %d of %d' % (i, len(players))

    print 'Inserting new ranking...'
    dao.insert_ranking(model.Ranking(
        id=ObjectId(),
        region=dao.region_id,
        time=now,
        tournaments=[t.id for t in tournaments],
        ranking=ranking))

    print 'Done!'
