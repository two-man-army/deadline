(function() {
    'use strict'

    angular.module('app.auth')
        .controller('AuthController', AuthController)
        .config(config)
        .run(run);

    AuthController.$inject = ['$http', 'authService', '$location']

    function AuthController($http, authService, $location) {
        var vm = this;

        vm.register = register
        vm.login = login
        vm.get_csrf_token = get_csrf_token

        function register(user) {

        }

        function login($event, user) {
            $event.preventDefault()

            authService.login(user)
                .then(
                    function(res) {
                        debugger;
                        sessionStorage['authToken'] = response.data.user_tocken;
                        $location.path('/dashboard');
                    },

                    function(error) {
                        console.log($http.defaults.headers)
                    }
                );
        }

        function get_csrf_token() {
            authService.get_csrf_token()
                .then(
                    function(response) {
                        console.log(response)
                    },

                    function(error) {
                        console.log(error)
                    })
        }
    }

    function config($httpProvider) {
        $httpProvider.defaults.headers.common['Access-Control-Allow-Headers'] = '*';
        $httpProvider.defaults.headers.common['access-control-allow-origin'] = '*';
    }

    function run($http) {
        $http.defaults.headers.post['X-CSRFToken'] = 'Ia57OLegUnsCqEie9kmmZuHfxNUqqunUYD5yLD3Ug2RSJNSEq8sUTQJcDcrcDvs6';
        $http.defaults.headers.common.Authorization = 'Token Ia57OLegUnsCqEie9kmmZuHfxNUqqunUYD5yLD3Ug2RSJNSEq8sUTQJcDcrcDvs6';
    }

}())
