from scraper.challonge import ChallongeScraper

URL = "http://challonge.com/TNE_Singles"

scraper = ChallongeScraper(URL)
matches = scraper.get_matches()
print "Number of matches", len(matches)
