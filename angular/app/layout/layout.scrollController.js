(function() {
    'use strict'

    angular.module('app.layout')
        .controller('LayoutScrollController', LayoutScrollController);

    LayoutScrollController.$inject = ['$window']

    function LayoutScrollController($window) {
        angular.element($window).bind('scroll', function() {
            //get scroll position
            var topWindow = $window.pageYOffset;

            //multipl by 1.5 so the arrow will become transparent half-way up the page
            var topWindow = topWindow * 1.5;

            //get height of window
            var windowHeight = angular.element($window).height();

            //set position as percentage of how far the user has scrolled 
            var position = topWindow / windowHeight;
            //invert the percentage
            position = 1 - position;

            //define arrow opacity as based on how far up the page the user has scrolled
            //no scrolling = 1, half-way up the page = 0
            $('.scroll-arrow').css('opacity', position);

        });


        $('a[href*="#login-form"]:not([href="#"])').click(function() {
            if (location.pathname.replace(/^\//, '') == this.pathname.replace(/^\//, '') && location.hostname == this.hostname) {
                var target = $(this.hash);
                target = target.length ? target : $('[name=' + this.hash.slice(1) + ']');

                if (target.length) {
                    $('html, body').animate({
                        scrollTop: target.offset().top
                    }, 1000);
                    return false;
                }
            }
        });
    }
}())
