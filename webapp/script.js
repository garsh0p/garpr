var app = angular.module('app', []);

// Norcal Controller 
app.controller("norcalController", function($scope, $http) {
    $http.get('http://garsh0p.no-ip.biz:5100/norcal/rankings').
        success(function(data) {
            $scope.data = data;
        });

});

// Austin Controller 
app.controller("austinController", function($scope, $http) {
    $http.get('http://garsh0p.no-ip.biz:5100/norcal/rankings').
        success(function(data) {
            $scope.data = data;
        });

});

// Texas Controller 
app.controller("texasController", function($scope, $http) {
    $http.get('http://garsh0p.no-ip.biz:5100/norcal/rankings').
        success(function(data) {
            $scope.data = data;
        });

});





