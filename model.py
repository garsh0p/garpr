from bson.objectid import ObjectId

import trueskill

import orm

SOURCE_TYPE_CHOICES = ('tio', 'challonge', 'smashgg', 'other')

# Embedded documents

class AliasMapping(orm.Document):
    collection_name = None
    fields = [('player_id', orm.ObjectIDField()),
              ('player_alias', orm.StringField(required=True))]


class AliasMatch(orm.Document):
    collection_name = None
    fields = [('winner', orm.StringField(required=True)),
              ('loser', orm.StringField(required=True))]


class Match(orm.Document):
    collection_name = None
    fields = [('match_id', orm.IntField(required=True)),
              ('winner', orm.ObjectIDField(required=True)),
              ('loser', orm.ObjectIDField(required=True)),
              ('excluded', orm.BooleanField(required=True, default=False))]


    def __str__(self):
        return "%s > %s" % (self.winner, self.loser)

    def contains_players(self, player1, player2):
        return (self.winner == player1 and self.loser == player2) or \
               (self.winner == player2 and self.loser == player1)

    def contains_player(self, player_id):
        return self.winner == player_id or self.loser == player_id

    def did_player_win(self, player_id):
        return self.winner == player_id

    def get_opposing_player_id(self, player_id):
        if self.winner == player_id:
            return self.loser
        elif self.loser == player_id:
            return self.winner
        else:
            return None


class RankingEntry(orm.Document):
    collection_name = None
    fields = [('player', orm.ObjectIDField(required=True)),
              ('rank', orm.IntField(required=True)),
              ('rating', orm.FloatField(required=True))]


class Rating(orm.Document):
    collection_name = None
    fields = [('mu', orm.FloatField(required=True, default=25.)),
              ('sigma', orm.FloatField(required=True, default=25. / 3))]

    def trueskill_rating(self):
        return trueskill.Rating(mu=self.mu, sigma=self.sigma)

    @classmethod
    def from_trueskill(cls, trueskill_rating):
        return Rating(mu=trueskill_rating.mu,
                      sigma=trueskill_rating.sigma)


# MongoDB collection documents

MONGO_ID_SELECTOR = {'db': '_id',
                     'web': 'id'}


class Player(orm.Document):
    collection_name = 'players'
    fields = [('id', orm.ObjectIDField(required=True, load_from=MONGO_ID_SELECTOR,
                                       dump_to=MONGO_ID_SELECTOR)),
              ('name', orm.StringField(required=True)),
              ('aliases', orm.ListField(orm.StringField())),
              ('ratings', orm.DictField(orm.StringField(), orm.DocumentField(Rating))),
              ('regions', orm.ListField(orm.StringField())),
              ('merged', orm.BooleanField(required=True, default=False)),
              ('merge_parent', orm.ObjectIDField()),
              ('merge_children', orm.ListField(orm.ObjectIDField()))
              ]

    def validate_document(self):
        # check: merged is True <=> merge_parent is not None
        if self.merged and self.merge_parent is None:
            return False, "player is merged but has no parent"

        if self.merge_parent is not None and not self.merged:
            return False, "player has merge_parent but is not merged"

        return True, None

    def post_init(self):
        # initialize merge_children to contain id if it does not already
        if not self.merge_children:
            self.merge_children = [self.id]

        # if aliases empty add name to aliases
        if not self.aliases:
            self.aliases = [self.name.lower()]

    @classmethod
    def create_with_default_values(cls, name, region):
        return cls(id=ObjectId(),
                   name=name,
                   aliases=[name.lower()],
                   ratings={},
                   regions=[region])


class Tournament(orm.Document):
    collection_name = 'tournaments'
    fields = [('id', orm.ObjectIDField(required=True, load_from=MONGO_ID_SELECTOR,
                                       dump_to=MONGO_ID_SELECTOR)),
              ('name', orm.StringField(required=True)),
              ('type', orm.StringField(
                  required=True,
                  validators=[orm.validate_choices(SOURCE_TYPE_CHOICES)])),
              ('date', orm.DateTimeField()),
              ('regions', orm.ListField(orm.StringField())),
              ('url', orm.StringField()),
              ('raw_id', orm.ObjectIDField()),
              ('matches', orm.ListField(orm.DocumentField(Match))),
              ('players', orm.ListField(orm.ObjectIDField())),
              ('orig_ids', orm.ListField(orm.ObjectIDField()))]

    def validate_document(self):
        # check: set of players in players = set of players in matches
        players_ids = {player for player in self.players}
        matches_ids = {match.winner for match in self.matches} | \
                      {match.loser for match in self.matches}

        if players_ids != matches_ids:
            return False, "set of players in players differs from set of players in matches"

        # check: no one plays themselves
        for match in self.matches:
            if match.winner == match.loser:
                return False, "tournament contains match where player plays themself"

        # check: len of orig_ids should equal len of players
        if len(self.orig_ids) != len(self.players):
            return False, "different number of orig_ids and players"

        return True, None

    def post_init(self):
        # if orig_ids empty, set to players
        if not self.orig_ids:
            self.orig_ids = [player for player in self.players]

    def replace_player(self, player_to_remove=None, player_to_add=None):
        # TODO edge cases with this
        # TODO the player being added cannot play himself in any match
        if player_to_remove is None or player_to_add is None:
            raise TypeError(
                "player_to_remove and player_to_add cannot be None!")

        player_to_remove_id = player_to_remove.id
        player_to_add_id = player_to_add.id

        if player_to_remove_id not in self.players:
            print "Player with id %s is not in this tournament. Ignoring." % player_to_remove.id
            return

        self.players.remove(player_to_remove_id)
        self.players.append(player_to_add_id)

        for match in self.matches:
            if match.winner == player_to_remove_id:
                match.winner = player_to_add_id

            if match.loser == player_to_remove_id:
                match.loser = player_to_add_id

    @classmethod
    def from_pending_tournament(cls, pending_tournament):
        # takes a real alias to id map instead of a list of objects
        def _get_player_id_from_map_or_throw(alias_to_id_map, alias):
            if alias in alias_to_id_map:
                return alias_to_id_map[alias]
            else:
                raise ValueError('Alias %s has no ID in map\n: %s' %
                                 (alias, alias_to_id_map))

        alias_to_id_map = dict([(entry.player_alias, entry.player_id)
                                for entry in pending_tournament.alias_to_id_map
                                if entry.player_id is not None])

        # we need to convert pending tournament players/matches to player IDs
        print pending_tournament.players, pending_tournament.matches
        players = [_get_player_id_from_map_or_throw(
            alias_to_id_map, p) for p in pending_tournament.players]

        matches = []
        counter = 0
        for am in pending_tournament.matches:
            m = Match(
                match_id=counter,
                winner=_get_player_id_from_map_or_throw(
                    alias_to_id_map, am.winner),
                loser=_get_player_id_from_map_or_throw(
                    alias_to_id_map, am.loser),
                excluded=False
            )
            matches.append(m)
            counter+=1

        return cls(
            id=pending_tournament.id,
            name=pending_tournament.name,
            type=pending_tournament.type,
            date=pending_tournament.date,
            regions=pending_tournament.regions,
            url=pending_tournament.url,
            raw_id=pending_tournament.raw_id,
            matches=matches,
            players=players,
            orig_ids=players)


class PendingTournament(orm.Document):
    collection_name = 'pending_tournaments'
    fields = [('id', orm.ObjectIDField(required=True, load_from=MONGO_ID_SELECTOR,
                                       dump_to=MONGO_ID_SELECTOR)),
              ('name', orm.StringField(required=True)),
              ('type', orm.StringField(required=True)),
              ('date', orm.DateTimeField()),
              ('regions', orm.ListField(orm.StringField())),
              ('url', orm.StringField()),
              ('raw_id', orm.ObjectIDField()),
              ('matches', orm.ListField(orm.DocumentField(AliasMatch))),
              ('players', orm.ListField(orm.StringField())),
              ('alias_to_id_map', orm.ListField(orm.DocumentField(AliasMapping)))]

    def validate_document(self):
        # check: set of aliases = set of aliases in matches
        players_aliases = set(self.players)
        matches_aliases = {match.winner for match in self.matches} | \
                          {match.loser for match in self.matches}
        mapping_aliases = {mapping.player_alias for mapping in self.alias_to_id_map}

        if players_aliases != matches_aliases:
            return False, "set of players in players differs from set of players in matches"

        # check: set of aliases in mapping is subset of player aliases
        if not mapping_aliases.issubset(players_aliases):
            return False, "alias mappings contain mapping for alias not in tournament"

        return True, None


    def set_alias_id_mapping(self, alias, id):
        if self.alias_to_id_map is None:
            self.alias_to_id_map = []

        for mapping in self.alias_to_id_map:
            if mapping.player_alias == alias:
                mapping.player_alias = alias
                mapping.player_id = id
                return

        # if we've gotten out here, we couldn't find an existing match, so add
        # a new element
        self.alias_to_id_map.append(AliasMapping(
            player_alias=alias,
            player_id=id
        ))

    def delete_alias_id_mapping(self, alias):
        if self.alias_to_id_map is None:
            self.alias_to_id_map = []

        for mapping in self.alias_to_id_map:
            if mapping.player_alias == alias:
                self.alias_to_id_map.remove(mapping)
                return mapping

    @classmethod
    def from_scraper(cls, type, scraper, region_id):
        raw_file = RawFile(id=ObjectId(),
                           data=str(scraper.get_raw()))
        pending_tournament = cls(
            id=ObjectId(),
            name=scraper.get_name(),
            type=type,
            date=scraper.get_date(),
            regions=[region_id],
            url=scraper.get_url(),
            raw_id=raw_file.id,
            players=scraper.get_players(),
            matches=scraper.get_matches())
        return pending_tournament, raw_file

# used to store large blobs of data (e.g. raw tournament data) so we don't
# need to carry around tournament data as much. (might eventually be replaced
# with something like S3)
class RawFile(orm.Document):
    collection_name = 'raw_files'
    fields = [('id', orm.ObjectIDField(required=True, load_from=MONGO_ID_SELECTOR,
                                       dump_to=MONGO_ID_SELECTOR)),
              ('data', orm.StringField())]

class Ranking(orm.Document):
    collection_name = 'rankings'
    fields = [('id', orm.ObjectIDField(required=True, load_from=MONGO_ID_SELECTOR,
                                       dump_to=MONGO_ID_SELECTOR)),
              ('region', orm.StringField(required=True)),
              ('tournaments', orm.ListField(orm.ObjectIDField())),
              ('time', orm.DateTimeField()),
              ('ranking', orm.ListField(orm.DocumentField(RankingEntry)))]

class Region(orm.Document):
    collection_name = 'regions'
    fields = [('id', orm.StringField(required=True, load_from=MONGO_ID_SELECTOR,
                                     dump_to=MONGO_ID_SELECTOR)),
              ('display_name', orm.StringField(required=True)),
              ('ranking_num_tourneys_attended', orm.IntField(required=True, default=2)),
              ('ranking_activity_day_limit', orm.IntField(required=True, default=60)),
              ('tournament_qualified_day_limit', orm.IntField(required=True, default=999))]


class User(orm.Document):
    collection_name = 'users'
    fields = [('id', orm.StringField(required=True, load_from=MONGO_ID_SELECTOR,
                                     dump_to=MONGO_ID_SELECTOR)),
              ('username', orm.StringField(required=True)),
              ('salt', orm.StringField(required=True)),
              ('hashed_password', orm.StringField(required=True)),
              ('admin_regions', orm.ListField(orm.StringField()))]


class Merge(orm.Document):
    collection_name = 'merges'
    fields = [('id', orm.ObjectIDField(required=True, load_from=MONGO_ID_SELECTOR,
                                       dump_to=MONGO_ID_SELECTOR)),
              ('requester_user_id', orm.StringField()),
              ('source_player_obj_id', orm.ObjectIDField(required=True)),
              ('target_player_obj_id', orm.ObjectIDField(required=True)),
              ('time', orm.DateTimeField())]

    def validate_document(self):
        if self.source_player_obj_id == self.target_player_obj_id:
            return False, "source and target must be different"

        return True, None


class Session(orm.Document):
    collection_name = 'sessions'
    fields = [('session_id', orm.StringField(required=True)),
              ('user_id', orm.StringField(required=True))]

