(function() {
    'use strict'

    angular.module('app.layout')
        .controller('LayoutFormController', LayoutFormController);

    function LayoutFormController() {
        var vm = this;

        angular.element('.form').find('input, textarea').bind('keyup blur focus', function (e) {
            var $this = angular.element(this),
                label = $this.prev('label');

            if (e.type === 'keyup') {
                if ($this.val() === '') {
                    label.removeClass('active highlight');

                } else {
                    label.addClass('active highlight');
                }

            } else if (e.type === 'blur') {
                if( $this.val() === '' ) {
                    label.removeClass('active highlight');

                } else {
                    label.removeClass('highlight');
                }

            } else if (e.type === 'focus') {
                if( $this.val() === '' ) {
                    label.removeClass('highlight'); 

                } else if( $this.val() !== '' ) {
                    label.addClass('highlight');
                }
            }

        });

        vm.switchForm = function($event) {
            var el = angular.element($event.currentTarget),
                target;

            $event.preventDefault()

            el.parent().addClass('active');
            el.parent().siblings().removeClass('active');

            target = el.attr('href');

            angular.element('.tab-content > div').not(target).hide();
            angular.element(target).fadeIn(600);
        }
    }
}())
