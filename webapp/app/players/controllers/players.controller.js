angular.module('app.players').controller("PlayersController", function($scope, $routeParams, RegionService, PlayerService) {
    RegionService.setRegion($routeParams.region);
    $scope.regionService = RegionService;
    $scope.playerService = PlayerService;

    /** PAGENATION **/
    /*
    $scope.totalItems = $scope.playerService.playerList.players.length;
    $scope.viewby = 25;
    $scope.currentPage = 1;
    $scope.itemsPerPage = $scope.viewby;
    $scope.maxSize = 5;
    $scope.setPage = function (pageNo) {
        $scope.currentPage = pageNo;
    };
    $scope.setItemsPerPage = function(num) {
        $scope.itemsPerPage = num;
        $scope.currentPage = 1;
    };
    /** END PAGENATION **/


});