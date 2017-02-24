(function() {
    'use strict';

    angular.module('app', [
        'ngRoute',
        'ngMessages',
        'ngCookies',
        'ui.bootstrap',
        'ngSanitize',
        'ui.tree',
        'app.layout',
        'app.auth',
        'app.dashboard',
        'app.challenge',
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

            .when('/challenges', {
                templateUrl: 'app/dashboard/templates/category_challenges.html',
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
            // if the next view requires authentication and the user is not authenticated
            if(next.requireLogin && !authService.isAuthenticated()) {
                $event.preventDefault();
            } else if (next.originalPath === '/' && authService.isAuthenticated()) {
                // Redirect the user if he's trying to acces the register/login page and is logged in
                $location.path('/dashboard')
            }
        })
    }
}());


