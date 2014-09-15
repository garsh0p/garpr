var app = angular.module('myApp', ['ngRoute']);

app.service('RegionService', function ($http) {
    var regions = [];
    var region = '';

    var service = {
        getRegion: function() {
            return region;
        },

        getRegions: function() {
            return regions;
        },

        setRegion: function(r) {
            region = r;
        },

        setRegions: function(r) {
            regions = r;
        }
    };

    $http.get('http://garsh0p.no-ip.biz:5100/regions').
        success(function(data) {
            service.setRegions(data.regions);
        });

    return service;
});


app.config(['$routeProvider', function($routeProvider) {
    $routeProvider.when('/:region/rankings', {
        templateUrl: 'rankings.html',
        controller: 'RankingsController'
    }).
    otherwise({
        redirectTo: '/norcal/rankings'
    });
}]);

app.controller("RegionDropdownController", function($scope, RegionService) {
    $scope.regionService = RegionService;
});

app.controller("RankingsController", function($scope, $http, $routeParams, RegionService) {
    RegionService.setRegion($routeParams.region);
    if (RegionService.getRegions().indexOf(RegionService.getRegion()) >= 0) {
        $http.get('http://garsh0p.no-ip.biz:5100/' + $routeParams.region + '/rankings').
            success(function(data) {
                $scope.data = data;
            });
    }
});
