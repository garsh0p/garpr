import requests
import re
import os
from model import MatchResult
from bs4 import BeautifulSoup

LOG_URL_PATH = 'log'
LOG_SUFFIX_TEMPLATE = 'log?page=%d'

MATCH_REGEX = r'reported a .+ win for (.+) over (.+)\.'
RESET_REGEX = r'This tournament was reset'
CHANGE_REGEX = r'changed the outcome of (.+) vs. (.+) to a .+ win for (.+)\.'

class ChallongeScraper(object):
    def __init__(self, url):
        self.url = url
        self.name = None
        self.date = None
        self.matches = None
        self.players = None

    def get_name(self):
        if not self.name:
            soup = self._verify_status_code(requests.get(self.url))
            self.name = soup.find('div', id='title').text.strip()

        return self.name

    # there's no good way to get the date from a challonge bracket (only day/month, not year)
    def get_date(self):
        return None

    def get_matches(self):
        if not self.matches:
            self.matches = self._get_matches()

        return self.matches

    def get_players(self):
        if not self.players:
            self.players = set()
            matches = self.get_matches()
            for match in matches:
                self.players.add(match.winner)
                self.players.add(match.loser)

        return self.players

    def _get_matches(self):
        full_log_url = os.path.join(self.url, LOG_URL_PATH)
        soup = self._verify_status_code(requests.get(full_log_url))

        log_paths = [li.a['href'] for li in soup.findAll('li', class_=re.compile(r'page.*'))]
        log_page_numbers = [m.group() for log_path in log_paths for m in [re.search(r'\d+$', log_path)] if m]
        max_page_number = int(max(log_page_numbers))

        log_urls = [os.path.join(self.url, LOG_SUFFIX_TEMPLATE % i) for i in xrange(1, max_page_number + 1)]

        log_entries = self._get_entries_from_log_urls(log_urls)
        print 'Log size:', len(log_entries)

        # find the latest time the tournament was reset and ignore everything before it
        for i in reversed(xrange(len(log_entries))):
            if re.search(RESET_REGEX, log_entries[i]):
                print 'Reset detected.'
                log_entries = log_entries[i:]
                print 'New log size:', len(log_entries)
                break

        # create MatchResult objects from the log entries
        match_results = []
        for entry in log_entries:
            m = re.search(MATCH_REGEX, entry)
            if m:
                match_result = MatchResult(winner=m.group(1), loser=m.group(2))
                match_results.append(match_result)
                continue

            m = re.search(CHANGE_REGEX, entry)
            if m:
                result_changed = False

                print 'Change detected:', entry
                winner = m.group(3)
                loser = m.group(1) if winner == m.group(2) else m.group(2)
                match_result = MatchResult(winner=winner, loser=loser)

                # find the match result we need to change
                for i in reversed(range(len(match_results))):
                    if match_results[i].contains_players(winner, loser):
                        print 'Previous match result:', match_results[i]
                        match_results[i] = match_result
                        print 'New match result:', match_results[i]
                        result_changed = True
                        break

                if not result_changed:
                    raise Exception('No previous match result was found to process change: %s' % (entry))

        return match_results

    @staticmethod
    def _verify_status_code(response):
        """Returns a BeautifulSoup object from the response"""
        if response.status_code != 200:
            raise Exception('Received status code of %d' % response.status_code)
        else:
            return BeautifulSoup(response.text)

    @classmethod
    def _get_entries_from_log_urls(cls, log_urls):
        return [entry for log_url in log_urls for entry in cls._get_entries_from_log_url(log_url)]

    @classmethod
    def _get_entries_from_log_url(cls, log_url):
        print 'Retrieving', log_url
        log_soup = cls._verify_status_code(requests.get(log_url))
        return [entry.text.strip() for entry in log_soup.findAll('td', class_='entry')]

