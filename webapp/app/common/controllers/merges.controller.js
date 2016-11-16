angular.module('app.common').controller("MergesController", function($scope, $routeParams, $modal, RegionService, MergeService, SessionService) {
    RegionService.setRegion($routeParams.region);
    $scope.regionService = RegionService;
    $scope.mergeService = MergeService;
    $scope.sessionService = SessionService;

    $scope.undoMerge = function(mergeID) {
        url = hostname + $routeParams.region + '/merges/' + mergeID;

        successCallback = function(data) {
            alert("The accounts have successfully been unmerged.");
            window.location.reload();
        };

        $scope.sessionService.authenticatedDelete(url, successCallback);
    };
});
