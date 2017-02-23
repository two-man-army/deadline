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


        //vm.getMainChallenges = getMainChallenges;
        vm.getSubCategoryChallenges = getSubCategoryChallenges;
        vm.showLatestAttepmts = true;
        vm.showCategoryChallenges = false;
        vm.showEditor = false;
        vm.goToChallenge = goToChallenge
        getMainCategories()
        getLatestAttemptedChallenges()

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

        function getChallengeInfo(id) {
            challengeService.getChallengeInfo(id)
                .then(
                    function(res) {
                        vm.challengeInfo = res.data;
                        console.log(vm.challengeInfo)
                    },

                    function(err) {
                        console.log(err)
                    }
                )
        }

        function submitSolution(id) {
            challengeService.submitSolution(id)
                .then(
                    function(res) {
                        console.log(res)
                    },

                    function(err) {
                        console.log(err)
                    })
        }

        function goToChallenge(id) {
            vm.showEditor = true;
            vm.showCategoryChallenges = false;
            getChallengeInfo(id)

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


            //$location.path('/challenge');
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
