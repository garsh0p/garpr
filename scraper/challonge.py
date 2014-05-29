import requests
import re
import urlparse
from model import MatchResult
from bs4 import BeautifulSoup

log_url_path = 'log'
log_suffix_template = 'log?page=%d'
match_regex = r'reported a .+ win for (.+) over (.+)\.'
reset_regex = r'This tournament was reset'
change_regex = r'changed the outcome of (.+) vs. (.+) to a .+ win for (.+)\.'

class ChallongeScraper(object):
    def __init__(self, url):
        self.url = url

    def get_name(self):
        return None

    def get_date(self):
        return None

    def get_matches(self):
        full_log_url = urlparse.urljoin(self.url, log_url_path)
        response = self._verify_status_code(requests.get(full_log_url))

        html = response.text
        soup = BeautifulSoup(html)

        log_paths = [li.a['href'] for li in soup.findAll('li', class_=re.compile(r'page.*'))]
        log_page_numbers = [m.group() for log_path in log_paths for m in [re.search(r'\d+$', log_path)] if m]
        max_page_number = int(max(log_page_numbers))

        log_urls = [urlparse.urljoin(full_log_url, log_suffix_template % i) for i in xrange(1, max_page_number + 1)]

        log_entries = self._get_entries_from_log_urls(log_urls)
        print 'Log size:', len(log_entries)

        # find the latest time the tournament was reset and ignore everything before it
        for i in reversed(xrange(len(log_entries))):
            if re.search(reset_regex, log_entries[i]):
                print 'Reset detected.'
                log_entries = log_entries[i:]
                print 'New log size:', len(log_entries)
                break

        # create MatchResult objects from the log entries
        match_results = []
        for entry in log_entries:
            m = re.search(match_regex, entry)
            if m:
                match_result = MatchResult(winner=m.group(1), loser=m.group(2))
                match_results.append(match_result)
                print match_result
                continue

            m = re.search(change_regex, entry)
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
        if response.status_code != 200:
            raise Exception('Received status code of %d' % response.status_code)
        else:
            return response

    @classmethod
    def _get_entries_from_log_urls(cls, log_urls):
        return [entry for log_url in log_urls for entry in cls._get_entries_from_log_url(log_url)]

    @classmethod
    def _get_entries_from_log_url(cls, log_url):
        print 'Retrieving', log_url
        log_response = cls._verify_status_code(requests.get(log_url))
        log_html = log_response.text
        log_soup = BeautifulSoup(log_html)
        return [entry.text.strip() for entry in log_soup.findAll('td', class_='entry')]


url = 'http://challonge.com/TNE_singles/'
scraper = ChallongeScraper(url)

matches = scraper.get_matches()

print ''
for match in matches:
    print match
