import requests

TOURNAMENTS_URL = "http://garsh0p.no-ip.biz:5100/norcal/tournaments"

r = requests.get(TOURNAMENTS_URL)
tournaments = r.json()['tournaments']

for tournament in tournaments:
    print "%s\t%s" % (tournament['date'], tournament['name'])
