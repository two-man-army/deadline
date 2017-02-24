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
            getUserTestCases: getUserTestCases,
            getUserInfo: getUserInfo
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

        function getUserInfo(userId) {
            var userURL = BASE_URL + 'accounts/user/' + userId

            return $http({
                method: 'GET',
                headers: {
                    'Authorization': 'Token ' + sessionStorage['authToken']
                },
                url: userURL
            })
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
        var i = 1;
        function myLoop () {           //  create a loop function
        setTimeout(function () {    //  call a 3s setTimeout when the loop is called
                      //  your code here
            i++;                     //  increment the counter
            if (i < 10) {            //  if the counter < 10, call the loop function
                myLoop();             //  ..  again which will trigger another 
            }                        //  ..  setTimeout()
        }, 300)
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
                        myLoop();
                        // var n = 1000000000;
                        // while (n > 0) {n--}  // stupid sleep
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
