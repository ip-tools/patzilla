// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG

UiController = Marionette.Controller.extend({
    initialize: function() {
        log('UiController.initialize');
    },

    setup_text_tools: function() {
        // auto-shorten some texts
        $(".very-short").shorten({showChars: 5, moreText: 'more', lessText: 'less'});
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
});

// setup controller
opsChooserApp.addInitializer(function(options) {
    this.ui = new UiController();
});
