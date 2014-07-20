import trueskill
import dao
import rating_calculators
from datetime import datetime, timedelta

dao.reset_all_player_ratings()

tournaments = dao.get_all_tournaments()

player_date_map = {}
now = datetime.now()
sixty_days_before = now - timedelta(days=60)

for tournament in dao.get_all_tournaments():
    for player in tournament.players:
        p = dao.get_player_by_alias(player)
        player_date_map[p.name] = tournament.date

    for match in tournament.matches:
        winner = dao.get_player_by_alias(match.winner)
        loser = dao.get_player_by_alias(match.loser)

        rating_calculators.update_trueskill_ratings(winner=winner, loser=loser)

        dao.update_player(winner)
        dao.update_player(loser)


excluded_players = set([p.name for p in dao.get_excluded_players()])
i = 1
players = dao.get_all_players()
sorted_players = sorted(players, key=lambda player: trueskill.expose(player.rating.trueskill_rating), reverse=True)
for player in sorted_players:
    player_last_active_date = player_date_map.get(player.name)
    if player_last_active_date == None or player_last_active_date < sixty_days_before or player.name in excluded_players:
        pass # do nothing, skip this player
    else:
        print "%s\t%s\t%s" % (i, player.name, trueskill.expose(player.rating.trueskill_rating))
        i += 1

    

