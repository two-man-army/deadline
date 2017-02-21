(function() {
    'use strict'

    angular.module('app.challenge')
        .controller('ChallengeController', ChallengeController);

    ChallengeController.$inject = ['$http', 'authService', '$location', 'BASE_URL']

    function ChallengeController($http, challengeService, $location) {
        var vm = this;
        vm.getChallenge = getChallenge

        function getChallenge($event, challengeId) {
            $event.preventDefault()

            challengeService.getChallengeInfo(challengeId)
                .then(
                    function(res) {
                        if (response.status != 200) {
                            // ERROR - Display to the user
                            return;
                        }
                        var challengeInfo = response.data
                        // TODO: Display the challenge to the user!
                        
                    },
                    function(error) {
                     console.log(error)   
                    }
                )
        }

        function submitSolution($event, challengeId, code) {
            $event.preventDefault()

            challengeService.submitSolution(challengeId, code)
                .then(
                    function(res) {
                        if (response.status != 201) {
                            // ERROR - Display to the user
                            return;
                        }
                        var solutionInfo = response.data;
                        // Issue GET requests to this URL to update it's score !!!
                        var solutionURL = BASE_URL + '/challenges/' + challengeId + '/submissions/' + solutionInfo.id
                        // Issue GET requests to this URL to get the test cases for the given solution
                        var solutionTestCasesURL = solutionURL + '/tests'
                    },
                    function(error) {
                        console.log(error)
                    }
                )
        }
    }
}())
