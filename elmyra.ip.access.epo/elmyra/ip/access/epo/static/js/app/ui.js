// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG

UiController = Marionette.Controller.extend({

    initialize: function() {
        log('UiController.initialize');
    },

    setup_ui: function() {

        // ------------------------------------------
        //   generic
        // ------------------------------------------

        // apply popovers to all desired buttons
        $('.btn-popover').popover();

        this.setup_text_tools();

        // defaults for notification popups
        $.notify.defaults({className: 'info', showAnimation: 'fadeIn', hideAnimation: 'fadeOut', autoHideDelay: 4000, showDuration: 300});

        // logout button
        if (opsChooserApp.config.get('mode') == 'liveview') {
            $('.logout-button').hide();
        }

        // switch query interface flavor to expert mode when receiving query via url
        if (opsChooserApp.config.get('query')) {
            opsChooserApp.queryBuilderView.set_flavor('cql');
        }


        // ------------------------------------------
        //   cql query area
        // ------------------------------------------

        // set cursor to end of query string, also focuses element
        //$('#query').caret($('#query').val().length);


        // ------------------------------------------
        //   online help
        // ------------------------------------------

        // transform query: open modal dialog to choose transformation kind
        $('.link-help').click(function() {

            // v1: modal dialog
            //$('#help-modal').modal('show');

            // v2: different page
            var baseurl = opsChooserApp.config.get('baseurl');
            var url = baseurl + '/help';
            $(this).attr('href', url);
        });

    },

    setup_text_tools: function() {
        // auto-shorten some texts
        $(".very-short").shorten({showChars: 5, moreText: 'more', lessText: 'less'});
    },

    reset_content: function(options) {
        $('#alert-area').empty();
        $('#info-area').empty();
        $('#pagination-info').hide();
        options = options || {};
        if (!options.keep_pager) {
            $('.pager-area').hide();
        }
        if (options.documents) {
            opsChooserApp.documents.reset();
        }
    },

    indicate_activity: function(active) {
        if (active) {
            $('.idler').hide();
            $('.spinner').show();

        } else {
            $('.spinner').hide();
            $('.idler').show();
        }
    },

    do_element_visibility: function() {

        // hide all navigational- and action-elements when in print mode
        var MODE_PRINT = opsChooserApp.config.get('mode') == 'print';
        if (MODE_PRINT) {
            $('.do-not-print').hide();
        }

        // hide all navigational- and action-elements when in view-only mode
        var MODE_LIVEVIEW = opsChooserApp.config.get('mode') == 'liveview';
        if (MODE_LIVEVIEW) {
            $('.non-liveview').hide();
        }
    },

    do_elements_focus: function() {
        if (opsChooserApp.documents.length) {
            $('#patentnumber').blur();
            $('#query').blur();
        }
    },

    notify: function(message, options) {

        if (options.icon) {
            message = '<span class="icon ' + options.icon + ' icon-large"></span>' + '<p>' + message + '</p>';
        }
        if (!options.type) {
            options.type = 'notice';
        }

        //setTimeout( function() {

            // create the notification
            var notification = new NotificationFx({
                message : message,
                layout : 'attached',
                effect : 'bouncyflip',
                type :   options.type, // notice, warning, error, success
                onClose : function() {
                    //bttn.disabled = false;
                },
                //ttl: 100000,
            });

            // show the notification
            notification.show();

        //}, 1200 );

    },

    // perform animated scrolling
    scroll_smooth: function(target) {
        if ($(target).offset()) {
            $('html, body').animate({
                scrollTop: $(target).offset().top
            }, 500);
        }
    },

});

// setup controller
opsChooserApp.addInitializer(function(options) {
    this.ui = new UiController();

    this.listenTo(this, 'application:ready', function() {
        this.ui.setup_ui();
    });

    this.listenTo(this, 'results:ready', function() {
        this.ui.do_elements_focus();
    });

});
