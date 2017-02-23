(function() {
    'use strict'

    angular.module('app.challenge')
        .controller('ChallengeController', ChallengeController);

    ChallengeController.$inject = ['$http', '$location', 'challengeService']

    function ChallengeController($http, $location, challengeService) {
        var vm = this;
        vm.getChallenge = getChallenge
        vm.submitSolution = submitSolution

        angular.element(document).ready(function() {
            require.config({ paths: { 'vs': 'node_modules/monaco-editor/min/vs' }});
            require(['vs/editor/editor.main'], function() {
                var editor = monaco.editor.create(document.getElementById('challenge-editor'), {
                    value: [
                        'def foo() {',
                        '\tprint("Hello world!")'
                    ].join('\n'),
                    language: "python",
                    lineNumbers: true,
                    roundedSelection: false,
                    scrollBeyondLastLine: false,
                    readOnly: false,
                    theme: "vs-dark",
                });
            });

        });

        function getChallenge(challengeId) {
            challengeService.getChallengeInfo(challengeId).
                then(
                    function(res) {
                        vm.challengeInfo = res.data
                    },
                    function(error) {
                        console.log(error)
                    })
        }

        function submitSolution(challengeId) {
            var code = window.monaco.editor.getModels()[0].getValue();

            challengeService.submitSolution(challengeId, code)
                .then(
                    function(res) {
                        vm.solutionInfo = res.data;
                        vm.solutionId = vm.solutionInfo.id;

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
