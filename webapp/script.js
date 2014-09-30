var app = angular.module('myApp', ['ngRoute']);

var toTitleCase = function(str){
    return str.replace(/\w\S*/g, function(txt){return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();});
}

app.service('RegionService', function ($http) {
    var service = {
        regions: [],
        region: ''
    };

    $http.get('http://garsh0p.no-ip.biz:5100/regions').
        success(function(data) {
            service.regions = data.regions;
        });

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

app.controller("RankingsController", function($scope, $http, $routeParams, RegionService) {
    RegionService.region = $routeParams.region;
    $scope.region = $routeParams.region;

    $http.get('http://garsh0p.no-ip.biz:5100/' + $routeParams.region + '/rankings').
        success(function(data) {
            $scope.data = data;
        });
});

app.controller("TournamentsController", function($scope, $http, $routeParams, RegionService) {
    RegionService.region = $routeParams.region;

    $http.get('http://garsh0p.no-ip.biz:5100/' + $routeParams.region + '/tournaments').
        success(function(data) {
            $scope.data = data;
        });
});

app.controller("PlayersController", function($scope, $http, $routeParams, RegionService) {
    RegionService.region = $routeParams.region;
    $scope.region = $routeParams.region;

    $http.get('http://garsh0p.no-ip.biz:5100/' + $routeParams.region + '/players').
        success(function(data) {
            $scope.data = data;
        });
});

app.controller("PlayerDetailController", function($scope, $http, $routeParams, RegionService) {
    RegionService.region = $routeParams.region;
    $scope.region = $routeParams.region;
    $scope.prettyRegionName = toTitleCase($scope.region);
    $scope.playerId = $routeParams.playerId;

    $http.get('http://garsh0p.no-ip.biz:5100/' + $routeParams.region + '/players/' + $routeParams.playerId).
        success(function(data) {
            $scope.playerData = data;
        });

    $http.get('http://garsh0p.no-ip.biz:5100/' + $routeParams.region + '/matches?player=' + $routeParams.playerId).
        success(function(data) {
            $scope.matches = data;
        });

});
