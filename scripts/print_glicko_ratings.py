import dao
from datetime import datetime, timedelta
from glicko import glicko2

tournaments = dao.get_all_tournaments()

player_date_map = {}
now = datetime.now()
sixty_days_before = now - timedelta(days=60)

player_rating_map = {}
for player in dao.get_all_players():
    player_rating_map[player.name] = glicko2.Player()

for tournament in dao.get_all_tournaments():
    for player in tournament.players:
        p = dao.get_player_by_alias(player)
        player_date_map[p.name] = tournament.date

    for match in tournament.matches:
        winner = dao.get_player_by_alias(match.winner)
        loser = dao.get_player_by_alias(match.loser)

        glicko_winner = player_rating_map[winner.name]
        glicko_loser = player_rating_map[loser.name]

        glicko_winner_copy = glicko2.Player(rating=glicko_winner.getRating(), rd=glicko_winner.getRd(), vol=glicko_winner.vol)
        glicko_loser_copy = glicko2.Player(rating=glicko_loser.getRating(), rd=glicko_loser.getRd(), vol=glicko_loser.vol)

        glicko_winner.update_player([glicko_loser_copy.getRating()], [glicko_loser_copy.getRd()], [1])
        glicko_loser.update_player([glicko_winner_copy.getRating()], [glicko_winner_copy.getRd()], [0])


ranked_player_list = sorted(player_rating_map, key=player_rating_map.get, reverse=True)
rating_player_map = dict((v,k) for k, v in player_rating_map.iteritems())
sorted_ratings = sorted(rating_player_map.keys(), key=lambda r: r.getRating(), reverse=True)
excluded_players = set([p.name for p in dao.get_excluded_players()])

i = 1
for rating in sorted_ratings:
    player = rating_player_map[rating]
    player_last_active_date = player_date_map.get(player)
    if player_last_active_date == None or player_last_active_date < sixty_days_before or player in excluded_players:
        pass # do nothing, skip this player
    else:
        print i, rating_player_map[rating], rating.getRating(), rating.getRd()
        i += 1
