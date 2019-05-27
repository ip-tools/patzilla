// -*- coding: utf-8 -*-
// (c) 2013-2018 Andreas Motl <andreas.motl@ip-tools.org>

/**
 * --------------------
 * Bootstrap foundation
 * --------------------
 */

// Compatibility shims for ECMAScript 6 (Harmony)
require('es6-shim');

// CSS Element Queries: Element responsiveness for a modern web
var EQ = require('css-element-queries').ElementQueries;
$(window).ready(function() {
    console.info('window.load happened');
    EQ.init();
});


// Twitter Bootstrap 2.3.2
// TODO: Upgrade to more recent version
require('bootstrap-2.3.2/css/bootstrap.css');
require('bootstrap-2.3.2/css/bootstrap-responsive.css');
require('bootstrap-2.3.2/js/bootstrap-affix.js');
require('bootstrap-2.3.2/js/bootstrap-alert.js');
require('bootstrap-2.3.2/js/bootstrap-button.js');
require('bootstrap-2.3.2/js/bootstrap-carousel.js');
require('bootstrap-2.3.2/js/bootstrap-collapse.js');
require('bootstrap-2.3.2/js/bootstrap-dropdown.js');
require('bootstrap-2.3.2/js/bootstrap-modal.js');
require('bootstrap-2.3.2/js/bootstrap-scrollspy.js');

// Use bootstrap-tabs from Bootstrap 2.0.0
//require('bootstrap-2.3.2/js/bootstrap-tab.js');
//require('bootstrap-tab.js');
require('bootstrap-tab-button.js');

// Popover derives from Tooltip, so keep them in that order
require('bootstrap-2.3.2/js/bootstrap-tooltip.js');
require('bootstrap-2.3.2/js/bootstrap-popover.js');

require('bootstrap-2.3.2/js/bootstrap-transition.js');
require('bootstrap-2.3.2/js/bootstrap-typeahead.js');

// Font Awesome 3.2.1; TODO: Upgrade to more recent version
require('font-awesome/css/font-awesome.css');


// Global utilities
require('purl/purl');
require('patzilla.lib.jquery');
require('patzilla.lib.underscore');
require('patzilla.lib.backbone');
require('patzilla.lib.marionette');
_(window).extend(require('patzilla.lib.util'));

// Application utilities
require('patzilla.common.issuereporter');
_(window).extend(require('patzilla.navigator.util.linkmaker'));
_(window).extend(require('patzilla.navigator.util.patentnumbers'));

// Application
require('patzilla.navigator.app.config');
require('patzilla.navigator.app.application');
require('patzilla.navigator.app.layout');
require('patzilla.navigator.app.results');
require('patzilla.navigator.components.pagination');
require('patzilla.navigator.components.results-tabular');
require('patzilla.navigator.components.results-dialog');
var propagate_opaque_errors = require('patzilla.navigator.components.opaquelinks').propagate_opaque_errors;

// CSS Stylesheets
require('patzilla.navigator.style');

// Material Design Icons
require('patzilla.lib.mdc.material-icons');


/**
 * -----------------------------------
 * Bootstrap application configuration
 * -----------------------------------
 */
console.info('Load application configuration');

var navigatorConfiguration = new NavigatorConfiguration();
navigatorConfiguration.set(navigator_configuration);
navigatorConfiguration.set(window.request_hidden);
if (navigatorConfiguration.get('opaque.meta.status') != 'error') {
    navigatorConfiguration.history_pushstate();
}

var theme_settings = {};
_.extend(theme_settings, {config: navigatorConfiguration});
_.extend(theme_settings, navigator_theme);
var navigatorTheme = new NavigatorTheme(theme_settings);


/**
 * --------------------------
 * Bootstrap main application
 * --------------------------
 */

console.info('Load application core');

// Main application object
navigatorApp = new NavigatorApp({config: navigatorConfiguration, theme: navigatorTheme});

// Setup data source adapters
require('patzilla.access.depatech');
require('patzilla.access.depatisnet');
require('patzilla.access.epo.ops');
require('patzilla.access.ificlaims');
require('patzilla.access.sip');

// Setup user interface regions
navigatorApp.addRegions({
    mainRegion: "#root-region",
    queryBuilderRegion: "#querybuilder-region",
    basketRegion: "#basket-region",
    metadataRegion: "#ops-metadata-region",
    listRegion: "#ops-collection-region",
    paginationRegionTop: "#ops-pagination-region-top",
    paginationRegionBottom: "#ops-pagination-region-bottom",
});


// Main application user interface
navigatorApp.addInitializer(function(options) {

    this.listenToOnce(this, "application:init", function() {

        //this.theme = new ApplicationTheme({config: navigatorConfiguration});
        //log('this.applicationTheme:', this.applicationTheme);

        this.layoutView = new LayoutView();
        this.mainRegion.show(this.layoutView);

    });

});

// Universal helpers
navigatorApp.addInitializer(function(options) {
    this.issues = new IssueReporterGui();
    this.listenTo(this, 'application:ready', function() {
        this.issues.setup_ui();
    });
    this.listenTo(this, 'results:ready', function() {
        this.issues.setup_ui();
    });
});


// Initialize models
navigatorApp.addInitializer(function(options) {

    // Application domain model objects
    this.search = new OpsPublishedDataSearch();
    this.metadata = new OpsExchangeMetadata();
    this.documents = new OpsExchangeDocumentCollection();
    this.results = new ResultCollection();

    // Set hooks to toggle search input dirtyness
    this.listenTo(this, 'search:success', function(args) {
        this.metadata.dirty(false);
    });
    this.listenTo(this, 'search:failure', function(args) {
        this.metadata.dirty(true);
    });

});

// Initialize views
navigatorApp.addInitializer(function(options) {

    this.listenToOnce(this, "application:init", function() {

        // bind model objects to view objects
        this.metadataView = new MetadataView({
            model: this.metadata
        });
        this.collectionView = new OpsExchangeDocumentCollectionView({
            collection: this.documents
        });
        this.resultView = new ResultCollectionView({
            collection: this.results
        });

        this.paginationViewTop = new PaginationView({
            model: this.metadata
        });
        this.paginationViewBottom = new PaginationView({
            model: this.metadata,
            bottom_pager: true,
        });

        // bind view objects to region objects
        this.metadataRegion.show(this.metadataView);
        this.paginationRegionTop.show(this.paginationViewTop);
        this.paginationRegionBottom.show(this.paginationViewBottom);

    });

});

// activate anonymous basket (non-persistent/project-associated)
navigatorApp.addInitializer(function(options) {
    // remark: the model instance created here will get overwritten later
    //         by a project-specific basket when activating a project
    // reason: we still do it here for the case we decide to deactivate the project
    //         subsystem in certain modes (dunno whether this will work out)
    // update [2014-06-08]: deactivated anonymous basket until further
    //this.basket_activate(new BasketModel());
});


// Main component event wiring
navigatorApp.addInitializer(function(options) {

    // Application core, first stage boot process
    this.listenToOnce(this, 'application:boot', function() {

        console.info('Initialize application (application:boot)');

        this.setup_ui();

        // Compute and set optimal data source.
        this.bootstrap_datasource();

        // Activate regular list region right now to avoid double rendering on initial page load.
        this.listRegion.show(this.collectionView);

        // Hide pagination- and metadata-area to start from scratch.
        this.ui.reset_content();

        // Propagate opaque error messages to alert area
        propagate_opaque_errors();

        // Enter second stage boot process
        this.trigger('application:ready');

        this.ui.do_element_visibility();

    });


    // Activate project as soon it's loaded from the datastore
    this.listenTo(this, "project:ready", this.project_activate);


    // Results were fetched, take action
    this.listenTo(this, 'results:ready', function() {

        // commit metadata, this will trigger e.g. PaginationView rendering
        this.metadata.trigger('commit');

        // show documents (ops results) in collection view
        // explicitly switch list region to OPS collection view
        if (this.listRegion.currentView !== this.collectionView) {
            this.listRegion.show(this.collectionView);
        }

    });


});

// Kick off the search process triggered from query parameters
navigatorApp.addInitializer(function(options) {

    // V1: Kick off search after basket machinery has been loaded
    // V2: Kick off search regardless to make it work without storage et al.

    // Just wait for project activation since this is a dependency before running
    // a search because the query history is associated to the project.
    //this.listenToOnce(this, "project:ready", function() {
    this.listenToOnce(this, "application:ready", function() {

        // Propagate search modifiers from query parameters to search engine metadata
        var modifiers = this.config.get('modifiers');
        this.metadata.apply_modifiers(modifiers);

        // Propagate search modifiers from search engine metadata to user interface
        var query_data = this.metadata.get('query_data');
        if (query_data) {
            this.queryBuilderView.set_common_form_data(query_data);
        }

        // The ui loading and lag woes are ready after the basket was fully initialized
        this.listenToOnce(this, "basket:activated", function() {

            // Forward viewstate
            var options = {};
            if (query_data) {
                options.query_data = query_data;
            }

            // Run search
            this.perform_search(options);
        });

    });

});
