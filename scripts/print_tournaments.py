import sys
from dao import Dao

dao = Dao(sys.argv[1])

for tournament in dao.get_all_tournaments():
    print "%s-%s-%s\t%s" % (tournament.date.year, tournament.date.month, tournament.date.day, tournament.name)
