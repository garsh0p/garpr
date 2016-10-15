angular.module('app.common').controller("NavbarController", function($scope, $route, $location, RegionService, PlayerService) {
    $scope.regionService = RegionService;
    $scope.playerService = PlayerService;
    $scope.$route = $route;

    $scope.selectedPlayer = null;

    $scope.playerSelected = function($item) {
        $location.path($scope.regionService.region.id + '/players/' + $item.id);
        $scope.selectedPlayer = null;
    };
});