from datetime import datetime, timedelta
from model import *
import rating_calculators
import trueskill

DEFAULT_RATING = TrueskillRating()

def generate_ranking(dao):
    dao.reset_all_player_ratings()

    player_date_map = {}
    now = datetime.now()
    inactivity_threshold = now - timedelta(days=45)
    player_id_to_player_map = dict((p.id, p) for p in dao.get_all_players())

    tournaments = dao.get_all_tournaments()
    for tournament in tournaments:
        print 'Processing:', tournament.name

        for player_id in tournament.players:
            player_date_map[player_id] = tournament.date

        for match in tournament.matches:
            winner = player_id_to_player_map[match.winner]
            loser = player_id_to_player_map[match.loser]

            rating_calculators.update_trueskill_ratings(winner=winner, loser=loser)

    excluded_players = set([p.id for p in dao.get_excluded_players()])
    i = 1
    players = player_id_to_player_map.values()
    sorted_players = sorted(players, key=lambda player: trueskill.expose(player.rating.trueskill_rating), reverse=True)
    ranking = []
    for player in sorted_players:
        player_last_active_date = player_date_map.get(player.id)
        if player_last_active_date == None or player_last_active_date < inactivity_threshold or player.id in excluded_players:
            pass # do nothing, skip this player
        else:
            ranking.append(RankingEntry(i, player.id, trueskill.expose(player.rating.trueskill_rating)))
            i += 1

    print 'Updating players...'
    for p in players:
        dao.update_player(p)

    print 'Inserting new ranking...'
    dao.insert_ranking(Ranking(now, [t.id for t in tournaments], ranking))

    print 'Done!'
