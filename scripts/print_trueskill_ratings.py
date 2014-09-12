import requests
import sys

RANKINGS_URL = "http://garsh0p.no-ip.biz:5100/%s/rankings" % sys.argv[1]

r = requests.get(RANKINGS_URL)
ranking = r.json()['ranking']

for line in ranking:
    print "%s\t%s\t%.3f" % (line['rank'], line['name'], line['rating'])
