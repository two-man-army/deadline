(function() {
    'use strict'

    angular.module('app.dashboard')
        .controller('DashboardController', DashboardController);

    DashboardController.$inject = ['$http', 'authService', '$location']
    config.$inject = ['$routeProvider']

    function DashboardController($http, $location, authService) {
        var vm = this;

    }
}())
