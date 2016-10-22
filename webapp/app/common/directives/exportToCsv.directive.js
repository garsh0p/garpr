/**
Adopted from Yuvaraj Tana's implementation @codepen.io : https://codepen.io/YuvarajTana/pen/yNoNdZ/
**/
angular.module('app.common').directive('exportToCsv',function(){
    return {
        restrict: 'A',
        link: function (scope, element, attrs) {
            var el = element[0];
            element.bind('click', function(e){
                var table = document.getElementById("seed_table");
                var csvString = '';
                for(var i=1; i<table.rows.length;i++){
                    var rowData = table.rows[i].cells;
                    for(var j=1; j<3;j++){
                        csvString = csvString + rowData[j].innerHTML.trim() + ",";
                    }
                    csvString = csvString.substring(0,csvString.length - 1);
                    csvString = csvString + "\n";
                }
                csvString = csvString.substring(0, csvString.length - 1);
                var a = $('<a/>', {
                    style:'display:none',
                    href:'data:application/octet-stream;base64,'+btoa(csvString),
                    download: scope.tournament_name+'_seeding.csv'
                }).appendTo('body')
                a[0].click()
                a.remove();
            });
        }
    }
});