# Tournament Import API

##Upload bracket: 
 - `POST /[region]/tournaments/new`
    - Body: Tourney name; Bracket type; Challonge link or (TIO file contents and bracket name)
    - Create `PendingTournament` from relevant `Scraper`; save this in the `pending_tournaments` collection
    - return success

##Merge aliases:
 - `GET /[region]/tournaments/pending/[pending_tournament_id]/player_aliases`
    - return: 
        ```
        {
          id: ObjectId of PendingTournament,
          player_map: { (alias): { suggestions: (list of suggestions), player: (player json) } },
          players_in_region: [] // actually just a list of aliases of players
        }
        ```
 - `POST /[region]/tournaments/pending/[pending_tournament_id]/player_aliases`
    - body: `{ (alias): { player_id: (player_id), is_new: (boolean), out_of_region: (boolean), player_name: (player_name) }`
    - for each unknown player: if new, create new player with given alias. otherwise, merge player.
    - Put all these into a map (`alias -> player id`). Extend this map with known players.
    - Save `alias_to_id_map` into the `PendingTournament` specified by `[pending_tournament_id]`.
    - return success

##Manual cleanup: 
Probably...
  - `DELETE /[region]/tournaments/pending/[tournament_id]/[match_id]`
  - `POST /[region]/player/[player_id]/merge` (body: player to merge with)

##List pending brackets:
 - `GET /[region]/tournaments/pending`

##Finalize:
 - `POST /[region]/tournaments/pending/[pending_tournament_id]/finalize`
    - create a `Tournament` from the `PendingTournament` and `alias_to_id_map`. Save in `tournaments` collection.
    - computes new ranking!
