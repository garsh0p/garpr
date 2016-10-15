angular.module('app.rankings').controller("RankingsController", function($scope, $routeParams, $modal, RegionService, RankingsService, SessionService) {
    RegionService.setRegion($routeParams.region);
    $scope.regionService = RegionService;
    $scope.rankingsService = RankingsService
    $scope.sessionService = SessionService

    $scope.modalInstance = null;
    $scope.disableButtons = false;

    $scope.prompt = function() {
        $scope.modalInstance = $modal.open({
            templateUrl: 'app/rankings/views/generate_rankings_prompt_modal.html',
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