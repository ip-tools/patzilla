// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG
'use strict';

require('jquery.shorten.1.0');
require('keyboarder/keyboarder.js');
require('keyboarder/keyboarder.css');

// Override key event listeners as no-ops, because they are not needed on the help page.
var elbody = document.getElementsByTagName('body')[0];
elbody.addEventListener("keydown", function(event) {
    event.stopImmediatePropagation();
}, true);
elbody.addEventListener("keyup", function(event) {
    event.stopImmediatePropagation();
}, true);

export const HotkeysHelpView = Marionette.ItemView.extend({

    template: require('./hotkeys-help.html'),

    initialize: function() {
        console.log('HelpHotkeysView.initialize');
    },

    onDomRefresh: function() {
        console.log('HelpHotkeysView.onDomRefresh');
        $(".expandable").shorten({showChars: 0, moreText: 'more', lessText: 'less'});
    },

});
