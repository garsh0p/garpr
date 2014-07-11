from scraper.challonge import ChallongeScraper
from scraper.tio import TioScraper
import os

scrapers = [
        ChallongeScraper('http://challonge.com/sfthrowdown1'),
        ChallongeScraper('http://macromicrogaming.challonge.com/ss15ssbm'),
        ChallongeScraper('http://showdownesports.challonge.com/SFGameNight5'),
        ChallongeScraper('http://challonge.com/ncm5'),
        ChallongeScraper('http://showdownesports.challonge.com/SFGameNight6'),
        ChallongeScraper('http://challonge.com/ncw1'),
        ChallongeScraper('http://challonge.com/sfgamenight7'),
        TioScraper(os.path.join('/drive1/Tio', '2014-06-27 NorCal Weeklies #2.tio'), 'Double Elim Bracket - Smash'),
        TioScraper(os.path.join('/drive1/Tio', '2014-06-28 Bay Area Monthly #1 Press 1.tio'), 'BAM Singles'),
        ChallongeScraper('http://challonge.com/sfgamenight8'),
        TioScraper(os.path.join('/drive1/Tio', '2014-07-06 Bay Area Monthly #2 We\'ll Take It.tio'), 'Singles'),
        ChallongeScraper('http://challonge.com/sfgamenight9')
]

players = set()
lower_players = set()
matches = []

'''
for scraper in scrapers:
    c_players = scraper.get_players()
    for c_player in c_players:
        if not c_player.lower() in lower_players:
            players.add(c_player)
            lower_players.add(c_player.lower())

    matches.extend(scraper.get_matches())

for match in matches:
    print match
'''

import elo
from model import Player

elo.setup(k_factor=24)

player_map = {}
with open('players.txt') as f:
    for line in f:
        name = line.strip().split(',')[0]
        aliases = [alias.strip().lower() for alias in line.strip().split(',')]
        player = Player(name, aliases, 1200)
        for alias in aliases:
            player_map[alias] = player

with open('matches.txt') as f:
    for line in f:
        split_line = line.strip().split(' > ')
        winner = player_map[split_line[0].lower()]
        loser = player_map[split_line[1].lower()]

        winner.rating, loser.rating = elo.rate_1vs1(winner.rating, loser.rating)


players = set(player_map.values())
rankings = sorted(players, key=lambda player: player.rating, reverse=True)

for player in rankings:
    print player.name, player.rating
