angular.module('app.tools').controller("AdminFunctionsController", function($scope, $http, RegionService, SessionService){
    var url = hostname + "adminfunctions";
    $scope.regionService = RegionService;
    $scope.sessionService = SessionService;

    $scope.regions = []
    $http.get(hostname + 'regions').
        success(function(data) {
            data.regions.forEach(function(region){
                $scope.regions.push(region);
            });
        });

    $scope.regionStatusMessage = "";
    $scope.userStatusMessage = "";

    $scope.foo = null;
    $scope.postParams = {
        function_type: '',
        new_region: '',
        new_user_name: '',
        new_user_pass: '',
        new_user_permissions: '',
        new_user_regions: []
    };

    $scope.addRegion = function(region){
        if(!$scope.postParams.new_user_regions.includes(region))
            $scope.postParams.new_user_regions.push(region);
    };

    $scope.removeRegion = function(region){
        if($scope.postParams.new_user_regions.includes(region))
            $scope.postParams.new_user_regions.splice($scope.postParams.new_user_regions.indexOf(region), 1);
    };

    $scope.checkRegionBox = function(region){
        var display_name = region.display_name;
        var checkboxId = display_name + "_checkbox";
        var checkbox = document.getElementById(checkboxId);
        if(checkbox.checked){
            $scope.addRegion(region.id);
        }
        else{
            $scope.removeRegion(region.id);
        }
    };

    $scope.submitNewUser = function(){
        if($scope.postParams.new_user_name == null ||
            $scope.postParams.new_user_pass == null){
            return;
        }
        $scope.postParams.function_type = 'user';

        //TODO HTTP CALL TO API
        $scope.sessionService.authenticatedPut(url, $scope.postParams, $scope.putUserSuccess, $scope.putUserFailure);
    };

    $scope.submitNewRegion = function(){
        if($scope.postParams.new_region == null){
            return;
        }
        $scope.postParams.function_type = 'region';

        //TODO HTTP CALL TO API
        $scope.sessionService.authenticatedPut(url, $scope.postParams, $scope.putRegionSuccess, $scope.putRegionFailure);
    };

    $scope.putRegionSuccess = function(response, status, headers, bleh){
        console.log(response);
        $scope.regionStatusMessage = "Region " + $scope.postParams.new_region + " successfully inserted!";
        document.getElementById('regionStatusMessage').innerHTML
            = "Region " + $scope.postParams.new_region + " successfully inserted!";

        var form = document.getElementById('newRegionForm');
        resetForm(form);
    };

    $scope.putUserSuccess = function(response, status, headers, bleh){
        console.log(response);
        $scope.userStatusMessage = "User " + $scope.postParams.new_user_name + " successfully inserted!";
        document.getElementById('userStatusMessage').innerHTML
            = "User " + $scope.postParams.new_user_name + " successfully inserted!";

        var form = document.getElementById('newUserForm');
        resetForm(form);
    };

    $scope.putRegionFailure = function(response, status, headers, bleh){
        console.log(response);
        $scope.regionStatusMessage = "An error occurred in inserting user."
        document.getElementById('regionStatusMessage').innerHTML = "An error occurred in inserting region.";
    };

    $scope.putUserFailure = function(response, status, headers, bleh){
        console.log(response);
        $scope.userStatusMessage = "An error occurred in inserting user."
        document.getElementById('userStatusMessage').innerHTML = "An error occurred in inserting user.";
    };

    function resetForm(form) {
        // clearing inputs
        var inputs = form.getElementsByTagName('input');
        for (var i = 0; i<inputs.length; i++) {
            switch (inputs[i].type) {
                // case 'hidden':
                case 'text':
                    inputs[i].value = '';
                    break;
                case 'radio':
                case 'checkbox':
                    inputs[i].checked = false;
            }
        }

        // clearing selects
        var selects = form.getElementsByTagName('select');
        for (var i = 0; i<selects.length; i++)
            selects[i].selectedIndex = 0;

        // clearing textarea
        var text= form.getElementsByTagName('textarea');
        for (var i = 0; i<text.length; i++)
            text[i].innerHTML= '';

        var pword = form.getElementsByTagName('password');
        for (var i = 0; i<text.length; i++)
            text[i].innerHTML= '';

        return false;
    };

});