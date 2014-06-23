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
});

// setup controller
opsChooserApp.addInitializer(function(options) {
    this.ui = new UiController();
});
