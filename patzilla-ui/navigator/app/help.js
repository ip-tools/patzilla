// -*- coding: utf-8 -*-
// (c) 2014,2017 Andreas Motl, Elmyra UG
'use strict';

// https://marionette.gitbooks.io/marionette-guides/content/en/approuter/
// https://marionette.gitbooks.io/marionette-guides/content/en/appendix/approuter/router.html
// https://marionette.gitbooks.io/marionette-guides/content/en/application/routing.html

require('backbone.marionette');
require('bootstrap/dist/css/bootstrap.min.css');
require('patzilla.navigator.style');

// Patches to make the old Backbone Marionette 1.1.0 work with Webpack
Backbone.$   = window.jQuery;
Marionette.$ = window.jQuery;


const Controller = Marionette.Controller.extend({

    initialize: function() {
        console.log('Controller.initialize');
        this.options.regionManager = new Marionette.RegionManager({});
        this.options.regionManager.addRegion('content', '#content-region');
    },

    hotkeys: function() {
        const {HotkeysHelpView} = require("patzilla.navigator.components.hotkeys/hotkeys-help");
        var rmanager = Marionette.getOption(this, 'regionManager');
        $('#title-container').html('Hotkeys overview');
        rmanager.get('content').show(new HotkeysHelpView());
    },
    ificlaims: function() {
        const {IFIClaimsHandbookView} = require("patzilla.access.ificlaims-help");
        var rmanager = Marionette.getOption(this, 'regionManager');
        $('#title-container').html('Benutzerhandbuch für die Suche bei IFI Claims');
        rmanager.get('content').show(new IFIClaimsHandbookView());
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
const NavigatorHelp = Backbone.Marionette.Application.extend({

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
