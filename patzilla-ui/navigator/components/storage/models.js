// -*- coding: utf-8 -*-
// (c) 2018 Andreas Motl <andreas.motl@ip-tools.org>
//import { SmartCollectionMixin } from 'patzilla.lib.backbone';
//import { MarionetteFuture } from 'patzilla.lib.marionette';
require('patzilla.lib.backbone');
require('patzilla.lib.marionette');
require('patzilla.navigator.components.storage');


ProfileRecord = Backbone.RelationalModel.extend({

    sync: Backbone.localforage.sync('ApplicationProfile'),

    defaults: {
        key: 'default',
        intents: {}
    },

    initialize: function() {
        //log('ProfileRecord::initialize');
        //this.listenTo(this, 'all', this.on_event);
    },


    // Debugging helpers
    on_event: function(event, model, value, foo, bar) {
        log('ProfileRecord event:', event, model, value, foo, bar);
    }

});


ProfileCollection = Backbone.Collection.extendEach(SmartCollectionMixin, {
    sync: Backbone.localforage.sync('ApplicationProfile'),
    find: Backbone.localforage.find,
    model: ProfileRecord,

    // initialize model
    initialize: function() {
        //log('ProfileCollection::initialize');
        //this.listenTo(this, 'all', this.on_event);
    },

    on_event: function(event, model, value, foo, bar) {
        log('ProfileCollection event:', event, model, value, foo, bar);
    },

});


ApplicationProfile = Backbone.Marionette.Controller.extendEach(MarionetteFuture, {

    // We just support a single application profile by now.
    profile_name: 'default',

    initialize: function(options) {

        console.log('ApplicationProfile::initialize');

        // The application object.
        this.application = this.getOption('application');

        // The current profile we are operating on.
        this.model = undefined;

        // Setup component.
        this.setup();

        // Register ourselves with the application machinery.
        this.application.register_component('profile');

    },

    setup: function() {

        // What's the profile name?
        var profile_name = this.getOption('profile_name');

        // Debugging.
        log('[ApplicationProfile::setup] Loading profile:', profile_name);

        // Setup the data store.
        this.store = new ProfileCollection();

        // Fetch data from store.
        var _this = this;
        this.store.fetch({
            success: function(response) {
                _this.model = _this.store.by_key(profile_name);
                log('[ApplicationProfile::setup] Loaded profile:', _this.model.attributes);
            }
        });

    },

    get_intent: function(name) {

        log('ApplicationProfile::get_intent');
        var value = this.model.get('intents')[name];

        return value;
    },

    set_intent: function(name, value) {
        log('ApplicationProfile::set_intent', name, value);
        this.model.get('intents')[name] = value;
        this.model.save();
    },

});


// Setup addon
navigatorApp.addInitializer(function(options) {

    // Start application profile component after the data store has been initialized.
    this.listenTo(this, 'localforage:ready', function() {
        this.profile = new ApplicationProfile({application: this});
    });

});
