(function() {
    'use strict';

    angular.module('app', [
        'ngRoute',
        'ngMessages',
        'app.layout',
        'app.auth',
        'app.dashboard',
        'app.challenge'
    ])
        .config(config)
        .run(run)
        .constant('BASE_URL', 'http://localhost:8000/');

    config.$inject = ['$routeProvider'];
    run.$inject = ['$rootScope', '$location', 'authService']

    function config($routeProvider) {
        $routeProvider
            .when('/', {
                templateUrl: 'app/layout/templates/layout.html',
                controllerAs: 'vm',
                controller: 'LayoutVideoController',
                requireLogin: false
            })

            .when('/dashboard', {
                templateUrl: 'app/dashboard/templates/dashboard.html',
                controllerAs: 'vm',
                controller: 'DashboardController',
                requireLogin: true
            })

            .when('/challenge', {
                templateUrl: 'app/challenge/templates/challenge.html',
                controllerAs: 'vm',
                controller: 'ChallengeController',
                requireLogin: true
            })

            .otherwise({
                redirectTo: '/'
            });
    }

    function run($rootScope, $location, authService) {
        $rootScope.$on('$routeChangeStart', function($event, next, current) {
            if(next.requireLogin && !authService.isAuthenticated()) {
                $event.preventDefault();
            } else {
                $location.path('/dashboard')
            }

        })
    }
}());


