import trueskill
import dao
from datetime import datetime, timedelta

tournaments = dao.get_all_tournaments()

player_date_map = {}
now = datetime.now()
sixty_days_before = now - timedelta(days=60)

player_rating_map = {}
for player in dao.get_all_players():
    player_rating_map[player.name] = trueskill.Rating()

for tournament in dao.get_all_tournaments():
    for player in tournament.players:
        p = dao.get_player_by_alias(player)
        player_date_map[p.name] = tournament.date

    for match in tournament.matches:
        winner = dao.get_player_by_alias(match.winner)
        loser = dao.get_player_by_alias(match.loser)

        new_winner_rating, new_loser_rating = trueskill.rate_1vs1(player_rating_map[winner.name], player_rating_map[loser.name])
        player_rating_map[winner.name] = new_winner_rating
        player_rating_map[loser.name] = new_loser_rating

ranked_player_list = sorted(player_rating_map, key=player_rating_map.get, reverse=True)
rating_player_map = dict((v,k) for k, v in player_rating_map.iteritems())
sorted_ratings = sorted(rating_player_map.keys(), key=trueskill.expose, reverse=True)
excluded_players = set([p.name for p in dao.get_excluded_players()])

i = 1
for rating in sorted_ratings:
    player = rating_player_map[rating]
    player_last_active_date = player_date_map.get(player)
    if player_last_active_date == None or player_last_active_date < sixty_days_before or player in excluded_players:
        pass # do nothing, skip this player
    else:
        print "%s\t%s\t%s" % (i, rating_player_map[rating], trueskill.expose(rating))
        i += 1
