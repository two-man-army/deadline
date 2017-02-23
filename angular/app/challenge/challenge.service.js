(function() {
    'use strict';

    angular
        .module('app.challenge')
        .factory('challengeService', challengeService);

    challengeService.$inject = ['$http', 'BASE_URL'];

    function challengeService($http, BASE_URL) {

        var challengeService = {
            getChallengeInfo: getChallengeInfo,
            getChallengeSolution: getChallengeSolution,
            getAllChallengeSolutions: getAllChallengeSolutions,
            submitSolution: submitSolution,
            getUserSubmissions: getUserSubmissions
        };

        return challengeService;

        function getChallengeInfo(challengeId) {
            var challengeURL = BASE_URL + 'challenges/' + challengeId;

            return $http({
                method: 'GET',
                headers: {
                    'Authorization': 'Token ' + sessionStorage['authToken']
                },
                url: challengeURL
            });
        }

        function getAllChallengeSolutions(challengeId) {
            var allSubmissionsURL = BASE_URL + 'challenges/' + challengeId + '/submissions/all';

            return $http({
                method: 'GET',
                headers: {
                    'Authorization': 'Token ' + sessionStorage['authToken']
                },
                url: allSubmissionsURL
            });
        }

        function getChallengeSolution(challengeId, solutionId) {
            var solutionURL = BASE_URL + 'challenges/' + challengeId + '/submissions/' + solutionId;

            return $http({
                method: 'GET',
                headers: {
                    'Authorization': 'Token ' + sessionStorage['authToken']
                },
                url:solutionURL
            });
        }

        function getChallengeTopSubmissions(challengeId) {
            var topSubmissionsURL = BASE_URL + 'challenges/' + challengeId + '/top'

            return $http({
                method: 'GET',
                headers: {
                    'Authorization': 'Token ' + sessionStorage['authToken']
                },
                url: topSubmissionsURL
            })
        }

        function getUserSubmissions(challengeId) {
            var userSubmissionsURL = BASE_URL + 'challenges/' + challengeId + '/submissions/all'

            return $http({
                method: 'GET',
                headers: {
                    'Authorization': 'Token ' + sessionStorage['authToken']
                },
                url: userSubmissionsURL
            })
        }

        /**
         * Submits a solution for a given challenge.
         * Returns the serialized solution
         */
        function submitSolution(challengeId, code) {
            /* */
            var submitSolutionURL = BASE_URL + 'challenges/' + challengeId + '/submissions/new';

            return $http({
                method: 'POST',
                url: submitSolutionURL,
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Token ' + sessionStorage['authToken']
                },
                data: {'code': code}
            })
        }
    }
}());
