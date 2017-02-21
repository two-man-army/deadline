(function() {
    'use strict';

    angular.module('app.challenge').factory('challengeService', challengeService);

    challengeService.$inject = ['$http', 'BASE_URL'];

    function challenceService($http, BASE_URL) {
        var challengeService = {
            getChallengeInfo: getChallengeInfo,
            getChallengeSubmissions: getChallengeSubmissions
        }
        function getChallengeInfo(challengeId) {
            var challengeURL = BASE_URL + 'challenges/' + challengeId;

            return $http({
                method: 'GET',
                url: challengeURL
            });
        }

        function getChallengeSubmissions(challengeId) {
            var allSubmissionsURL = BASE_URL + 'challenges/' + challengeId + '/submissions/all';
            
            return $http({
                method: 'GET',
                url: allSubmissionsURL
            });
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
                headers: { 'Content-Type': 'application/json' },
                data: {'code': code}
            })
        }
    }
})