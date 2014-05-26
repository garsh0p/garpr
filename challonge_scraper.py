from scrapy.item import Item, Field
from scrapy.spider import Spider

class Match(Item):
    winner = Field()
    loser = Field()

class ChallongeSpider(Spider):
    name = 'challonge'
    start_urls = ['http://oxy.challonge.com/SmashSundaysSingles20/log']
    allowed_domains = ['challonge.com']

    def parse(self, response):
        filename = response.url.split("/")[-2]
        open(filename, 'wb').write(response.body)
