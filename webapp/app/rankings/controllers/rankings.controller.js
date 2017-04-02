angular.module('app.rankings').controller("RankingsController", function($scope, $http, $routeParams, $modal, RegionService, RankingsService, SessionService, TournamentService) {
    RegionService.setRegion($routeParams.region);
    $scope.regionService = RegionService;
    $scope.rankingsService = RankingsService
    $scope.sessionService = SessionService
    $scope.tournamentService = TournamentService

    $scope.modalInstance = null;
    $scope.disableButtons = false;

    $scope.rankingNumDaysBack = 0;
    $scope.rankingsNumTourneysAttended = 0;
    $scope.tourneyNumDaysBack = 999;

    $scope.postData = {};

    $scope.prompt = function() {
        var selectedTournament = null;
        var finalizedTournaments = $scope.tournamentService.getFinalizedTournaments();
        if (finalizedTournaments.length == 1) {
            selectedTournament = finalizedTournaments[0];
        } else if (finalizedTournaments.length > 1) {
            selectedTournament = finalizedTournaments[1];
        }
        $scope.postData = {tournamentToDiff: selectedTournament};
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
            $scope.disableButtons = false;
        };

        var postParams = {
            ranking_num_tourneys_attended: $scope.rankingsNumTourneysAttended,
            ranking_activity_day_limit: $scope.rankingNumDaysBack,
            tournament_qualified_day_limit: $scope.tourneyNumDaysBack,
            tournament_id_to_diff: $scope.postData.tournamentToDiff.id
        }

        $scope.sessionService.authenticatedPost(url, postParams, successCallback, angular.noop);
    };

    $scope.cancel = function() {
        $scope.modalInstance.close();
        $scope.disableButtons = false;
    };

    $scope.getRegionRankingCriteria = function(){
        url = hostname + $routeParams.region + '/rankings';
        $http.get(url)
        .then(
        (res) => {
            $scope.rankingNumDaysBack = res.data.ranking_criteria.ranking_activity_day_limit;
            $scope.rankingsNumTourneysAttended = res.data.ranking_criteria.ranking_num_tourneys_attended;
            $scope.tourneyNumDaysBack = res.data.ranking_criteria.tournament_qualified_day_limit;

        },
        (err) => {
            alert('There was an error getting the Ranking Criteria for the region')
        });

    }

    $scope.saveRegionRankingsCriteria = function(){
        url = hostname + $routeParams.region + '/rankings';
        var putParams = {
            ranking_num_tourneys_attended: $scope.rankingsNumTourneysAttended,
            ranking_activity_day_limit: $scope.rankingNumDaysBack,
            tournament_qualified_day_limit: $scope.tourneyNumDaysBack
        }

        $scope.sessionService.authenticatedPut(url, putParams,
        (res) => {
            alert('Successfully updated Region: ' + $routeParams.region + ' Ranking Criteria.');
        },
        (err) => {
            alert('There was an error updating the Region Ranking Criteria. Please try again.');
        });
    };

    var rankingCriteria = $scope.getRegionRankingCriteria()
});
