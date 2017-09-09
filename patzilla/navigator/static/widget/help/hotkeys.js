// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG

HelpHotkeysView = Backbone.Marionette.ItemView.extend({

    template: "#help-hotkeys-template",

    initialize: function() {
        console.log('HelpHotkeysView.initialize');
    },

    onDomRefresh: function() {
        console.log('HelpHotkeysView.onDomRefresh');
        $(".expandable").shorten({showChars: 0, moreText: 'more', lessText: 'less'});
    },

});

navigatorHelp.addInitializer(function(options) {
    this.region_hotkeys.show(new HelpHotkeysView());
});
