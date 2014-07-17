import dao

players = dao.get_all_players_by_rating()
rank = 1
for player in players:
    print "%d. %s %s" % (rank, player.name, player.rating)
    rank += 1
