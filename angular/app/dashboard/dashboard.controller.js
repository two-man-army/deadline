(function() {
    'use strict'

    angular.module('app.dashboard')
        .controller('DashboardController', DashboardController)
        .config(config);

    DashboardController.$inject = ['$http', 'authService', '$location']
    config.$inject = ['$routeProvider']

    function DashboardController($http, $location) {
        var vm = this;

    }

    function config($routeProvider) {
        $routeProvider.when('/dashboard', {
            templateUrl: 'app/dashboard/templates/dashboard.html',
            controllerAs: 'vm',
            controller: 'DashboardController'
        });
    }

}())
