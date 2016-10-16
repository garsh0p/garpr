angular.module('app.tools').controller("SeedController", function($scope, $http, $routeParams, $modal,SessionService, RegionService, PlayerService, RankingsService) {
    RegionService.setRegion($routeParams.region);
    $scope.regionService = RegionService;
    $scope.playerService = PlayerService;
    $scope.rankingsService = RankingsService;
    $scope.sessionService = SessionService;

    $scope.seeding = {
        players:[]
    };

    $scope.addPlayerRow = function()
    {
        $scope.seeding.players.push(
        {
            seed: $scope.seeding.players.length+1,
            tag : "",
            new : true
        });
    }

    $scope.playerSelected = function(player, item)
    {
        /**
        -1: no rating
        0: current in-region rating
        1: inactive, in-region rating
        2: OOR rating (active/inactive)
        **/
        player.ratingType=-1;
        player.regions = item.regions;
        player.tag = item.name;
        player.rating = undefined;
        player.id = item.id;
        player.new = false;
        $scope.rankingsService.rankingsList.ranking.forEach(function(rank)
        {
            if(rank.name == item.name)
            {
                player.rating = rank.rating;
                player.ratingType = 0;
            }
        });

        //use inactive/OOR ranking if available
        if(player.ratingType==-1)
        {
            
            if(item.ratings !== undefined)
            {
                //inactive
                if($scope.rankingsService.rankingsList.region in item.ratings)
                {
                    var ratingObj = item.ratings[$scope.rankingsService.rankingsList.region];
                    player.rating = ratingObj.mu - 3*ratingObj.sigma;
                    player.ratingType=1;
                }
                //OOR
                else
                {
                    for (var first in item.ratings) break;//this is whack
                    if(first !== undefined){
                        player.rating = item.ratings[first].mu;
                        player.oorRanking = first;
                        player.ratingType = 2;
                    }
                }
            }
        }

        $scope.resortSeeding();
    }

    $scope.prompt = function() {
        $scope.modalInstance = $modal.open({
            templateUrl: 'app/tools/seed_tournament/views/import_tournament_modal_challonge_only.html',
            scope: $scope,
            size: 'lg'
        });
    };

    $scope.resortSeeding = function()
    {
        $scope.seeding.players.sort(function(a, b) {
            if(b.rating === undefined)
                return -1;
            else if (a.rating === undefined)
                return 1;
            else
                return b.rating - a.rating;
        });
        $scope.seeding.players.forEach(function(player, index)
        {
            player.seed = index + 1;
        });
    }

     $scope.prettyPrintRegionListForPlayer = function(player) {
        var retString = 'None';
        if (player != null && player.hasOwnProperty('regions')) {
            var regions = player.regions;
            for (i = 0; i < regions.length; i++) {
                r = regions[i];
                if (retString == 'None') {
                    retString = $scope.regionService.getRegionDisplayNameFromRegionId(r);
                }
                else {
                    retString += ', ' + $scope.regionService.getRegionDisplayNameFromRegionId(r);
                }
            }
        }

        return retString;
    };







    $scope.open = function() {
        $scope.disableButtons = false;
        $scope.modalInstance = $modal.open({
            templateUrl: 'app/tools/seed_tournament/views/import_tournament_modal_challonge_only.html',
            scope: $scope,
            size: 'lg'
        });
    };

    $scope.setBracketType = function(bracketType) {
        $scope.postParams = {};
        $scope.postParams.type = bracketType;
        $scope.errorMessage = false;
    };

    $scope.close = function() {
        $scope.modalInstance.close();
    };


    $scope.submit = function() {
        console.log($scope.postParams);
        $scope.disableButtons = true;

        url = hostname + $routeParams.region + '/tournamentseed';
        successCallback = function(data) {
            data.players.forEach(function(player){
            var players = $scope.playerService.getPlayerListFromQuery(player);
            if(players.length > 0)
            {
                $scope.seeding.players.push({'seed':$scope.seeding.players.length, 'tag':""});
                $scope.playerSelected($scope.seeding.players[$scope.seeding.players.length-1], players[0]);
            }
            else
                $scope.seeding.players.push({'seed':$scope.seeding.players.length, 'tag':player, new:true});
           });
            $scope.tournament_name = data.name;
            $scope.close();
        };

        failureCallback = function(data) {
            $scope.disableButtons = false;
            $scope.errorMessage = true;
        };

        $scope.sessionService.authenticatedPost(url, $scope.postParams, successCallback, failureCallback);
    };


     $scope.loadFile = function(fileContents) {
        $scope.postParams.data = fileContents;
    };

    $scope.openDeleteTournamentModal = function(tournamentId) {
        $scope.modalInstance = $modal.open({
            templateUrl: 'app/tools/common/views/delete_tournament_modal.html',
            scope: $scope,
            size: 'lg'
        });
    $scope.tournamentId = tournamentId;
    };

    $scope.isNewPlayer = function(player)
    {
        return player.rating === undefined;
    }

    $scope.setPlayerNew = function(player)
    {
        
        if(player.new)
            player.rating = undefined;

        $scope.resortSeeding();
    }

    $scope.removePlayer = function(seed)
    {
        $scope.seeding.players.splice(seed-1,1);
        $scope.resortSeeding();
    }

    $scope.close = function(){
        $scope.modalInstance.close();
    }
});