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
            get_csrf_token: get_csrf_token
        };

        return authService;

        function register(user) {
            return $http({
                method: 'POST',
                url: BASE_URL + 'accounts/register',
                headers: { 'Content-Type': 'application/json ' + sessionStorage.authToken },
                data: user
            });
        }

        function login(user) {
            return $http({
                method: 'POST',
                url: BASE_URL + 'accounts/login',
                headers: { 'Content-Type': 'application/json' },
                data: user
            });
        }

        function get_csrf_token(){
            return $http.get(BASE_URL + '/accounts/get_csrf')
        }
    }
}());
