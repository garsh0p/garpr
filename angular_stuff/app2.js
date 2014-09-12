var app = angular.module("myApp", []);
app.controller("AppController", function($scope, $http){
	var app = this; 
	$http.get("http://localhost:3000")
	   .success(function(data){
	      $scope.stuff = data;
	});

});
