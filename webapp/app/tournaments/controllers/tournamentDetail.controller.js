angular.module('app.tournaments').controller("TournamentDetailController", function($scope, $routeParams, $http, $modal, RegionService, SessionService, PlayerService) {
    RegionService.setRegion($routeParams.region);
    $scope.regionService = RegionService;
    $scope.sessionService = SessionService;
    $scope.playerService = PlayerService;

    $scope.modalInstance = null;
    $scope.disableButtons = false;
    $scope.errorMessage = false;

    $scope.tournament = null;
    $scope.tournamentId = $routeParams.tournamentId
    $scope.isPendingTournament = false;
    $scope.aliasMap = {};
    $scope.playerData = {};
    $scope.playerCheckboxState = {};

    $scope.matchCheckbox = null;
    $scope.addMatchWinner = '';
    $scope.addMatchLoser = '';

    $scope.playerToRemove = null;
    $scope.playerToAdd = null;

    $scope.closeModal = function() {
        $scope.modalInstance.close()
    };

    $scope.openDetailsModal = function() {
        $scope.modalInstance = $modal.open({
            templateUrl: 'app/tournaments/views/tournament_details_modal.html',
            scope: $scope,
            size: 'lg'
        });
        $scope.postParams = {name: $scope.tournament.name,
                             date: $scope.tournament.date,
                             pending: $scope.isPendingTournament};
        $scope.tournamentRegionCheckbox = {};

        $scope.sessionService.getAdminRegions().forEach(
            function(regionId){
                if($scope.isTournamentInRegion(regionId)){
                    $scope.tournamentRegionCheckbox[regionId] = "IN_REGION";
                }else{
                    $scope.tournamentRegionCheckbox[regionId] = "NOT_IN_REGION";
                }
            });

        $scope.disableButtons = false;
        $scope.errorMessage = false;
    };

    $scope.closeDetailsModal = function() {
        $scope.modalInstance.close()
    };

    $scope.openAddMatchModal = function(){
        $scope.modalInstance = $modal.open({
            templateUrl: 'app/tournaments/views/tournament_add_match_modal.html',
            scope: $scope,
            size: 'lg'
        });
    };

    $scope.addMatchToTournament = function(winnerId, loserId){

        var putParams = {
            winner_id: winnerId,
            loser_id: loserId
        }

        url = hostname + $routeParams.region + '/tournaments/' + $scope.tournamentId + '/addMatch';

        $scope.sessionService.authenticatedPut(url, putParams,
            (data) => {
                //ON SUCCESS RELOAD THE PAGE
                alert('Added Match Successfully!');
                location.reload();
            },
            (err) => {
                //ON ERROR INDICATE TO THE USER
                alert('Match Addition Failed. Please try again. ' +
                      '\nPlease check that both Winner and Loser are filled in' +
                      '\nIf the problem persists please contact the Admins');
            })
    }

    $scope.updateTournamentDetails = function() {
        url = hostname + $routeParams.region + '/tournaments/' + $scope.tournamentId;
        $scope.disableButtons = true;

        tournamentInRegion = function(regionId){
            return $scope.tournamentRegionCheckbox[regionId]!=="NOT_IN_REGION";
        };

        $scope.postParams['regions'] = $scope.sessionService.getAdminRegions().filter(tournamentInRegion);

        successCallback = function(data) {
            $scope.tournament = data;
            $scope.closeDetailsModal();
        };

        failureCallback = function(data) {
            $scope.disableButtons = false;
            $scope.errorMessage = true;
        };

        $scope.sessionService.authenticatedPut(url, $scope.postParams, successCallback, failureCallback);

        return;
    };

    $scope.openSubmitPendingTournamentModal = function() {
        $scope.modalInstance = $modal.open({
            templateUrl: 'app/tournaments/views/submit_pending_tournament_confirmation_modal.html',
            scope: $scope,
            size: 'lg'
        });
    };

    $scope.closeSubmitPendingTournamentModal = function() {
        $scope.modalInstance.close()
    };

    $scope.submitPendingTournament = function() {
        $scope.putTournamentFromUI();
        url = hostname + $routeParams.region + '/tournaments/' + $scope.tournamentId + '/finalize';
        successCallback = function(data) {
            window.location.reload();
        };
        $scope.sessionService.authenticatedPost(url, {}, successCallback);
    };

    $scope.isTournamentInRegion = function(regionId) {
        return $scope.tournament.regions.indexOf(regionId) > -1
    };

    $scope.onPlayerCheckboxChange = function(playerAlias) {
        $scope.playerData[playerAlias] = null;
    };

    $scope.playerSelected = function(playerAlias, $item) {
        $scope.playerCheckboxState[playerAlias] = false;
    };

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

    $scope.updateAliasMapFromUI = function() {
        var aliasMap = {}
        for (var player in $scope.playerCheckboxState) {
            if ($scope.playerCheckboxState[player] === true) {
                aliasMap[player] = null;
                delete $scope.playerData[player];
            }
        }
        for (var player in $scope.playerData){
            aliasMap[player] = $scope.playerData[player].id
        }
        $scope.aliasMap = aliasMap;
    };

    $scope.putTournamentFromUI = function() {
        $scope.updateAliasMapFromUI();

        // listify the current alias_to_id_map so angular
        // does not strip certain properties
        $scope.tournament.alias_to_id_map = [];
        for(var alias in $scope.aliasMap){
            var id = $scope.aliasMap[alias];
            $scope.tournament.alias_to_id_map.push(
                { "player_alias": alias,
                  "player_id": id
                });
        }

        url = hostname + $routeParams.region + '/pending_tournaments/' + $scope.tournamentId;
        $scope.sessionService.authenticatedPut(url, $scope.tournament, $scope.updateData);
    }

    $scope.updateData = function(data) {
        $scope.tournament = data;
        if ($scope.tournament.hasOwnProperty('alias_to_id_map')) {
            $scope.isPendingTournament = true;

            // load individual player detail
            $scope.tournament.alias_to_id_map.forEach(
                function(aliasItem){
                    var player = aliasItem["player_alias"];
                    var id = aliasItem["player_id"];
                    $scope.aliasMap[player] = id;
                    if(id != null){
                        $scope.playerCheckboxState[player] = false;

                        // TODO: this generates tons of requests. we should be
                        // able to do this with one giant request.
                        $http.get(hostname + $routeParams.region + '/players/' + id).
                            success(function(data) {
                                $scope.playerService.addTypeaheadDisplayText(data);
                                $scope.playerData[player] = data;
                            });

                    }else{
                        $scope.playerCheckboxState[player] = true;
                    }
                });
        }
    }
    // TODO submission checks! check to make sure everything in $scope.playerData is an object (not a string. string = partially typed box)

    $scope.isMatchCurrentlyExcluded = function(match){
        var excluded = match.excluded;

        if(excluded){
            //var htmlId = 'exclude_set_checkbox_' + match.match_id;
            var winnerHtmlId = 'winner_' + match.match_id;
            var loserHtmlId = 'loser_' + match.match_id;

            //var matchCheckbox = document.getElementById(htmlId);
            var winnerElement = document.getElementById(winnerHtmlId);
            var loserElement = document.getElementById(loserHtmlId);

            winnerElement.className = 'excluded';
            loserElement.className = 'excluded';
        }

        return excluded;
    }

    $scope.changeMatchExclusion = function(match){
        var htmlId = 'exclude_set_checkbox_' + match.match_id;
        var winnerHtmlId = 'winner_' + match.match_id;
        var loserHtmlId = 'loser_' + match.match_id;

        var matchCheckbox = document.getElementById(htmlId);
        var winnerElement = document.getElementById(winnerHtmlId);
        var loserElement = document.getElementById(loserHtmlId);

        postParams = {
            tournament_id : $scope.tournamentId,
            match_id : match.match_id,
            excluded_tf : matchCheckbox.checked
        }

        url = hostname + $routeParams.region + '/tournaments/' + $scope.tournamentId + '/excludeMatch';

        if(matchCheckbox.checked){
            //API CALL HERE
            $scope.sessionService.authenticatedPost(url, postParams,
                (data) => {
                    // TODO gray out the row
                    winnerElement.className = 'excluded';
                    loserElement.className = 'excluded';
                    return false;
               },
                () => {
                    excludeFailure();
                    matchCheckbox.checked = false;
               });
        }
        else{
            // API CALL HERE
            $scope.sessionService.authenticatedPost(url, postParams,
                (data) => {
                    // TODO ungray the row
                    winnerElement.className = 'success';
                    loserElement.className = 'danger';
                    alert('Match Included Successfully!');
                    return false;
                },
                () => {
                    excludeFailure();
                    matchCheckbox.checked = true;
               });
        }
    };

    function excludeFailure(){
        alert('Failure to exclude set. Please try again');
    };

    $scope.swapWinnerLoser = function(match){
        if( confirm('Are you sure you want to swap ' + match.winner_name + ' (W) with ' + match.loser_name + ' (L)?' )){
            var winnerHtmlId = 'winner_' + match.match_id;
            var loserHtmlId = 'loser_' + match.match_id;

            var winnerElement = document.getElementById(winnerHtmlId);
            var loserElement = document.getElementById(loserHtmlId);

            var winnerAnchor = winnerElement.getElementsByTagName('a');
            var winnerLink = winnerAnchor[0].href;
            var loserAnchor = loserElement.getElementsByTagName('a');
            var loserLink = loserAnchor[0].href;

            var postParams = {
                tournament_id : $scope.tournamentId,
                match_id : match.match_id
            }
            url = hostname + $routeParams.region + '/tournaments/' + $scope.tournamentId + '/swapWinnerLoser';

            $scope.sessionService.authenticatedPost(url, postParams,
                (data) => {
                    // TODO simply switch the names in the Winner-Loser boxes
                    winnerAnchor[0].innerHTML = match.loser_name;
                    winnerAnchor[0].href = loserLink;

                    loserAnchor[0].innerHTML = match.winner_name;
                    loserAnchor[0].href = winnerLink;

                    alert('Swap was successful! (If people did not swap on table, please refresh the page)');
                    return;
                },
                (err) => {
                    // TODO alert of a failure and exit
                    alert('Failed to swap Winner-Loser');
                    return;
               });
        }

    };

    $scope.openDeleteTournamentModal = function(tournamentId) {
        $scope.modalInstance = $modal.open({
            templateUrl: 'app/tournaments/views/delete_tournament_modal.html',
            scope: $scope,
            size: 'lg'
        });
        $scope.tournamentId = tournamentId;
    };

    $scope.deleteTournament = function() {
        url = hostname + $routeParams.region + '/tournaments/' + $scope.tournamentId;
        successCallback = function(data) {
            window.location.href = "#/" + $routeParams.region + '/tournaments' ;
            window.location.reload();
        };
        $scope.sessionService.authenticatedDelete(url, successCallback);
    };

    $scope.openReplacePlayerModal = function(playerToRemove) {
        $scope.modalInstance = $modal.open({
            templateUrl: 'app/tournaments/views/replace_player_modal.html',
            scope: $scope,
            size: 'lg'
        });
        $scope.playerToRemove = playerToRemove;
        $scope.playerToAdd = null;
    };

    $scope.replacePlayer = function(playerToRemove, playerToAdd) {
        $scope.disableButtons = true;

        postParams = {
            players: [],
            matches: [],
        }

        $scope.tournament.players.forEach(
            function(player) {
                if (player.id === playerToRemove.id) {
                    var p = {
                        id: playerToAdd.id,
                        name: playerToAdd.name
                    };
                } else {
                    var p = player;
                }

                postParams.players.push(p);
        });

        $scope.tournament.matches.forEach(
            function(match) {
                if (match.loser_id === playerToRemove.id) {
                    var m = {
                        match_id: match.match_id,
                        excluded: match.excluded,
                        loser_id: playerToAdd.id,
                        loser_name: playerToAdd.name,
                        winner_id: match.winner_id,
                        winner_name: match.winner_name,
                    };
                } else if (match.winner_id === playerToRemove.id) {
                    var m = {
                        match_id: match.match_id,
                        excluded: match.excluded,
                        loser_id: match.loser_id,
                        loser_name: match.loser_name,
                        winner_id: playerToAdd.id,
                        winner_name: playerToAdd.name,
                    };
                } else {
                    var m = match;
                }

                postParams.matches.push(m);
        });

        url = hostname + $routeParams.region + '/tournaments/' + $scope.tournamentId;
        $scope.sessionService.authenticatedPut(
            url, postParams,
            function(data) {
                $scope.tournament = data;
                $scope.closeModal();
            },
            function(data) {
                $scope.disableButtons = false;
            });
    };


    $http.get(hostname + $routeParams.region + '/tournaments/' + $scope.tournamentId).
        success($scope.updateData);
});
