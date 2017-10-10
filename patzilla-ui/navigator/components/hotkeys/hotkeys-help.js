// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG
require('jquery.shorten.1.0');
require('keyboarder/keyboarder.js');
require('keyboarder/keyboarder.css');
require('bs3-list-group');

HotkeysHelpView = Marionette.ItemView.extend({

    template: require('./hotkeys-help.html'),

    initialize: function() {
        console.log('HelpHotkeysView.initialize');
    },

    onDomRefresh: function() {
        console.log('HelpHotkeysView.onDomRefresh');
        $(".expandable").shorten({showChars: 0, moreText: 'more', lessText: 'less'});
    },

});
