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
                        var solutionId = solutionInfo.id;
                        // TODO !!!
                        // TODO: Issue GET requests with challengeService.getChallengeSolution()
                        // until response.data.pending is True, then display the results!
                    },
                    function(error) {
                        console.log(error)
                    }
                )
        }
    }
}())
