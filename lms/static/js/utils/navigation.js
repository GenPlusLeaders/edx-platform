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
                navigation.listenForClick();
                navigation.listenForKeypress();
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
                var button = navigation.getActiveIndex();

                navigation.closeAccordions();

                if (button !== null) {
                    navigation.setupCurrentAccordionSection(button);
                }
            },

            listenForClick: function() {
                $('.accordion .dropdown-menu').on('click', '.button-chapter', function(event) {
                    event.preventDefault();

                    var $button = $(event.currentTarget),
                        section = "#" + $button.attr('data-section-id');

                    if($button.hasClass('locked')) {
                      event.stopPropagation();
                      return false;
                    }

                    navigation.closeAccordions($button, section);
                    navigation.openAccordion($button, section, true);
                    navigation.updateDropDownButton($button);
                });
            },

            listenForKeypress: function() {
                $('.accordion').on('keydown', '.button-chapter', function(event) {
                    // because we're changing the role of the toggle from an 'a' to a 'button'
                    // we need to ensure it has the same keyboard use cases as a real button.
                    // this is useful for screenreader users primarily.
                    var currentButton  = $(this);
                    if (event.which == 32 && !currentButton.hasClass('locked')) { // spacebar
                        event.preventDefault();
                        $(event.currentTarget).trigger('click');
                    } else {
                        return true;
                    }
                });
            },

            closeAccordions: function(button, section) {
                var menu = $(section),
                    $sections = $('.chapter-content-container'),
                    toggle;

                $('.accordion .dropdown-menu .button-chapter').each(function(index, element) {
                    $toggle = $(element);
                    $sectionEl = $(section)

                    $toggle
                        .removeClass('is-open')
                        .attr('aria-expanded', 'false');

                    $toggle
                        .children('.group-heading')
                        .removeClass('active')

                    $sections.not(menu)
                        .removeClass('is-open')
                        .find('.chapter-menu')
                            .removeClass('is-open')
                            .slideUp();
                });
            },

            setupCurrentAccordionSection: function(button) {
                var section = "#" + $(button).attr('data-section-id');

                navigation.openAccordion(button, section);
                navigation.updateDropDownButton(button);
            },

            updateDropDownButton : function (button) {
              var buttonHtml = $(button).find('.group-heading').html();
              var $dropButton = $('#selectLessonsButton');

              if ($(button).hasClass('complete')) {
                $dropButton.addClass('complete')
              } else {
                $dropButton.removeClass('complete')
              }

              $dropButton
                .find('.text')
                .html(buttonHtml);
            },

            openAccordion: function(button, section, clicked = false) {
                var $sectionEl = $(section),
                    $buttonEl = $(button);

                $buttonEl
                    .addClass('is-open')
                    .attr('aria-expanded', 'true');

                $buttonEl
                    .children('.group-heading')
                    .addClass('active')

                $sectionEl
                    .addClass('is-open')
                    .find('.chapter-menu')
                        .addClass('is-open')
                        .slideDown(function() {
                          if (clicked) {
                            navigation.selectFirstUnit(section);
                            $('#selectLessonsButton').addClass('disabled');
                          }
                        });
            },

            selectFirstUnit: function (section) {
              var firstSubesctioUrl = $(section)
                                        .find('.menu-item')
                                        .first()
                                        .addClass('active')
                                        .find('.accordion-nav')
                                        .attr('href');
              if (firstSubesctioUrl) {
                window.location.href = firstSubesctioUrl;
              }
            }
        };

        return {
            init: navigation.init
        };
    }());

edx.util = edx.util || {};
edx.util.navigation = Navigation;
edx.util.navigation.init();
