var app = angular.module('myApp', []);
app.controller("Controller", function($scope, $http) {
    $http.get('http://garsh0p.no-ip.biz:5100/norcal/rankings').
        success(function(data) {
            $scope.data = data;
        });

});

var moduleA = angular.module('MyModuleA', []);
moduleA.controller("MyControllerA", function($scope, $http) {
    $http.get('http://garsh0p.no-ip.biz:5100/austin/rankings').
        success(function(data) {
            $scope.data = data;
        });

});

var moduleT = angular.module('MyModuleT', []);
moduleT.controller("MyControllerT", function($scope, $http) {
    $http.get('http://garsh0p.no-ip.biz:5100/texas/rankings').
        success(function(data) {
            $scope.data = data;
        });

});





