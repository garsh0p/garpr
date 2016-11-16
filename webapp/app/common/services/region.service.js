angular.module('app.common').service('RegionService', function ($http, PlayerService, TournamentService, RankingsService, MergeService, SessionService) {
    var service = {
        regionsPromise: $http.get(hostname + 'regions'),
        regions: [],
        region: '',
        setRegion: function (newRegionId) {
            if (!this.region || newRegionId != this.region.id) {
                this.regionsPromise.then(function(response) {
                    service.region = service.getRegionFromRegionId(newRegionId);
                    PlayerService.playerList = null;
                    TournamentService.tournamentList = null;
                    RankingsService.rankingsList = null;
                    MergeService.mergeList = null;
                    service.populateDataForCurrentRegion();
                });
            }
        },
        getRegionFromRegionId: function(regionId) {
            return this.regions.filter(function(element) {
                return element.id == regionId;
            })[0];
        },
        getRegionDisplayNameFromRegionId: function(regionId) {
            var region = this.getRegionFromRegionId(regionId);
            if(region!=null){
                return region.display_name;
            }else{
                return "Invalid Region";
            }
        },
        populateDataForCurrentRegion: function() {
            // get all players instead of just players in region
            var curRegion = this.region;
            $http.get(hostname + this.region.id + '/players?all=true').
                success(function(data) {
                    PlayerService.allPlayerList = data;

                    // filter players for this region
                    PlayerService.playerList = {
                        'players': data.players.filter(
                            function(player){
                                return player.regions.some(
                                    function(region){
                                        if(region==null) return false;
                                        return region === curRegion.id;
                                    });
                            })
                    };
                });

            SessionService.authenticatedGet(hostname + this.region.id + '/tournaments?includePending=true',
                function(data) {
                    TournamentService.tournamentList = data.tournaments.reverse();
                });

            $http.get(hostname + this.region.id + '/rankings').
                success(function(data) {
                    RankingsService.rankingsList = data;
                });

            SessionService.authenticatedGet(hostname + this.region.id + '/merges',
                function(data) {
                    MergeService.mergeList = data;
                });
        }
    };

    service.regionsPromise.success(function(data) {
        service.regions = data.regions;
    });

    service.display_regions = [{"id": "newjersey", "display_name": "New Jersey"},
                               {"id": "nyc", "display_name": "NYC Metro Area"},
                               {"id": "li", "display_name": "Long Island"},
                               {"id": "chicago", "display_name": "Chicago"},
                               {"id": "georgia", "display_name": "Georgia"},
                               {"id": "alabama", "display_name": "Alabama"},
                               {"id": "tennessee", "display_name": "Tennessee"},
                               {"id": "southcarolina", "display_name": "South Carolina"}];
    return service;
});