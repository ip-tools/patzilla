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

import Marionette from 'backbone.marionette';


const Controller = Marionette.Controller.extend({

    initialize: function() {
        console.log('Controller.initialize');
    },

    hotkeys: function() {
        const {HotkeysHelpView} = require("patzilla.navigator.components.hotkeys/hotkeys-help");
        $('#title-container').html('Hotkeys overview');
        navigatorHelp.showView(new HotkeysHelpView());
    },
    ificlaims: function() {
        const {IFIClaimsHandbookView} = require("patzilla.access.ificlaims-help");
        $('#title-container').html('Benutzerhandbuch für die Suche bei IFI Claims');
        navigatorHelp.showView(new IFIClaimsHandbookView());
    },
});


const Router = Marionette.AppRouter.extend({

    appRoutes: {
        'hotkeys':   'hotkeys',
        'ificlaims': 'ificlaims'
    },

    initialize: function() {
        console.log('Router.initialize');
        this.controller = new Controller({
            initialData: Marionette.getOption(this, 'initialData'),
        });
    },

});


// Main
const NavigatorHelp = Marionette.Application.extend({

    region: '#content-region',

    initialize: function() {
    },

    onStart: function(options) {
        console.info('NavigatorHelp:onStart');
        var router = new Router(options);
        Backbone.history.start();
    },

});

const navigatorHelp = new NavigatorHelp({});

$(function() {
    console.log("document.ready");
    navigatorHelp.start();
});
