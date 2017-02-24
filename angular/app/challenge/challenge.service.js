(function() {
    'use strict';

    angular
        .module('app.challenge')
        .factory('challengeService', challengeService);

    challengeService.$inject = ['$interval', '$http', 'BASE_URL'];

    function challengeService($interval, $http, BASE_URL) {

        var challengeService = {
            getChallengeInfo: getChallengeInfo,
            getChallengeSolution: getChallengeSolution,
            getAllChallengeSolutions: getAllChallengeSolutions,
            submitSolution: submitSolution,
            getUserSubmissions: getUserSubmissions,
            getUserTestCases: getUserTestCases
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
            })
                .then(function(data, status, headers, config) {
                    console.log(data.data.pending)
                    if (data.data.pending === false) {
                        console.log(data.pending)
                        console.log(data)
                        return data.data
                    } else {
                        console.log('loop')
                        var n = 1000000000;
                        while (n > 0) {n--}  // stupid sleep
                        return getChallengeSolution(challengeId, solutionId)
                    }
                })
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

        function getUserTestCases(challengeId, solutionId) {
            var userTestCasesURL = BASE_URL + 'challenges/' + challengeId + '/submissions/' + solutionId + '/tests'
             return $http({
                method: 'GET',
                headers: {
                    'Authorization': 'Token ' + sessionStorage['authToken']
                },
                url: userTestCasesURL
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
