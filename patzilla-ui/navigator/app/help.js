// -*- coding: utf-8 -*-
// (c) 2014,2017 Andreas Motl, Elmyra UG

// https://marionette.gitbooks.io/marionette-guides/content/en/approuter/
// https://marionette.gitbooks.io/marionette-guides/content/en/appendix/approuter/router.html
// https://marionette.gitbooks.io/marionette-guides/content/en/application/routing.html

// Foundation
require('backbone.marionette');
require('bootstrap-2.3.2/css/bootstrap.css');
require('bootstrap-2.3.2/css/bootstrap-responsive.css');

require('patzilla.navigator.style');

// Patches to make the old Backbone Marionette 1.1.0 work with Webpack
Backbone.$   = window.jQuery;
Marionette.$ = window.jQuery;


var Controller = Marionette.Controller.extend({

    initialize: function() {
        console.log('Controller.initialize');
        this.options.regionManager = new Marionette.RegionManager({});
        this.options.regionManager.addRegion('content', '#content-region');
    },

    hotkeys: function() {
        require('../components/hotkeys/hotkeys-help.js');
        var rmanager = Marionette.getOption(this, 'regionManager');
        $('#title-container').html('Hotkeys overview');
        rmanager.get('content').show(new HotkeysHelpView());
    },
    ificlaims: function() {
        require('../../access/ificlaims-help.js');
        var rmanager = Marionette.getOption(this, 'regionManager');
        $('#title-container').html('Benutzerhandbuch für die Suche bei IFI Claims');
        rmanager.get('content').show(new IFIClaimsHandbookView());
    },
});


var Router = Marionette.AppRouter.extend({

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
NavigatorHelp = Backbone.Marionette.Application.extend({

    initialize: function() {
    },

    onStart: function(options) {
        console.info('NavigatorHelp:onStart');
        var router = new Router(options);
        Backbone.history.start();
    },

});

navigatorHelp = new NavigatorHelp({});

$(document).ready(function() {
    console.log("document.ready");
    navigatorHelp.start();
});
