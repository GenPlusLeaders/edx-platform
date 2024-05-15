var edx = edx || {},

    Navigation = (function() {
        var navigation = {

            init: function() {
                if ($('.accordion').length) {
                    navigation.loadAccordion();
                }
            },

            loadAccordion: function() {
                navigation.checkForCurrent();
                navigation.listenForChange();
                // navigation.listenForKeypress();
            },

            getActiveIndex: function() {
                var index = $('.accordion .button-chapter:has(.active)').index('.accordion .button-chapter'),
                    button = null;

                if (index > -1) {
                    button = $('.accordion .button-chapter:eq(' + index + ')');
                }

                return button;
            },

            checkForCurrent: function() {
              var section = '#' + $('.accordion').find('#select-lessons').val();
              navigation.openAccordion(section);
            },

            listenForChange: function() {
                $('.accordion').on('change', '#select-lessons', function(event) {
                    section = '#' + event.target.value;

                    navigation.closeAccordions();
                    navigation.openAccordion(section);
                });
            },

            listenForKeypress: function() {
                $('.accordion').on('keydown', '.button-chapter', function(event) {
                    // because we're changing the role of the toggle from an 'a' to a 'button'
                    // we need to ensure it has the same keyboard use cases as a real button.
                    // this is useful for screenreader users primarily.
                    if (event.which == 32) { // spacebar
                        event.preventDefault();
                        $(event.currentTarget).trigger('click');
                    } else {
                        return true;
                    }
                });
            },

            closeAccordions: function() {

                $('.chapter-content-container').each(function(index, element) {
                    $(element)
                        .removeClass('is-open')
                        .find('.chapter-menu')
                            .removeClass('is-open')
                            .slideUp();
                });
            },

            setupCurrentAccordionSection: function(button) {
                var section = $(button).next('.chapter-content-container');

                navigation.openAccordion(section);
            },

            openAccordion: function(section) {
                var $sectionEl = $('.accordion').find(section);

                $sectionEl
                    .addClass('is-open')
                    .find('.chapter-menu')
                        .addClass('is-open')
                        .slideDown();
            }
        };

        return {
            init: navigation.init
        };
    }());

edx.util = edx.util || {};
edx.util.navigation = Navigation;
edx.util.navigation.init();
