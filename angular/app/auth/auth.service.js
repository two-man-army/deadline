(function() {
    'use strict';

    angular
        .module('app.auth')
        .factory('authService', authService);

    authService.$inject = ['$http', 'BASE_URL'];

    function authService($http, BASE_URL) {

        var authService = {
            register: register,
            login: login,
            isAuthenticated: isAuthenticated
        };

        return authService;

        function register(user) {
            return $http({
                method: 'POST',
                url: BASE_URL + 'accounts/register/',
                headers: { 'Content-Type': 'application/json' },
                data: user
            });
        }

        function login(user) {
            return $http({
                method: 'POST',
                url: BASE_URL + 'accounts/login/',
                headers: { 'Content-Type': 'application/json' },
                data: user
            });
        }

        function isAuthenticated() {
            return sessionStorage['authToken'] != undefined;
        }
    }
}());
