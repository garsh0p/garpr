import requests
import re
import urlparse
from model import MatchResult
from bs4 import BeautifulSoup

# use urllib urljoin?

log_suffix_template = 'log?page=%d'
match_regex = r'reported a .+ win for (.+) over (.+)\.'

class ChallongeScraper(object):
    def __init__(self, url):
        self.url = url

    def get_name(self):
        return None

    def get_date(self):
        return None

    def get_matches(self):
        response = self._verify_status_code(requests.get(url))

        html = response.text
        soup = BeautifulSoup(html)

        log_paths = [li.a['href'] for li in soup.findAll('li', class_=re.compile(r'page.*'))]
        log_page_numbers = [m.group() for log_path in log_paths for m in [re.search(r'\d+$', log_path)] if m]
        max_page_number = int(max(log_page_numbers))

        log_urls = [urlparse.urljoin(self.url, log_suffix_template % i) for i in xrange(1, max_page_number + 1)]

        log_entries = self._get_entries_from_log_urls(log_urls)
        for entry in log_entries:
            m = re.search(match_regex, entry)
            if m:
                match_result = MatchResult(winner=m.group(1), loser=m.group(2))
                print match_result

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
        print log_url
        log_response = cls._verify_status_code(requests.get(log_url))
        log_html = log_response.text
        log_soup = BeautifulSoup(log_html)
        return [entry.text.strip() for entry in log_soup.findAll('td', class_='entry')]


# TODO add log onto the end of URLs
url = 'http://challonge.com/PH2_Singles/log'
scraper = ChallongeScraper(url)

matches = scraper.get_matches()

import pprint
pp = pprint.PrettyPrinter(indent=2)
pp.pprint(matches)
