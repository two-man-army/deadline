(function() {
    'use strict';

    angular
        .module('app.dashboard')
        .factory('dashboardService', dashboardService);

    dashboardService.$inject = ['$http', 'BASE_URL'];

    function dashboardService($http, BASE_URL) {
        var dashboardService = {
            getMainCategories: getMainCategories,
            getSubCategory: getSubCategory
        };

        return dashboardService;

        function getMainCategories() {
            return $http({
                method: 'GET',
                headers: {
                    'Authorization': 'Token ' + sessionStorage['authToken']
                },
                url: BASE_URL + 'challenges/categories/all'
            })
        }

        function getSubCategory(subCategoryName) {
            return $http({
                method: 'GET',
                headers: {
                    'Authorization': 'Token ' + sessionStorage['authToken']
                },
                url: BASE_URL + '/challenges/subcategories/' + subCategoryName
            })
        }
    }
}());
