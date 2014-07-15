from scraper.challonge import ChallongeScraper
from scraper.tio import TioScraper

c = ChallongeScraper('TNE_Singles')
print c.get_raw()
