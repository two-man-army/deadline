(function() {
    'use strict';

    angular.module('app', [
        'ngRoute',
        'ngMessages',
        'app.layout',
        ])
        .config(config)
        .constant('BASE_URL', 'Add url here');

    config.$inject = ['$routeProvider'];

    function config($routeProvider) {
        $routeProvider.otherwise({
            redirectTo: '/'
        });
    }
}());


