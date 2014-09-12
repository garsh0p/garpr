from datetime import datetime, timedelta
from model import *
import rating_calculators
import trueskill

def generate_ranking(dao):
    dao.reset_all_player_ratings()

    tournaments = dao.get_all_tournaments()

    player_date_map = {}
    now = datetime.now()
    sixty_days_before = now - timedelta(days=60)

    for tournament in dao.get_all_tournaments():
        for player_id in tournament.players:
            player_date_map[player_id] = tournament.date

        for match in tournament.matches:
            winner = dao.get_player_by_id(match.winner)
            loser = dao.get_player_by_id(match.loser)

            rating_calculators.update_trueskill_ratings(winner=winner, loser=loser)

            dao.update_player(winner)
            dao.update_player(loser)

    excluded_players = set([p.id for p in dao.get_excluded_players()])
    i = 1
    players = dao.get_all_players()
    sorted_players = sorted(players, key=lambda player: trueskill.expose(player.rating.trueskill_rating), reverse=True)
    ranking = []
    for player in sorted_players:
        player_last_active_date = player_date_map.get(player.id)
        if player_last_active_date == None or player_last_active_date < sixty_days_before or player.id in excluded_players:
            pass # do nothing, skip this player
        else:
            ranking.append(RankingEntry(i, player.id, trueskill.expose(player.rating.trueskill_rating)))
            i += 1

    dao.insert_ranking(Ranking(now, [t.id for t in dao.get_all_tournaments()], ranking))
