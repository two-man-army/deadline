(function() {
    'use strict'

    angular.module('app.dashboard')
        .controller('DashboardController', DashboardController)
        .directive('ngChallenge', [function(){
            return {
                restrict: 'A',
                templateUrl: 'app/challenge/templates/challenge.html'
            }
        }]);

    DashboardController.$inject = ['$scope', '$http', '$location', '$cookies', 'dashboardService', 'challengeService']

    function DashboardController($scope, $http, $location, $cookies, dashboardService, challengeService) {
        var mobileView = 992,
            vm = this;

        var NEWLINE_PLACEHOLDER_TOKEN = '{{NPL}}'
        //vm.getMainChallenges = getMainChallenges;
        vm.getSubCategoryChallenges = getSubCategoryChallenges;
        vm.showLatestAttepmts = true;
        vm.showCategoryChallenges = false;
        vm.userScore = sessionStorage['user_score'] || '0'
        vm.showEditor = false;
        vm.goToChallenge = goToChallenge;
        vm.submitSolution = submitSolution;
        vm.getUserSubmissions = getUserSubmissions
        vm.logout = logout;
        getMainCategories();
        getLatestAttemptedChallenges();

        function getMainCategories() {
            dashboardService.getMainCategories().then(
                function(res) {
                    console.log(res)
                    // Categories is a list of Category objects
                    // A Category object is the following:
                    // {
                    //    "name":"Algorithms",
                    //    "sub_categories":["Graphs", "Strings", "Recursion"]
                    // }

                    vm.categories = res.data
                },
                function(error) {
                    console.log(error)
                }
            )
        }

        function getSubCategoryChallenges(subCategoryName) {
            // Used to list the challenges from a specific category
            dashboardService.getSubCategory(subCategoryName).then(
                function(res) {
                    /*
                        A SubCategory object is the following:
                        {
                            {"name":"Graph", 
                            "challenges": [
                                {
                                    "id":1, 
                                    "name":"Find Something In Graph", 
                                    "rating":5, "score":10
                                }
                                ]
                            }
                        }
                        Holds a name and challenges - a list of challenge objects with some meta information
                        */
                    vm.subcategory = res.data;
                    vm.challenges = vm.subcategory.challenges;
                    vm.showCategoryChallenges = true;
                    vm.showLatestAttepmts = false;
                    vm.showEditor = false;
                    //$location.path('/challenges')

                },
                function(error) {
                    console.log(error)
                }
            )
        }

        function getLatestAttemptedChallenges() {
            // Used to list the latest attempted challenges by the user
            dashboardService.getLatestAttemptedChallenges().then(
                function (res) {
                    /*
                        Returns a list of LimitedChallenge objects.
                        A LimitedChallenge object is the following:
                        {
                            name: "Say Hello World!",
                            rating: 5  // the difficulty of the challenge
                            score: 10 // the score it gives
                            category: "Miscellaneous"
                        }
                        */
                    vm.latestAttemptedChallenges = res.data;
                }
            ),
                function(error) {
                    console.log(error)
                }
        }
        // Will remove all falsy values: undefined, null, 0, false, NaN and "" (empty string)
        function cleanArray(actual) {
        var newArray = new Array();
        for (var i = 0; i < actual.length; i++) {
            if (actual[i]) {
            newArray.push(actual[i]);
            }
        }
        return newArray;
        }

        function convertBold(str) {
            var splitContent = str.split(/\s/)
            for (var i=0; i<splitContent.length; i++) {
                if (splitContent[i].startsWith('**')) {
                    if (splitContent[i].endsWith('**.')) {
                        var wantedStr = splitContent[i].substring(2,splitContent[i].length - 3);
                        splitContent[i] = '<strong>' + wantedStr + '</strong>' + '.'
                    } else if (splitContent[i].endsWith('**,')) {
                        var wantedStr = splitContent[i].substring(2,splitContent[i].length - 3);
                        splitContent[i] = '<strong>' + wantedStr + '</strong>' + ','
                    }
                    else if (splitContent[i].endsWith('**')) {
                        var wantedStr = splitContent[i].substring(2,splitContent[i].length - 2);
                        splitContent[i] = '<strong>' + wantedStr + '</strong>'
                    }
                }
            }
            var result = cleanArray(splitContent.join(' ')
            .split(NEWLINE_PLACEHOLDER_TOKEN)).join('<br>')  // format new line placeholders
            console.log(result.length)
            if (result.length === 0) {
                return ''
            } else {
                return '<p>' + result + '</p>'
            }
        }

        function getChallengeInfo(id) {
            challengeService.getChallengeInfo(id)
                .then(
                    function(res) {
                        vm.challengeInfo = res.data;
                        vm.challengeInfo.description.content = convertBold(vm.challengeInfo.description.content)
                        vm.challengeInfo.description.input_format = convertBold(vm.challengeInfo.description.input_format)
                        vm.challengeInfo.description.output_format = convertBold(vm.challengeInfo.description.output_format)
                        vm.challengeInfo.description.sample_input = convertBold(vm.challengeInfo.description.sample_input)
                        vm.challengeInfo.description.sample_output = convertBold(vm.challengeInfo.description.sample_output)
                        vm.challengeInfo.description.constraints = convertBold(vm.challengeInfo.description.constraints)
                        vm.challengeInfo.description.explanation = convertBold(vm.challengeInfo.description.explanation)
                    },

                    function(err) {
                        console.log(err)
                    }
                )
        }

        function submitSolution(id) {
            var code = window.monaco.editor.getModels()[0].getValue();

            challengeService.submitSolution(id, code)
                .then(
                    function(res) {
                        vm.solutionInfo = res.data;
                        vm.solutionId = res.data.id;
                        getChallengeSolution(id, vm.solutionId)
                        challengeService.getUserInfo(sessionStorage['user_id'])
                        .then(
                            function(res) {
                                console.log('GOT USER INFO')
                                console.log(res.data)
                            }
                        )
                    },

                    function(err) {
                        console.log(err)
                    })
        }

        function getChallengeSolution(challengeId, solutionId) {
            challengeService.getChallengeSolution(challengeId, solutionId)
                .then(
                    function(res) {
                        console.log(res)
                        challengeService.getUserTestCases(challengeId, solutionId)
                        .then(
                            function(res) {
                                vm.testData = res.data
                                challengeService.getUserInfo(sessionStorage['user_id'])
                        .then(
                                function(res) {
                                    vm.userScore = res.data.score
                                    console.log(res.data.score)
                                    sessionStorage['user_score'] = res.data.score
                                }
                            )
                            }
                        )
                    },

                    function(err) {
                        console.log(err)
                    })
        }

        function getUserSubmissions(challengeId) {
            challengeService.getUserSubmissions(challengeId).then(
                function (res) {
                    vm.userSubmissions = res.data;
                },
                function(error) {
                    console.log(error);
                }
            )
        }


        function goToChallenge(id) {
            vm.showEditor = true;
            vm.showCategoryChallenges = false;
            vm.showLatestAttepmts = false;
            vm.testData = undefined;
            getChallengeInfo(id)
            console.log('WENT TO CHALLENGE!')
            angular.element(document).ready(function() {
                require.config({ paths: { 'vs': 'node_modules/monaco-editor/min/vs' }});
                require(['vs/editor/editor.main'], function() {
                    var editor = monaco.editor.create(document.getElementById('challenge-editor'), {
                        value: [
                            "__author__ = '" + sessionStorage['username'] + "'",
                            "",
                            "",
                            "def main():",
                            "    # Write your code here!",
                            "    pass",
                            "",
                            "",
                            "if __name__ == '__main__':",
                                "    main()"
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


            //$location.path('/challenge');
        }

        function logout() {
            sessionStorage.clear();
        }

        vm.getWidth = function() {
            return window.innerWidth;
        }

        $scope.$watch(vm.getWidth, function(newValue, oldValue) {
            if (newValue >= mobileView) {
                if (angular.isDefined($cookies.get('toggle'))) {
                    vm.toggle = ! $cookies.get('toggle') ? false : true;
                } else {
                    vm.toggle = true;
                }
            } else {
                vm.toggle = false;
            }

        });

        vm.toggleSidebar = function() {
            vm.toggle = !vm.toggle;
            $cookies.put('toggle', vm.toggle);
        };
        vm.showSubCategories = function () {
            vm.subCategoriesAreShown = !vm.subCategoriesAreShown
            $cookies.put('subCategoriesAreShown', vm.subCategoriesAreShown);
        }
        vm.toggle = false;
        vm.subCategoriesAreShown = false;
        window.onresize = function() {
            $scope.$apply();
        };
    }
}())
