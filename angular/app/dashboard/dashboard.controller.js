(function() {
    'use strict'

    angular.module('app.dashboard')
        .controller('DashboardController', DashboardController);

    DashboardController.$inject = ['$http', '$location', 'dashboardService']

    function DashboardController($http, $location, dashboardService) {
        var vm = this;
        vm.getMainChallenges = getMainChallenges;
        vm.getSubCategory = getSubCategory;

        function getMainCategories() {
            // Used to list all the categories and their sub categories
            dashboardService.getMainCategories().then(
                function(res) {
                    /* 
                        Categories is a list of Category objects
                        A Category object is the following:
                         {
                            "name":"Algorithms", 
                            "sub_categories":["Graphs", "Strings", "Recursion"]
                         }
                     */
                    var categories = res.data;
                    vm.categories = categories
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
    }
}())
