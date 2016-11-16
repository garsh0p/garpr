angular.module('app.common').controller("AuthenticationController", function($scope, $modal, Facebook, SessionService, RegionService) {
    $scope.sessionService = SessionService;
    $scope.regionService = RegionService;
    $scope.postParams = {};
    $scope.errorTxt = "";

    $scope.handleAuthResponse = function(response, status, headers, bleh) {
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
            templateUrl: 'app/common/views/login_modal.html',
            scope: $scope,
            size: 'lg'
        });
    };

    $scope.login = function() {
        url = hostname + 'users/session'
        $scope.sessionService.authenticatedPut(url, $scope.postParams, $scope.handleAuthResponse, $scope.handleAuthResponse);
    };

    $scope.logout = function() {
        url = hostname + 'users/session'
        $scope.sessionService.authenticatedDelete(url, $scope.handleAuthResponse, $scope.postParams,
            $scope.handleAuthResponse);
    };

    // Initial login
    $scope.getSessionInfo();
});