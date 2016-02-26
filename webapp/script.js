var app = angular.module('myApp', ['ngRoute', 'ui.bootstrap', 'angulartics', 'angulartics.google.analytics', 'facebook']);

var dev = false;
if (dev) {
    var hostname = 'http://localhost:3000/';
}
else {
    var hostname = 'http://192.168.111.222/api/'; //whensgarpr.gg:3000
}

app.directive('onReadFile', function ($parse) {
    return {
        restrict: 'A',
        scope: false,
        link: function(scope, element, attrs) {
            var fn = $parse(attrs.onReadFile);

            element.on('change', function(onChangeEvent) {
                var reader = new FileReader();

                reader.onload = function(onLoadEvent) {
                    scope.$apply(function() {
                        fn(scope, {$fileContent:onLoadEvent.target.result});
                    });
                };

                reader.readAsText((onChangeEvent.srcElement || onChangeEvent.target).files[0]);
            });
        }
    };
});

app.service('RegionService', function ($http, PlayerService, TournamentService, RankingsService, SessionService) {
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
            return this.regions.filter(function(element) {
                return element.id == regionId;
            })[0].display_name;
        },
        populateDataForCurrentRegion: function() {
            $http.get(hostname + this.region.id + '/players').
                success(function(data) {
                    PlayerService.playerList = data;
                });

            SessionService.authenticatedGet(hostname + this.region.id + '/tournaments?includePending=true',
                function(data) {
                    TournamentService.tournamentList = data.tournaments.reverse();
                });

            $http.get(hostname + this.region.id + '/rankings').
                success(function(data) {
                    RankingsService.rankingsList = data;
                });
        }
    };

    service.regionsPromise.success(function(data) {
        service.regions = data.regions;
    });

    return service;
});

app.service('PlayerService', function($http) {
    var service = {
        playerList: null,
        getPlayerIdFromName: function (name) {
            for (i = 0; i < this.playerList.players.length; i++) {
                p = this.playerList.players[i]
                if (p.name == name) {
                    return p.id;
                }
            }
            return null;
        },
        getPlayerListFromQuery: function(query, filter_fn) {
            // region doesn't matter here, so we hardcode norcal
            url = hostname + 'norcal/players';
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
            });
        }
    };
    return service;
});

app.service('TournamentService', function() {
    var service = {
        tournamentList: null
    };
    return service;
});

app.service('RankingsService', function() {
    var service = {
        rankingsList: null
    };
    return service;
});

app.service('SessionService', function($http) {
    var service ={
        loggedIn: false,
        userInfo: null,
        authenticatedGet: function(url, successCallback) {
            config = {
                "headers": { 
                    "withCredentials": true, 
                    "Access-Control-Allow-Credentials": true
                }
            };
            $http.get(url, config).success(successCallback)
        },
        authenticatedPost: function(url, data, successCallback, failureCallback) {
            config = {
                "headers": { 
                    "withCredentials": true, 
                    "Access-Control-Allow-Credentials": true
                }
            };
            $http.post(url, data, config).success(successCallback).error(failureCallback);
        },
        authenticatedPut: function(url, successCallback, data, failureCallback) {
            if (data === undefined) {
                data = {};
            }
            config = {
                "headers": { 
                    "withCredentials": true, 
                    "Access-Control-Allow-Credentials": true
                }
            };
            if (failureCallback === undefined) {
                failureCallback = function(data) {}            
            }
            $http.put(url, data, config).success(successCallback).error(failureCallback);
        },
        authenticatedDelete: function(url, successCallback) {
            config = {
                "headers": { 
                    "withCredentials": true, 
                    "Access-Control-Allow-Credentials": true
                }
            };
            $http.delete(url, config).success(successCallback);
        },
        isAdmin: function() {
            if (!this.loggedIn) {
                return false;
            }
            else {
                return this.userInfo.admin_regions.length > 0
            }
        },
        isAdminForRegion: function(regionId) {
            if (!this.loggedIn) {
                return false;
            }
            else {
                return this.userInfo.admin_regions.indexOf(regionId) > -1;
            }
        },
        getAdminRegions: function() {
            return this.userInfo.admin_regions
        }
    };

    return service;
});

app.config(function ($httpProvider) {
    $httpProvider.defaults.withCredentials = true;
    $httpProvider.defaults.useXDomain = true;
    $httpProvider.defaults.headers.common = 'Content-Type: application/json';
    delete $httpProvider.defaults.headers.common['X-Requested-With'];
    //rest of route code
});

app.config(['$routeProvider', function($routeProvider) {
    $routeProvider.when('/:region/rankings', {
        templateUrl: 'rankings.html',
        controller: 'RankingsController',
        activeTab: 'rankings'
    }).
    when('/:region/players', {
        templateUrl: 'players.html',
        controller: 'PlayersController',
        activeTab: 'players'
    }).
    when('/:region/players/:playerId', {
        templateUrl: 'player_detail.html',
        controller: 'PlayerDetailController',
        activeTab: 'players'
    }).
    when('/:region/tournaments', {
        templateUrl: 'tournaments.html',
        controller: 'TournamentsController',
        activeTab: 'tournaments'
    }).
    when('/:region/tournaments/:tournamentId', {
        templateUrl: 'tournament_detail.html',
        controller: 'TournamentDetailController',
        activeTab: 'tournaments'
    }).
    when('/:region/headtohead', {
        templateUrl: 'headtohead.html',
        controller: 'HeadToHeadController',
        activeTab: 'headtohead'
    }).
    when('/about', {
        templateUrl: 'about.html',
        activeTab: 'about'
    }).
    otherwise({
        redirectTo: '/norcal/rankings'
    });
}]);

app.controller("AuthenticationController", function($scope, $modal, Facebook, SessionService, RegionService) {
    $scope.sessionService = SessionService;
    $scope.regionService = RegionService;
    $scope.postParams = {};
    $scope.errorTxt = "";

    $scope.handleAuthResponse = function(response, status, headers, bleh) {
        console.log(response)
        if (response.status == 'connected') {
            $scope.errorTxt = "";
            $scope.getSessionInfo(function() {
                $scope.closeLoginModal();
            });
        }
        else {
            $scope.sessionService.loggedIn = false;
            $scope.sessionService.userInfo = null;
            $scope.errorTxt = "Login Failed";
        }
    };

    $scope.getSessionInfo = function(callback) {
        $scope.sessionService.authenticatedGet(hostname + 'users/session',
            function(data) {
                console.log("session data")
                console.log(data)
                $scope.sessionService.loggedIn = true;
                $scope.sessionService.userInfo = data;
                $scope.regionService.populateDataForCurrentRegion();
                if (callback) { callback(); }
            }
        );
    }

    $scope.closeLoginModal = function() {
        $scope.modalInstance.close()
    };

    $scope.openLoginModal = function() {
        $scope.modalInstance = $modal.open({
            templateUrl: 'login_modal.html',
            scope: $scope,
            size: 'lg'
        });
    };

    $scope.login = function() {
        console.log("logging in user")
        console.log($scope.postParams)
        url = hostname + 'users/session'
        $scope.sessionService.authenticatedPut(url, $scope.handleAuthResponse, $scope.postParams,
            $scope.handleAuthResponse);
    };

    $scope.logout = function() {
        console.log("logging out user")
        url = hostname + 'users/session'
        $scope.sessionService.authenticatedDelete(url, $scope.handleAuthResponse, $scope.postParams,
            $scope.handleAuthResponse);
    };

    // Initial login
    $scope.getSessionInfo();
});

app.controller("NavbarController", function($scope, $route, $location, RegionService, PlayerService) {
    $scope.regionService = RegionService;
    $scope.playerService = PlayerService;
    $scope.$route = $route;

    $scope.selectedPlayer = null;

    $scope.playerSelected = function($item) {
        $location.path($scope.regionService.region.id + '/players/' + $item.id);
        $scope.selectedPlayer = null;
    };
});

app.controller("RankingsController", function($scope, $routeParams, $modal, RegionService, RankingsService, SessionService) {
    RegionService.setRegion($routeParams.region);
    $scope.regionService = RegionService;
    $scope.rankingsService = RankingsService
    $scope.sessionService = SessionService

    $scope.modalInstance = null;
    $scope.disableButtons = false;

    $scope.prompt = function() {
        $scope.modalInstance = $modal.open({
            templateUrl: 'generate_rankings_prompt_modal.html',
            scope: $scope,
            size: 'lg'
        });
    };

    $scope.confirm = function() {
        $scope.disableButtons = true;
        url = hostname + $routeParams.region + '/rankings';
        successCallback = function(data) {
            $scope.rankingsService.rankingsList = data;
            $scope.modalInstance.close();
        };

        $scope.sessionService.authenticatedPost(url, {}, successCallback, angular.noop);
    };

    $scope.cancel = function() {
        $scope.modalInstance.close();
    };
});

app.controller("TournamentsController", function($scope, $routeParams, $modal, RegionService, TournamentService, SessionService) {
    RegionService.setRegion($routeParams.region);
    $scope.regionService = RegionService;
    $scope.tournamentService = TournamentService;
    $scope.sessionService = SessionService;

    $scope.modalInstance = null;
    $scope.disableButtons = false;
    $scope.errorMessage = false;

    $scope.postParams = {};

    $scope.open = function() {
        $scope.disableButtons = false;
        $scope.modalInstance = $modal.open({
            templateUrl: 'import_tournament_modal.html',
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

        url = hostname + $routeParams.region + '/tournaments';
        successCallback = function(data) {
            // TODO don't need to populate everything, just tournaments
            $scope.regionService.populateDataForCurrentRegion()
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
});

app.controller("TournamentDetailController", function($scope, $routeParams, $http, $modal, RegionService, SessionService, PlayerService) {
    RegionService.setRegion($routeParams.region);
    $scope.regionService = RegionService;
    $scope.sessionService = SessionService;
    $scope.playerService = PlayerService;

    $scope.tournament = null;
    $scope.tournamentId = $routeParams.tournamentId
    $scope.isPendingTournament = false;
    $scope.modalInstance = null;
    $scope.playerData = {}
    $scope.playerCheckboxState = {};

    $scope.openRegionModal = function() {
        $scope.modalInstance = $modal.open({
            templateUrl: 'tournament_region_modal.html',
            scope: $scope,
            size: 'lg'
        });
        $scope.tournamentRegionCheckbox = {}
    };

    $scope.closeRegionModal = function() {
        $scope.modalInstance.close()
    };

    $scope.openSubmitPendingTournamentModal = function() {
        $scope.modalInstance = $modal.open({
            templateUrl: 'submit_pending_tournament_confirmation_modal.html',
            scope: $scope,
            size: 'lg'
        });
        $scope.tournamentRegionCheckbox = {}
    };

    $scope.closeSubmitPendingTournamentModal = function() {
        $scope.modalInstance.close()
    };

    $scope.submitPendingTournament = function() {
        url = hostname + $routeParams.region + '/tournaments/' + $scope.tournamentId + '/finalize';
        successCallback = function(data) {
            window.location.reload();
        };
        $scope.sessionService.authenticatedPost(url, {}, successCallback);
    };

    $scope.isTournamentInRegion = function(regionId) {
        return $scope.tournament.regions.indexOf(regionId) > -1
    };

    $scope.onCheckboxChange = function(regionId) {
        url = hostname + $routeParams.region + '/tournaments/' + $scope.tournamentId + '/region/' + regionId;
        successCallback = function(data) {
            $scope.tournament = data;
        };

        if ($scope.tournamentRegionCheckbox[regionId]) {
            $scope.sessionService.authenticatedPut(url, successCallback);
        }
        else {
            $scope.sessionService.authenticatedDelete(url, successCallback);
        }
    };

    $scope.onPlayerCheckboxChange = function(playerAlias) {
        $scope.put_tournament_from_ui()
    };

    $scope.playerSelected = function(playerAlias, $item) {
        $scope.put_tournament_from_ui()
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

        return retString
    };

    $scope.update_alias_map_from_ui = function() {
        var alias_map = {}
        for (var player in $scope.playerCheckboxState) {
            if ($scope.playerCheckboxState[player] === true) {
                alias_map[player] = null;
                delete $scope.playerData[player];
            }
        }
        for (var player in $scope.playerData){
            alias_map[player] = $scope.playerData[player].id
        }
        $scope.tournament.alias_to_id_map = alias_map;
    };

    $scope.put_tournament_from_ui = function() {
        $scope.update_alias_map_from_ui()
        console.log($scope.tournament.alias_to_id_map);
        url = hostname + $routeParams.region + '/pending_tournaments/' + $scope.tournamentId;
        $scope.sessionService.authenticatedPut(url, $scope.updateData, $scope.tournament);
    }

    $scope.updateData = function(data) {
        $scope.tournament = data;
        if ($scope.tournament.hasOwnProperty('alias_to_id_map')) {
            $scope.isPendingTournament = true;

            // load individual player detail
            for (var player in $scope.tournament.alias_to_id_map) {
                var id = $scope.tournament.alias_to_id_map[player];
                if (id != null) {
                    $scope.playerCheckboxState[player] = false;
                    (function(clsplayer, clsid) {
                        $http.get(hostname + $routeParams.region + '/players/' + clsid).
                            success(function(data) {
                                $scope.playerData[clsplayer] = data;
                            })
                    })(player, id);
                }
                else {
                    $scope.playerCheckboxState[player] = true;
                }
            }
        }
    }
    // TODO submission checks! check to make sure everything in $scope.playerData is an object (not a string. string = partially typed box)

    $http.get(hostname + $routeParams.region + '/tournaments/' + $scope.tournamentId).
        success($scope.updateData);
});

app.controller("PlayersController", function($scope, $routeParams, RegionService, PlayerService) {
    RegionService.setRegion($routeParams.region);
    $scope.regionService = RegionService;
    $scope.playerService = PlayerService;
});

app.controller("PlayerDetailController", function($scope, $http, $routeParams, $modal, RegionService, SessionService, PlayerService) {
    RegionService.setRegion($routeParams.region);
    $scope.regionService = RegionService;
    $scope.sessionService = SessionService;
    $scope.playerService = PlayerService;

    $scope.playerId = $routeParams.playerId;
    $scope.mergePlayer = "";
    $scope.modalInstance = null;

    $scope.open = function() {
        $scope.modalInstance = $modal.open({
            templateUrl: 'player_region_modal.html',
            scope: $scope,
            size: 'lg'
        });
        $scope.playerRegionCheckbox = {}
    };

    $scope.close = function() {
        $scope.modalInstance.close()
    };

    $scope.isPlayerInRegion = function(regionId) {
        return $scope.player.regions.indexOf(regionId) > -1
    };

    $scope.onCheckboxChange = function(regionId) {
        url = hostname + $routeParams.region + '/players/' + $scope.playerId + '/region/' + regionId;
        successCallback = function(data) {
            $scope.player = data;
        };

        if ($scope.playerRegionCheckbox[regionId]) {
            $scope.sessionService.authenticatedPut(url, successCallback);
        }
        else {
            $scope.sessionService.authenticatedDelete(url, successCallback);
        }
    };

    $scope.submitMerge = function() {
        if ($scope.mergePlayer.id === undefined) {
            alert("You must select a player to merge");
            return;
        }
        url = hostname + $routeParams.region + '/merges';
        params = {"base_player_id": $scope.playerId, "to_be_merged_player_id": $scope.mergePlayer.id};
        console.log(params);
        $scope.sessionService.authenticatedPost(url, params, 
            function() {alert("Your merge request has been sent. A site admin will process it soon.")}, 
            function() {alert("Your merge request didn't go through. Please try again later.")});
    };

    $scope.getMergePlayers = function(viewValue) {
        players = $scope.playerService.getPlayerListFromQuery(viewValue, 
            function(player) {return player.id != $scope.playerId});
        return players;
    }

    $http.get(hostname + $routeParams.region + '/players/' + $routeParams.playerId).
        success(function(data) {
            $scope.player = data;
        });

    $http.get(hostname + $routeParams.region + '/matches/' + $routeParams.playerId).
        success(function(data) {
            $scope.matches = data.matches.reverse();
        });

});

app.controller("HeadToHeadController", function($scope, $http, $routeParams, RegionService, PlayerService) {
    RegionService.setRegion($routeParams.region);
    $scope.regionService = RegionService;
    $scope.playerService = PlayerService;
    $scope.player1 = null;
    $scope.player2 = null;
    $scope.wins = 0;
    $scope.losses = 0;

    $scope.onChange = function() {
        if ($scope.player1 != null && $scope.player2 != null) {
            $http.get(hostname + $routeParams.region + 
                '/matches/' + $scope.player1.id + '?opponent=' + $scope.player2.id).
                success(function(data) {
                    $scope.playerName = $scope.player1.name;
                    $scope.opponentName = $scope.player2.name;
                    $scope.matches = data.matches.reverse();
                    $scope.wins = data.wins;
                    $scope.losses = data.losses;
                });
        }
    };
});

