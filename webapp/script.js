var app = angular.module('myApp', ['ngRoute', 'ui.bootstrap', 'angulartics', 'angulartics.google.analytics', 'facebook']);

var dev = true;
if (dev) {
    var hostname = 'http://garsh0p.no-ip.biz:5101/';
}
else {
    var hostname = 'https://api.garpr.com/';
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
        getPlayerListFromQuery: function(query) {
            // region doesn't matter here, so we hardcode norcal
            url = hostname + 'norcal/players';
            params = {
                params: {
                    query: query
                }
            }

            return $http.get(url, params).then(function(response) {
                return response.data.players;
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
        accessToken: null,
        authenticatedGet: function(url, successCallback) {
            if (this.accessToken != null) {
                config = {
                    headers: {
                        'Authorization': this.accessToken
                    }
                }
                $http.get(url, config).success(successCallback);
            }
            else {
                $http.get(url).success(successCallback);
            }
        },
        authenticatedPost: function(url, data, successCallback, failureCallback) {
            if (this.accessToken != null) {
                config = {
                    headers: {
                        'Authorization': this.accessToken
                    }
                }
                $http.post(url, data, config).success(successCallback).error(failureCallback);
            }
            else {
                $http.post(url, data).success(successCallback).error(failureCallback);
            }
        },
        authenticatedPut: function(url, successCallback) {
            if (this.accessToken != null) {
                config = {
                    headers: {
                        'Authorization': this.accessToken
                    }
                }
                $http.put(url, {}, config).success(successCallback);
            }
            else {
                $http.put(url, {}).success(successCallback);
            }
        },
        authenticatedDelete: function(url, successCallback) {
            if (this.accessToken != null) {
                config = {
                    headers: {
                        'Authorization': this.accessToken
                    }
                }
                $http.delete(url, config).success(successCallback);
            }
            else {
                $http.delete(url).success(successCallback);
            }
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

app.config(function(FacebookProvider) {
    FacebookProvider.init({
        appId: '328340437351153',
        cookie: false
    });
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

app.controller("AuthenticationController", function($scope, Facebook, SessionService, RegionService) {
    $scope.sessionService = SessionService;
    $scope.regionService = RegionService;

    // Monitor the authResponseChange event so we can refresh expired access tokens
    $scope.$on('Facebook:authResponseChange', function(event, response) {
        $scope.handleAuthResponse(response);
    });

    $scope.handleAuthResponse = function(response) {
        if (response.status == 'connected') {
            $scope.sessionService.accessToken = response.authResponse.accessToken;
            $scope.sessionService.authenticatedGet(hostname + 'users/me',
                function(data) {
                    $scope.sessionService.loggedIn = true;
                    $scope.sessionService.userInfo = data;
                    $scope.regionService.populateDataForCurrentRegion();
                }
            );
        }
        else {
            $scope.sessionService.loggedIn = false;
            $scope.sessionService.userInfo = null;
            $scope.sessionService.accessToken = null;
        }
    };

    $scope.login = function() {
        Facebook.login();
    };

    $scope.logout = function() {
        Facebook.logout();
    };

    // Initial login
    Facebook.getLoginStatus();
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

    $scope.open = function() {
        $scope.modalInstance = $modal.open({
            templateUrl: 'tournament_region_modal.html',
            scope: $scope,
            size: 'lg'
        });
        $scope.tournamentRegionCheckbox = {}
    };

    $scope.close = function() {
        $scope.modalInstance.close()
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
        console.log($scope.tournament.alias_to_id_map);
        console.log($scope.playerData);
        if ($scope.playerCheckboxState[playerAlias]) {
            $scope.tournament.alias_to_id_map[playerAlias] = null;
            delete $scope.playerData[playerAlias];
        }

    };

    $scope.playerSelected = function(playerAlias, $item) {
        $scope.playerCheckboxState[playerAlias] = false;
        $scope.tournament.alias_to_id_map[playerAlias] = $item.id;
        $http.get(hostname + $routeParams.region + '/players/' + $item.id).
            success(function(data) {
                $scope.playerData[playerAlias] = data;
                console.log($scope.tournament.alias_to_id_map);
            })
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


    // TODO submission checks! check to make sure everything in $scope.playerData is an object (not a string. string = partially typed box)

    $http.get(hostname + $routeParams.region + '/tournaments/' + $scope.tournamentId).
        success(function(data) {
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
        });
});

app.controller("PlayersController", function($scope, $routeParams, RegionService, PlayerService) {
    RegionService.setRegion($routeParams.region);
    $scope.regionService = RegionService;
    $scope.playerService = PlayerService;
});

app.controller("PlayerDetailController", function($scope, $http, $routeParams, $modal, RegionService, SessionService) {
    RegionService.setRegion($routeParams.region);
    $scope.regionService = RegionService;
    $scope.sessionService = SessionService;

    $scope.playerId = $routeParams.playerId;
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

