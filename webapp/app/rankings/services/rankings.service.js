angular.module('app.rankings').service('RankingsService', function($http, SessionService) {
    var service = {
        rankingsList: null,
        getRegionRankingCriteria: function(region){
            $scope.sessionService = SessionService

            url = hostname + region + '/rankings';
            $http.get(url, {},
            (data) => {
                return data;
            },
            (err) => {
                alert('There was an error getting the Ranking Criteria for the region')
            });
        }
    };
    return service;
});