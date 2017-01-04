angular.module('app.players').service('PlayerService', function($http) {
    var service = {
        playerList: null,
        allPlayerList:null,
        getPlayerIdFromName: function (name) {
            for (i = 0; i < this.playerList.players.length; i++) {
                p = this.playerList.players[i]
                if (p.name == name) {
                    return p.id;
                }
            }
            return null;
        },
        addTypeaheadDisplayText: function(player){
            player.typeahead = player.name.toLowerCase();
            try{ 
                var minSig = 100;
                var mainRegion = "";
                player.regions.forEach(function(region)
                {
                    if(player.ratings[region] !== undefined && player.ratings[region].sigma < minSig)
                    {
                        minSig = player.ratings[region].sigma;
                        mainRegion = region;
                    }
                });
                if(mainRegion != "")
                    player.typeahead = player.name.toString() + ' ~ ' + mainRegion;
                else
                    player.typeahead = player.name.toString() + ' ~ ' + player.regions[0].toString();
            } catch(err){
                /* FAIL GRACEFULLY */
            }
        },
        // local port of _player_matches_query from backend
        // now returns matchQuality instead of just a boolean
        // if match_quality > 0, consider it a match
        playerMatchesQuery: function(player, query) {
            var playerName = player.name.toLowerCase();
            var query = query.toLowerCase();

            if(playerName === query){
                return 10;
            }

            var rex = /\.|\|| /;
            var tokens = playerName.split(rex);
            for(var i=0;i<tokens.length;i++){
                var token = tokens[i];
                if(token.length > 0){
                    if(token.startsWith(query)){
                        return 5;
                    }
                }
            }

            if(query.length >= 3 && playerName.includes(query)){
                return 1;
            }

            // no match
            return 0;
        },
        getPlayerListFromQuery: function(query, filter_fn) {
            var TYPEAHEAD_PLAYER_LIMIT = 20;
            var filteredPlayers = [];
            for (var i = 0; i < this.allPlayerList.players.length; i++) {
                var curPlayer = this.allPlayerList.players[i];

                if(filter_fn == null || filter_fn(curPlayer)){
                    var matchQuality = this.playerMatchesQuery(curPlayer, query);
                    this.addTypeaheadDisplayText(curPlayer);
                    if(matchQuality > 0){
                        filteredPlayers.push({'player': curPlayer,
                                              'quality': matchQuality});
                    }
                }
            }

            filteredPlayers.sort(function(p1, p2){
                if(p1.quality < p2.quality) return 1;
                else if(p1.quality > p2.quality) return -1;
                else return 0;
            });

            filteredPlayers = filteredPlayers.slice(0, TYPEAHEAD_PLAYER_LIMIT);

            filteredPlayers = filteredPlayers.map(p => p.player);

            return filteredPlayers;

            // let's not send so many get requests
            /*
            url = hostname + defaultRegion + '/players';
            params = {
                params: {
                    query: query
                }
            }

            return $http.get(url, params).then(function(response) {
                players = response.data.players;
                if (filter_fn != undefined) {
                    filtered_players = []
                    for (var i = 0; i < players.length; i++) {
                        if (filter_fn(players[i])) {
                            filtered_players.push(players[i])
                        }
                    }
                    players = filtered_players;
                }
                return players;
            });*/
        }
    };
    return service;
});