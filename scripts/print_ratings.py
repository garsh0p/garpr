import dao
from datetime import datetime, timedelta

def get_player_active_dates():
    player_date_map = {}

    tournaments = dao.get_all_tournaments()
    for tournament in tournaments:
        for player in tournament.players:
            p = dao.get_player_by_alias(player)
            player_date_map[p.name] = tournament.date

    return player_date_map


player_date_map = get_player_active_dates()
now = datetime.now()
sixty_days_before = now - timedelta(days=60)

players = dao.get_all_players_sorted_by_rating()
rank = 1
for player in players:
    player_last_active_date = player_date_map.get(player.name)
    if player_last_active_date == None or player_last_active_date < sixty_days_before:
        pass # do nothing, skip this player
    else:
        print "%d. %s %s" % (rank, player.name, player.rating)
        rank += 1
