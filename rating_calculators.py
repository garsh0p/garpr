import trueskill
from model import TrueskillRating

def update_trueskill_ratings(winner=None, loser=None):
    new_winner_rating, new_loser_rating = trueskill.rate_1vs1(winner.rating.trueskill_rating, loser.rating.trueskill_rating)
    winner.rating = TrueskillRating(trueskill_rating=new_winner_rating)
    loser.rating = TrueskillRating(trueskill_rating=new_loser_rating)
