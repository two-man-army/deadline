(function() {
    'use strict';

    angular.module('app', [
        'ngRoute',
        'ngMessages',
        'app.layout',
        'app.auth',
        'app.dashboard'
        ])
        .config(config)
        .constant('BASE_URL', 'http://localhost:8000/');

    config.$inject = ['$routeProvider'];

    function config($routeProvider) {
        $routeProvider.otherwise({
            redirectTo: '/'
        });
    }
}());


