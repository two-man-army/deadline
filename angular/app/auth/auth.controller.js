(function() {
    'use strict'

    angular.module('app.auth')
        .controller('AuthController', AuthController)
        .config(config)
        .run(run);

    config.$inject = ['$httpProvider']
    AuthController.$inject = ['$http', 'authService', '$location']

    function AuthController($http, authService, $location) {
        var vm = this;

        vm.register = register
        vm.login = login

        function register($event, user) {
            $event.preventDefault()
            console.log(user)

            authService.register($event, user)
                .then(
                    function(res) {
                        vm.login($event, user)
                    },
                    function(error) {
                        console.log(error)
                    })
        }

        function login($event, user) {
            $event.preventDefault()

            authService.login(user)
                .then(
                    function(res) {
                        sessionStorage['authToken'] = res.data.user_token;
                        $location.path('/dashboard');
                    },

                    function(error) {
                        console.log(error)
                    }
                );
        }
    }

    function config($httpProvider) {
        $httpProvider.defaults.headers.common['Access-Control-Allow-Headers'] = '*';
        $httpProvider.defaults.headers.common['access-control-allow-origin'] = '*';
        $httpProvider.defaults.xsrfCookieName = 'csrftoken';
        $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    }

    function run($http) {
        // $http.defaults.headers.post['X-CSRFToken'] = '801hIqX6ohVMTgrve4q0utdOiWxlQhflrwDPG3J5yCQmc2MssMcAGEa66eKLYyXY';
        // $http.defaults.headers.common.Authorization = 'Token Ia57OLegUnsCqEie9kmmZuHfxNUqqunUYD5yLD3Ug2RSJNSEq8sUTQJcDcrcDvs6';
    }

}())
