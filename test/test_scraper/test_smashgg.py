import unittest
import os
import json
from scraper.smashgg import SmashGGScraper

TEST_URL_1 = 'https://smash.gg/tournament/htc-throwdown/events/melee-singles/brackets/2096/6529'
TEST_URL_2 = 'https://smash.gg/tournament/tiger-smash-4/events/melee-singles/brackets/21317/70949'
TEST_URL_3 = 'https://smash.gg/tournament/ceo-2016/events/wii-u-singles/brackets/45259/150418'
TEST_URL_4 = 'https://smash.gg/tournament/nebulous-prime-melee-47/events/melee-singles/brackets/49705/164217'
TEST_DATA1 = os.path.abspath('test' + os.sep + 'test_scraper' + os.sep + 'data' + os.sep + 'smashgg.json')
TEST_DATA2 = os.path.abspath('test' + os.sep + 'test_scraper' + os.sep + 'data' + os.sep + 'smashgg2.json')
TEST_EVENT_NAME_1 = 'htc-throwdown'
TEST_EVENT_NAME_2 = 'tiger-smash-4'
TEST_EVENT_NAME_3 = 'nebulous-prime-melee-47'
TEST_PHASE_NAME_1 = 'melee-singles'
TEST_PHASE_ID_1 = 2096
TEST_PHASE_ID_2 = 21317
TEST_PHASE_ID_3 = 45259
TEST_PHASE_GROUP_ID_1 = 11226
TEST_PHASE_GROUP_ID_2 = 70949
TEST_PHASE_GROUP_ID_3 = 83088
TEST_PLAYER_ENTRANTID_1 = 16081
TEST_PLAYER_ENTRANTID_2 = 110555
TEST_PLAYER_ENTRANTID_3 = 52273
TEST_PLAYER_SMASHGGID_1 = 1000
TEST_PLAYER_SMASHGGID_2 = 4442
TEST_PLAYER_SMASHGGID_3 = 13932

# TO ACCESS THE SMASHGG DUMPS USED HERE, THE FOLLOWING LINKS WILL GET YOU THERE
# https://api.smash.gg/phase_group/11226?expand[0]=sets&expand[1]=seeds&expand[2]=entrants&expand[3]=matches TEST API
# https://api.smash.gg/phase_group/6529?expand[0]=sets&expand[1]=seeds&expand[2]=entrants&expand[3]=matches
# https://api.smash.gg/phase_group/70949?expand[0]=sets&expand[1]=seeds&expand[2]=entrants&expand[3]=matches

class TestSmashGGScraper(unittest.TestCase):
    def setUp(self):
        self.tournament1 = TestSmashGGScraper.tournament1
        self.tournament2 = TestSmashGGScraper.tournament2
        #self.tournament3 = TestSmashGGScraper.tournament3
        self.tournament4 = TestSmashGGScraper.tournament4
        #self.excluded_phases3 = [49706]
        #self.tournament3 = SmashGGScraper(TEST_URL_3)
        #list = self.tournament3.get_matches()
        #print 'hello'

    # query tons of URLs just once, not for each test
    @classmethod
    def setUpClass(cls):
        print 'Pulling tournaments from smash.gg ...'
        super(TestSmashGGScraper, cls).setUpClass()
        cls.tournament1 = SmashGGScraper(TEST_URL_1, [1511, 2095, 2096])
        cls.tournament2 = SmashGGScraper(TEST_URL_2, [3930, 21317])
        #cls.tournament3 = SmashGGScraper(TEST_URL_3, [])
        cls.tournament4 = SmashGGScraper(TEST_URL_4, [49153, 49705])


    def tearDown(self):
        self.tournament1 = None
        self.tournament2 = None
        #self.tournament3 = None
        self.tournament4 = None

    @unittest.skip('skipping test_get_raw1 until api is complete')
    def test_get_raw1(self):
        with open(TEST_DATA1) as data1:
            self.tournament1_json_dict = json.load(data1)
        self.assertEqual(self.tournament1.get_raw()['smashgg'], self.tournament1_json_dict)

    @unittest.skip('skipping test_get_raw2 until api is complete')
    def test_get_raw2(self):
        with open(TEST_DATA2) as data2:
            self.tournament2_json_dict = json.load(data2)
        self.assertEqual(self.tournament2.get_raw()['smashgg'], self.tournament2_json_dict)

    # @unittest.skip('test is failing, May be API agile iterations manipulating data. Need to revisit')
    def test_get_raw_sub(self):
        raw = self.tournament1.get_raw()

        self.assertTrue('event' in raw)
        self.assertTrue('groups' in raw)
        self.assertEqual(len(raw['groups']), 35)

        entrants = raw['event']['entities']['entrants']
        for entrant in entrants:
            self.assertIsNotNone(entrant['id'])

        # TODO: add more stuff

        raw = self.tournament2.get_raw()

        self.assertTrue('event' in raw)
        self.assertTrue('groups' in raw)
        self.assertEqual(len(raw['groups']), 9)

        entrants = raw['event']['entities']['entrants']
        for entrant in entrants:
            self.assertIsNotNone(entrant['id'])

        # TODO: add more stuff

    def test_player_lookup(self):
        player = self.tournament1.player_lookup[TEST_PLAYER_ENTRANTID_1]
        self.assertEqual(player.smash_tag, 'C9 | Mango')

        player = self.tournament2.player_lookup[TEST_PLAYER_ENTRANTID_2]
        self.assertEqual(player.smash_tag, 'Druggedfox')

    def test_get_players(self):
        self.assertEqual(len(self.tournament1.get_players()), 386)
        self.assertEquals(len(self.tournament2.get_players()), 75)

    def test_get_matches(self):
        tournament_1_matches = self.tournament1.get_matches()
        self.assertEqual(len(tournament_1_matches), 731)
        # spot check that mang0 got double elim'd
        mango_count = 0
        for m in tournament_1_matches:
            if m.loser == 'C9 | Mango':
                mango_count += 1
        self.assertEqual(2, mango_count, msg="mango didnt get double elim'd?")

        # Make sure grand finals is at the end
        grand_finals = tournament_1_matches[-1]
        self.assertEqual('TSM | Leffen', grand_finals.winner)
        self.assertEqual('Liquid` | Hungrybox', grand_finals.loser)

        tournament_2_matches = self.tournament2.get_matches()
        self.assertEquals(len(tournament_2_matches), 361)
        # spot check that Druggedfox was only in 5 matches, and that he won all of them
        sami_count = 0
        for m in tournament_2_matches:
            if m.winner == 'Druggedfox':
                sami_count += 1
            self.assertFalse(m.loser == 'Druggedfox')
        self.assertEqual(14, sami_count)

        # Make sure grand finals is at the end
        grand_finals = tournament_2_matches[-1]
        self.assertEqual('Druggedfox', grand_finals.winner)
        self.assertEqual('PG | ESAM', grand_finals.loser)

    def test_get_date(self):
        date = self.tournament1.get_date()
        self.assertEqual(date.year, 2015)
        self.assertEqual(date.month, 9)
        self.assertEqual(date.day, 19)

        date = self.tournament2.get_date()
        self.assertEqual(date.year, 2016)
        self.assertEqual(date.month, 3)
        self.assertEqual(date.day, 26)

    def test_get_name(self):
        self.assertEqual(self.tournament1.get_name(), 'htc throwdown')
        self.assertEqual(self.tournament2.get_name(), 'tiger smash 4')

    def test_duplicate_tags(self):
        tags = self.tournament1.get_players()
        self.assertEqual(len(tags), len(set(tags)))
        tags = self.tournament2.get_players()
        self.assertEqual(len(tags), len(set(tags)))

    def test_get_group_ids(self):
        group_ids = self.tournament1.get_group_ids()
        self.assertEqual(len(group_ids), 35)
        group_ids = self.tournament2.get_group_ids()
        self.assertEqual(len(group_ids), 10)

    def test_get_tournament_phase_id_from_url(self):
        self.assertEqual(SmashGGScraper.get_tournament_phase_id_from_url(TEST_URL_1), 6529)
        self.assertEqual(SmashGGScraper.get_tournament_phase_id_from_url(TEST_URL_2), 70949)

    def test_get_tournament_name_from_url(self):
        self.assertEqual(SmashGGScraper.get_tournament_name_from_url(TEST_URL_1), 'htc throwdown')
        self.assertEqual(SmashGGScraper.get_tournament_name_from_url(TEST_URL_2), 'tiger smash 4')

    def test_get_event_name(self):
        self.assertEqual(SmashGGScraper.get_event_name(TEST_EVENT_NAME_1, TEST_PHASE_NAME_1), 'Melee Singles')
        self.assertEqual(SmashGGScraper.get_event_name(TEST_EVENT_NAME_2, TEST_PHASE_NAME_1), 'Melee Singles')

    def test_get_phase_name(self):
        self.assertEqual(SmashGGScraper.get_phase_bracket_name(TEST_PHASE_ID_1), 'Round 2 Bracket')
        self.assertEqual(SmashGGScraper.get_phase_bracket_name(TEST_PHASE_ID_2), 'Final Bracket')

    def test_get_phasename_id_map(self):
        self.assertEqual(len(SmashGGScraper.get_phasename_id_map(TEST_EVENT_NAME_1, TEST_PHASE_NAME_1)), 3)
        self.assertEqual(len(SmashGGScraper.get_phasename_id_map(TEST_EVENT_NAME_2, TEST_PHASE_NAME_1)), 3)

    def test_included_phases(self):
        self.assertEqual(len(self.tournament2.group_dicts), 9)
        self.assertEqual(len(self.tournament4.group_dicts), 9)
