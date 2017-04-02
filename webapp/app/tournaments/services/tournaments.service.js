angular.module('app.tournaments').service('TournamentService', function($filter) {
    var service = {
        tournamentList: null,
        getFinalizedTournaments: function() {
            return $filter('filter')(this.tournamentList, {pending: false});
        }
    };
    return service;
});
