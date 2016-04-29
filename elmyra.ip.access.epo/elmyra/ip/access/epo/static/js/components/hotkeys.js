// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG

HotkeysPlugin = Marionette.Controller.extend({

    initialize: function(options) {
        console.log('HotkeysPlugin.initialize');
        this.app = options.app;
    },

    setup_hotkeys: function() {

        var _this = this;

        // ------------------------------------------
        //   hotkeys
        // ------------------------------------------

        // submit on meta+enter
        $('#query').on('keydown', null, 'meta+return', function() {
            _this.app.perform_search({reviewmode: false, flavor: 'cql'});
        });
        $('#query').on('keydown', null, 'ctrl+return', function(event) {
            _this.app.perform_search({reviewmode: false, flavor: 'cql'});
        });

        // submit on meta+enter
        $('#numberlist').on('keydown', null, 'meta+return', function() {
            _this.app.perform_numberlistsearch();
        });

        // open cql field chooser
        $('#query').on('keydown', null, 'alt+ctrl+f', function(event) {
            event.preventDefault();
            $('#cql-field-chooser').select2('open');
            $('#cql-field-chooser').unbind('select2-close');
            $('#cql-field-chooser').on('select2-close', function(event) {
                window.setTimeout(function() {
                    $('#query').focus();
                }, 100);
            });
        });

        // zoom input field
        $('input').on('keydown', null, 'shift+return', function(event) {
            event.preventDefault();
            $(this).parent().find('.add-on.add-on-zoom').click();
        });

        _([document, '#query', '#numberlist', 'input']).each(function (selector) {
            _this.querybuilder_hotkeys(selector);
        });

        // add/remove/rate the document in viewport to/from basket
        $(document).on('keydown', null, '+', function() {
            _this.app.viewport.document_add_basket();
        });
        $(document).on('keydown', null, 'insert', function() {
            _this.app.viewport.document_rate(1);
        });

        $(document).on('keydown', null, '-', function() {
            _this.app.viewport.document_remove_basket();
        });
        $(document).on('keydown', null, 'r', function() {
            _this.app.viewport.document_remove_basket();
        });
        $(document).on('keydown', null, 'del', function() {
            _this.app.viewport.document_remove_basket();
        });
        $(document).on('keydown', null, 'ctrl+d', function() {
            _this.app.viewport.document_remove_basket();
        });

        $(document).on('keydown', null, '0', function() {
            _this.app.viewport.document_rate(null, true);
        });
        $(document).on('keydown', null, 'd', function() {
            _this.app.viewport.document_rate(null, true);
        });
        $(document).on('keydown', null, '1', function() {
            _this.app.viewport.document_rate(1);
        });
        $(document).on('keydown', null, '2', function() {
            _this.app.viewport.document_rate(2);
        });
        $(document).on('keydown', null, '3', function() {
            _this.app.viewport.document_rate(3);
        });


        var scroll_smooth = _this.app.ui.scroll_smooth;

        // snap scrolling to our items (space key)
        $(document).on('keydown', null, null, function(event) {

            if (event.keyCode == 32 && !_(['input', 'textarea']).contains(event.target.localName)) {
                event.preventDefault();

                // scroll to the best next target element
                if (event.shiftKey == false) {
                    scroll_smooth(_this.app.viewport.next_item({paging: true}));

                // scroll to the best previous target element
                } else if (event.shiftKey == true) {
                    scroll_smooth(_this.app.viewport.previous_item({paging: true}));
                }

            }
        });
        $(document).on('keydown', null, 'pagedown', function(event) {
            event.preventDefault();
            scroll_smooth(_this.app.viewport.next_item({paging: true}));
        });
        $(document).on('keydown', null, 'pageup', function(event) {
            event.preventDefault();
            scroll_smooth(_this.app.viewport.previous_item({paging: true}));
        });


        // navigate the Biblio, Desc, Claims with left/right arrow keys
        $(document).on('keydown', null, 'right', function(event) {
            event.preventDefault();
            var tab_chooser = _this.app.viewport.get_document().find('.document-actions .document-details-chooser').first();
            var active_button = tab_chooser.find('button.active');
            var next = active_button.next('button');
            if (!next.length) {
                next = active_button.siblings('button').first();
            }
            next.tab('show');
        });
        $(document).on('keydown', null, 'left', function(event) {
            event.preventDefault();
            var tab_chooser = _this.app.viewport.get_document().find('.document-actions .document-details-chooser').first();
            var active_button = tab_chooser.find('button.active');
            var next = active_button.prev('button');
            if (!next.length) {
                next = active_button.siblings('button').last();
            }
            next.tab('show');
        });


        // navigate the drawings carousel with shift+left/right arrow keys
        $(document).on('keydown', null, 'shift+right', function(event) {
            event.preventDefault();
            var drawings_carousel = _this.app.viewport.get_document().find('.drawings-carousel').first();
            var carousel_button_more = drawings_carousel.find('.carousel-control.right');
            carousel_button_more.trigger('click');
        });
        $(document).on('keydown', null, 'shift+left', function(event) {
            event.preventDefault();
            var drawings_carousel = _this.app.viewport.get_document().find('.drawings-carousel').first();
            var carousel_button_more = drawings_carousel.find('.carousel-control.left');
            carousel_button_more.trigger('click');
        });


        // open pdf on "shift+p"
        $(document).on('keydown', null, 'shift+p', function(event) {
            event.preventDefault();
            var anchor = _this.app.viewport.get_document().find('a.anchor-pdf');
            anchor[0].click();
        });


        // links to various patent offices
        // open Espacenet on "shift+e"
        $(document).on('keydown', null, 'shift+e', function(event) {
            event.preventDefault();
            var anchor = _this.app.viewport.get_document().find('a.anchor-biblio-espacenet');
            anchor[0].click();
        });
        // open DEPATISnet on "shift+d"
        $(document).on('keydown', null, 'shift+d', function(event) {
            event.preventDefault();
            var anchor = _this.app.viewport.get_document().find('a.anchor-biblio-depatisnet');
            anchor[0].click();
        });
        // open epo register information on "shift+alt+e"
        $(document).on('keydown', null, 'alt+shift+e', function(event) {
            event.preventDefault();
            _this.app.viewport.get_document().find('a.anchor-register-epo')[0].click();
        });
        // open dpma register information on "shift+alt+d"
        $(document).on('keydown', null, 'alt+shift+d', function(event) {
            event.preventDefault();
            _this.app.viewport.get_document().find('a.anchor-register-dpma')[0].click();
        });
        // open ccd on "shift+c"
        $(document).on('keydown', null, 'shift+c', function(event) {
            event.preventDefault();
            _this.app.viewport.get_document().find('a.anchor-ccd')[0].click();
        });


        // open help on "h"
        $(document).on('keydown', null, 'h', function(event) {
            event.preventDefault();
            var baseurl = _this.app.config.get('baseurl');
            var url = baseurl + '/help';
            window.open(url);
        });

    },

    querybuilder_hotkeys: function(selector) {

        var _this = this;

        // user interface flavor chooser
        $(selector).on('keydown', null, 'ctrl+shift+c', function(event) {
            $('#querybuilder-flavor-chooser button[data-value="comfort"]').tab('show');
        });
        $(selector).on('keydown', null, 'ctrl+shift+x', function(event) {
            $('#querybuilder-flavor-chooser button[data-value="cql"]').tab('show');
        });
        $(selector).on('keydown', null, 'ctrl+shift+n', function(event) {
            $('#querybuilder-flavor-chooser button[data-value="numberlist"]').tab('show');
        });

        // datasource selector
        $(selector).on('keydown', null, 'ctrl+shift+e', function(event) {
            $('#datasource button[data-value="ops"]').button('toggle');
            _this.app.set_datasource('ops');
        });
        $(selector).on('keydown', null, 'ctrl+shift+d', function(event) {
            $('#datasource button[data-value="depatisnet"]').button('toggle');
            _this.app.set_datasource('depatisnet');
        });
        if (opsChooserApp.config.get('google_allowed')) {
            $(selector).on('keydown', null, 'ctrl+shift+g', function(event) {
                var google_button = $('#datasource button[data-value="google"]');
                google_button.show();
                google_button.button('toggle');
                _this.app.set_datasource('google');
            });
        }
        if (opsChooserApp.config.get('ftpro_enabled')) {
            $(selector).on('keydown', null, 'ctrl+shift+f', function(event) {
                $('#datasource button[data-value="ftpro"]').button('toggle');
                _this.app.set_datasource('ftpro');
            });
        }
        if (opsChooserApp.config.get('ifi_enabled')) {
            $(selector).on('keydown', null, 'ctrl+shift+i', function(event) {
                $('#datasource button[data-value="ifi"]').button('toggle');
                _this.app.set_datasource('ifi');
            });
        }
        $(selector).on('keydown', null, 'ctrl+shift+r', function(event) {
            _this.app.basketModel.review();
        });

    },

    querybuilder_zoomed_hotkeys: function(selector, regular_element) {
        // submit on meta+enter
        $(selector).unbind('keydown');
        $(selector).on('keydown', null, 'meta+return', function() {
            $("#querybuilder-comfort-form").submit();
        });
        $(selector).on('keydown', null, 'ctrl+return', function(event) {
            $("#querybuilder-comfort-form").submit();
        });
        $(selector).on('keydown', null, 'shift+return', function(event) {
            event.preventDefault();
            opsChooserApp.queryBuilderView.comfort_form_zoomed_to_regular_data();
            opsChooserApp.queryBuilderView.comfort_form_zoomed_to_regular_ui(regular_element);
        });
    },

});

// setup plugin
opsChooserApp.addInitializer(function(options) {
    this.hotkeys = new HotkeysPlugin({app: this});

    this.listenTo(this, 'application:ready', function() {
        this.hotkeys.setup_hotkeys();
    });

});
