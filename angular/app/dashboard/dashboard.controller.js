(function() {
    'use strict'

    angular.module('app.dashboard')
        .controller('DashboardController', DashboardController);

    DashboardController.$inject = ['$http', 'authService', '$location']

    function DashboardController($http, $location, authService) {
        var vm = this;

    }
}())
