var app = angular.module('app', 
    ['ngRoute', 'ui.bootstrap', 'angulartics', 'angulartics.google.analytics', 'facebook',
        'app.common',
        'app.headToHead',
        'app.players',
        'app.rankings',
        'app.tools',
        'app.tournaments']);






app.config(function ($httpProvider) {
    $httpProvider.defaults.withCredentials = true;
    $httpProvider.defaults.useXDomain = true;
    $httpProvider.defaults.headers.common = 'Content-Type: application/json';
    delete $httpProvider.defaults.headers.common['X-Requested-With'];
    //rest of route code
});

app.config(['$routeProvider', function($routeProvider) {
    $routeProvider.when('/:region/rankings', {
        templateUrl: 'app/rankings/views/rankings.html',
        controller: 'RankingsController',
        activeTab: 'rankings'
    }).
    when('/:region/players', {
        templateUrl: 'app/players/views/players.html',
        controller: 'PlayersController',
        activeTab: 'players'
    }).
    when('/:region/players/:playerId', {
        templateUrl: 'app/players/views/player_detail.html',
        controller: 'PlayerDetailController',
        activeTab: 'players'
    }).
    when('/:region/tournaments', {
        templateUrl: 'app/tournaments/views/tournaments.html',
        controller: 'TournamentsController',
        activeTab: 'tournaments'
    }).
    when('/:region/tournaments/:tournamentId', {
        templateUrl: 'app/tournaments/views/tournament_detail.html',
        controller: 'TournamentDetailController',
        activeTab: 'tournaments'
    }).
    when('/:region/merges', {
        templateUrl: 'app/players/views/merges.html',
        controller: 'MergesController',
        activeTab: 'tournaments'
    }).
    when('/:region/headtohead', {
        templateUrl: 'app/head_to_head/views/headtohead.html',
        controller: 'HeadToHeadController',
        activeTab: 'headtohead'
    }).
    when('/:region/seed', {
        templateUrl: 'app/tools/seed_tournament/views/seed.html',
        controller: 'SeedController',
        activeTab: 'seed'
    }).
    when('/about', {
        templateUrl: 'app/common/views/about.html',
        activeTab: 'about'
    }).
    when('/adminfunctions',{
        templateUrl: 'app/tools/admin_functions/views/admin_functions.html',
        controller: 'AdminFunctionsController'
    }).
    otherwise({
        redirectTo: '/' + defaultRegion + '/rankings'
    });
}]);




