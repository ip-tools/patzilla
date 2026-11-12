// -*- coding: utf-8 -*-
// (c) 2014,2017 Andreas Motl, Elmyra UG
'use strict';

// https://marionette.gitbooks.io/marionette-guides/content/en/approuter/
// https://marionette.gitbooks.io/marionette-guides/content/en/appendix/approuter/router.html
// https://marionette.gitbooks.io/marionette-guides/content/en/application/routing.html

require('patzilla.lib.backbone');
require('patzilla.lib.marionette');
require('patzilla.lib.bootstrap');
require('patzilla.navigator.style');

import Marionette from 'marionette';
//import AppRouter from 'marionette.approuter';


const HelpView = Marionette.View.extend({
    el: 'body',
    template: function() {},

    regions: {
        content: '#content-region',
    },

    hotkeys: function() {
        const {HotkeysHelpView} = require("patzilla.navigator.components.hotkeys/hotkeys-help");
        this.$('#title-container').text('Hotkeys overview');
        this.showChildView('content', new HotkeysHelpView());
    },

    ificlaims: function() {
        const {IFIClaimsHandbookView} = require("patzilla.access.ificlaims-help");
        this.$('#title-container').text('Benutzerhandbuch für die Suche bei IFI Claims');
        this.showChildView('content', new IFIClaimsHandbookView());
    },
});

const Router = AppRouter.extend({
    appRoutes: {
        'hotkeys': 'hotkeys',
        'ificlaims': 'ificlaims',
    },
});

$(function() {
    const helpView = new HelpView();
    new Router({controller: helpView});
    Backbone.history.start();
});
