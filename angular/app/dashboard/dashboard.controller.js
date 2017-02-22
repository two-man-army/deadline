(function() {
    'use strict'

    angular.module('app.dashboard')
        .controller('DashboardController', DashboardController);

    DashboardController.$inject = ['$scope', '$http', '$location', '$cookies', 'dashboardService']

    function DashboardController($scope, $http, $location, $cookies, dashboardService) {
        var mobileView = 992,
            vm = this;


        //vm.getMainChallenges = getMainChallenges;
        vm.getSubCategory = getSubCategory;
        getMainCategories()

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

        function getSubCategory(subCategoryName) {
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
                    var subcategory = res.data;
                    vm.subcategory = subcategory;
                    vm.challenges = subcategory.challenges;

                    // TODO: Display all challenges in the page
                },
                function(error) {
                    console.log(error)
                }
            )
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
        vm.toggle = false;

        window.onresize = function() {
            $scope.$apply();
        };
    }
}())
