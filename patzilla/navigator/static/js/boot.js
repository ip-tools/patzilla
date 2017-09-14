// -*- coding: utf-8 -*-
// (c) 2013-2017 Andreas Motl, Elmyra UG


/**
 * --------------------
 * Bootstrap foundation
 * --------------------
 */

console.info('Load foundation');

// Patches to make the old Backbone Marionette 1.1.0 work with Webpack
Backbone.$   = window.jQuery;
Marionette.$ = window.jQuery;

// Application core
console.info('Load application');
require('patzilla.app.main');


// Application components
console.info('Load application components');

// Essential application components
require('patzilla.app.core');
require('patzilla.app.ui');

// Semi-essential application components
require('patzilla.components.document');
// TODO: Currently, quite some core machinery relies on the querybuilder. Improve that!
require('patzilla.components.querybuilder');

// Keywords, comments and rating
require('patzilla.components.storage');
require('patzilla.components.project');
require('patzilla.components.keywords');
require('patzilla.components.basket');
require('patzilla.components.comment');

// Optional application components
require('patzilla.components.analytics');
require('patzilla.components.crawler');
require('patzilla.components.export');
require('patzilla.components.hotkeys');
require('patzilla.components.permalink');
require('patzilla.components.reading');
require('patzilla.components.viewport');
require('patzilla.components.waypoints');


// Bootstrap the application after registering all components
opsChooserApp.addInitializer(function(options) {
    this.listenToOnce(this, 'application:init', function() {
        this.trigger('application:boot');
    });
});
