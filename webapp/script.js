var app = angular.module('myApp', []);
app.controller("Controller", function($scope, $http) {
    $http.get('http://garsh0p.no-ip.biz:5100/norcal/rankings').
        success(function(data) {
            $scope.data = data;
        });

});
