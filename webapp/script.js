var app = angular.module('myApp', ['ngRoute']);

app.service('RegionService', function ($http, PlayerService, TournamentService, RankingsService) {
    var service = {
        regions: [],
        region: '',
        setRegion: function (newRegion) {
            if (newRegion != this.region) {
                this.region = newRegion;
                PlayerService.playerList = null;
                TournamentService.tournamentList = null;
                RankingsService.rankingsList = null;

                $http.get('http://garsh0p.no-ip.biz:5100/' + this.region + '/players').
                    success(function(data) {
                        PlayerService.playerList = data;
                    });

                $http.get('http://garsh0p.no-ip.biz:5100/' + this.region + '/tournaments').
                    success(function(data) {
                        TournamentService.tournamentList = data;
                    });

                $http.get('http://garsh0p.no-ip.biz:5100/' + this.region + '/rankings').
                    success(function(data) {
                        RankingsService.rankingsList = data;
                    });
            }
        }
    };

    $http.get('http://garsh0p.no-ip.biz:5100/regions').
        success(function(data) {
            service.regions = data.regions;
        });

    return service;
});

app.service('PlayerService', function ($http) {
    var service = {
        playerList: null
    };
    return service;
});

app.service('TournamentService', function ($http) {
    var service = {
        tournamentList: null
    };
    return service;
});

app.service('RankingsService', function ($http) {
    var service = {
        rankingsList: null
    };
    return service;
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
    when('/about', {
        templateUrl: 'about.html',
        activeTab: 'about'
    }).
    otherwise({
        redirectTo: '/norcal/rankings'
    });
}]);

app.controller("RegionDropdownController", function($scope, $route, RegionService) {
    $scope.regionService = RegionService;
    $scope.$route = $route;
});

app.controller("RankingsController", function($scope, $http, $routeParams, RegionService, RankingsService) {
    RegionService.setRegion($routeParams.region);
    $scope.regionService = RegionService;
    $scope.rankingsService = RankingsService
});

app.controller("TournamentsController", function($scope, $http, $routeParams, RegionService, TournamentService) {
    RegionService.setRegion($routeParams.region);
    $scope.regionService = RegionService;
    $scope.tournamentService = TournamentService;
});

app.controller("PlayersController", function($scope, $http, $routeParams, RegionService, PlayerService) {
    RegionService.setRegion($routeParams.region);
    $scope.regionService = RegionService;
    $scope.playerService = PlayerService;
});

app.controller("PlayerDetailController", function($scope, $http, $routeParams, RegionService) {
    RegionService.setRegion($routeParams.region);
    $scope.regionService = RegionService;
    $scope.playerId = $routeParams.playerId;

    $http.get('http://garsh0p.no-ip.biz:5100/' + $routeParams.region + '/players/' + $routeParams.playerId).
        success(function(data) {
            $scope.playerData = data;
        });

    $http.get('http://garsh0p.no-ip.biz:5100/' + $routeParams.region + '/matches/' + $routeParams.playerId).
        success(function(data) {
            $scope.matches = data.matches.reverse();
        });

});
