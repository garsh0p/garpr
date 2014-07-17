import dao
import elo

dao.reset_all_player_ratings()
elo.setup(k_factor=24)

tournaments = dao.get_all_tournaments()
for tournament in tournaments:
    print "Processing tournament:", tournament.date, tournament.name
    matches = tournament.matches
    for match in matches:
        winner = dao.get_player_by_alias(match.winner)
        loser = dao.get_player_by_alias(match.loser)

        print "Processing match: %s (%s) > %s (%s)" % (winner.name, winner.rating, loser.name, loser.rating)

        new_winner_rating, new_loser_rating = elo.rate_1vs1(winner.rating, loser.rating)

        dao.update_player_rating(winner, new_winner_rating)
        dao.update_player_rating(loser, new_loser_rating)
        
        print "New ratings: %s (%s), %s (%s)" % (winner.name, new_winner_rating, loser.name, new_loser_rating)
