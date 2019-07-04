// -*- coding: utf-8 -*-
// (c) 2018 Andreas Motl <andreas.motl@ip-tools.org>
'use strict';

import { SmartCollectionMixin } from 'patzilla.lib.backbone';
import { MarionetteFuture, NamedViewController } from 'patzilla.lib.marionette';
import { StackCheckboxWidget, StackOpenerWidget, StackMenuWidget } from './stack-ui.js';

export { StackDisplayMode };

require('backbone-dom-to-view');
require('patzilla.navigator.components.storage');


const StackDisplayMode = {
    RATING: 'mode-rating',
    STACK:  'mode-stack',
};


const StackModel = Backbone.RelationalModel.extend({

    sync: Backbone.localforage.sync('StackEntry'),

    // Automatically maintain "created" and "modified" model attributes
    timestamped: true,

    relations: [
    ],

    defaults: {
        key: undefined,
        selected: undefined,
    },

    initialize: function() {
        //log('StackModel::initialize');
    },

});


const StackCollection = Backbone.Collection.extendEach(SmartCollectionMixin, {
    sync: Backbone.localforage.sync('StackEntry'),
    find: Backbone.localforage.find,
    model: StackModel,

    // initialize model
    initialize: function() {
        //log('StackCollection::initialize');
    },

});


const StackManager = NamedViewController.extend({

    // The name under which this controller
    // register itself with the designated view.
    name: 'stack_manager',

    // The model field to use as ground truth for
    // whether an item is selected or not.
    modelField: 'selected',

    // Which text label to display besides the checkbox
    textLabel: 'Select',

    // Resolve the closest Backbone view
    viewport_resolver: function() {
        var element = $('.document-anchor:in-viewport').closest('.ops-collection-entry');
        return element;
    },

    initialize: function(options) {

        //log('StackManager::initialize');

        //this.collection = options.collection;
        this.model = options.model;
        this.view = options.view;

        // https://makandracards.com/makandra/22121-how-to-call-overwritten-methods-of-parent-classes-in-backbone-js
        // https://stackoverflow.com/questions/15987490/backbone-view-inheritance-call-parent-leads-to-recursion/15988038#15988038
        StackManager.__super__.initialize.apply(this, arguments);

        this.setup_ui();

        // Debugging: Activate stack selection mode immediately
        //this.show_stack();

    },

    setup_ui: function() {

        // Find DOM elements
        var rating_stack_container = this.view.$el.find('.document-rating-stack');
        this.rating_element = rating_stack_container.find('.document-rating-widget');

        // setup descendant views
        // https://github.com/rafeememon/marionette-checkbox-behavior/blob/master/test/checkbox-behavior-test.js
        this.checkbox_widget = new StackCheckboxWidget({
            model: this.model,
            modelField: this.modelField,
            textLabel: this.textLabel,
        });

        // Wire model events to user interface updates
        this.listenTo(this.model, 'change:selected', this.save_model);
        this.listenTo(this.model, 'change:selected', this.update_sidecar_indicator);

        // When model gets destroyed, shutdown the user interface.
        this.listenTo(this.model, 'destroy', this.close);

        // Show/hide vertical marker on the document's left side.
        this.update_sidecar_indicator();

        // Debug events
        /*
        this.listenTo(this, 'all', this.on_manager_event);
        this.listenTo(this.model, 'all', this.on_model_event);
        this.listenTo(this.checkbox_widget, 'all', this.on_widget_event);
        */

    },

    close: function() {
        //log('StackManager::close');

        // Signal we are currently in progress of destroying ourselves.
        // This will be used from StackManager::save_model.
        this.shutting_down = true;

        // Shutdown user interface components.
        this.close_checkbox();

        StackManager.__super__.close.apply(this);

    },

    // Manipulate the data model
    select: function() {
        this.model.set('selected', true);
    },
    unselect: function() {
        this.model.set('selected', false);
    },

    // Persist model
    save_model: function() {
        log('StackManager::save_model');

        // Skip saving if we are currently shutting down.
        if (this.shutting_down) {
            return;
        }

        // Persist model.
        this.model.save();
    },

    // Update another UI element based on data model
    update_sidecar_indicator: function() {

        // Read model
        var selected = !!this.model.get(this.modelField);

        // Update sidecar view
        var sidecar_element = this.view.$el;
        if (selected) {
            sidecar_element.addClass('document-stack-decorated');
        } else {
            sidecar_element.removeClass('document-stack-decorated');
        }
    },

    // Manipulate the user interface
    activate: function(mode) {
        if (mode == StackDisplayMode.STACK) {
            this.show_stack();
        } else {
            this.show_rating();
        }
    },
    show_stack: function() {
        this.rating_element.hide('fast');
        this.show_checkbox();
    },
    show_rating: function() {
        this.close_checkbox();
        this.rating_element.show('fast');
    },

    show_checkbox: function() {
        this.view.region_stack_checkbox.show(this.checkbox_widget);
    },
    close_checkbox: function() {
        var region_stack_checkbox = this.view.region_stack_checkbox;
        if (region_stack_checkbox) {
            region_stack_checkbox.reset();
        }
    },

    // Debugging helpers
    on_manager_event: function(event) {
        log('StackManager::on_manager_event', event);
    },
    on_model_event: function(event) {
        log('StackManager::on_model_event', event);
    },
    on_widget_event: function(event) {
        log('StackManager::on_widget_event', event);
    },

});


const StackPlugin = Backbone.Marionette.Controller.extendEach(MarionetteFuture, {

    manager_class: StackManager,

    initialize: function(options) {

        log('StackPlugin::initialize');

        // The application object.
        this.application = this.getOption('application');

        // Setup the data store
        this.listenTo(this.application, 'localforage:ready', function() {
            log('localforage:ready-stack');
            this.setup(options);
        });

        // Register ourselves with the application machinery.
        this.application.register_component('stack');

    },

    setup: function(options) {

        log('StackPlugin::setup');

        // The list view the items are rendered into,
        // so we are listening to its 'itemview:item:rendered' events.
        this.view = this.getOption('view');

        // Setup the data store.
        this.store = new StackCollection();

        // Fetch data from store.
        this.store.fetch({success: function(response) {
            log('StackPlugin: fetch ready');
            // FIXME: nobody currently waits for this to happen
        }});

        // Attach a new item-specific manager after each itemview got rendered.
        this.listenTo(this.view, 'itemview:item:rendered', function(itemview) {

            // This guy will manage the widget to model to environment interactions
            this.make_stack_manager(itemview);

        });

        // Apply intents after the whole listview has rendered.
        this.listenTo(this.view, 'render', this.intent_hook);

        // TODO: Register global hotkeys
        this.bind_hotkeys();
    },

    intent_hook: function() {
        var mode = this.get_intent_mode();
        log('StackPlugin::intent_hook mode:', mode);
        if (mode) {
            this.update_content_view(mode);
        }
    },

    get_intent_mode: function() {
        if (this.application.component_enabled('profile')) {
            var mode = this.application.profile.get_intent('work.mode');
            return mode;
        }
    },

    set_intent_mode: function(mode) {
        // Remember this choice in application state, so it will
        // persist across paging actions and even page reloads.
        if (this.application.component_enabled('profile')) {
            this.application.profile.set_intent('work.mode', mode);
        }
    },

    make_stack_manager: function(view) {
        //log('StackPlugin::make_stack_manager');

        // Get unique key of model
        // `get_unique_key()` is a highlevel application convention
        var key = view.model.get_unique_key();

        // Load model from store
        var model = this.store.by_key(key);

        var manager = new this.manager_class({
            //collection: this.store,
            model: model,
            view: view,
        });
        return manager;
    },

    // Register global hotkeys
    bind_hotkeys: function() {
        this.bind_hotkeys_viewport();
        this.bind_hotkeys_selection();
    },

    bind_hotkeys_viewport: function() {
        var _this = this;
        $(document).on('keydown', null, 'S', function() {

            try {
                // Display checkbox and obtain manager object
                var manager = _this.activate_by_viewport(StackDisplayMode.STACK);

                // Select item
                manager.select();

            } catch (error) {
                console.error('Selecting document failed:', error);
            }
        });

        $(document).on('keydown', null, 'X', function() {

            try {
                // Display checkbox and obtain manager object
                var manager = _this.activate_by_viewport(StackDisplayMode.STACK);

                // Unselect item
                manager.unselect();

            } catch (error) {
                console.error('Unselecting document failed:', error);
            }
        });

    },

    bind_hotkeys_selection: function() {
        var _this = this;
        $(document).off('keydown', null, 'alt+r');
        $(document).on('keydown', null, 'alt+r', _.bind(this.reset, this));
    },

    reset: function() {

        // Reset models.
        var buffer = [];
        this.store.forEach(function(item) {
            buffer.push(item);
        });
        _.each(buffer, function(item, index) {
            item && item.destroy();
        });
        this.store.reset();

        // Reset user interface.
        var _this = this;
        this.view.children.forEach(function(itemview) {
            _this.make_stack_manager(itemview);
        });
    },

    // Activate single element
    activate_by_element: function(element, mode) {
        var stack = this.manager_class.prototype.by_element(element);
        if (!stack) return;
        stack.activate(mode);
        return stack;
    },

    // Activate single element currently in viewport
    activate_by_viewport: function(mode) {
        var stack = this.manager_class.prototype.by_viewport();
        if (!stack) return;
        stack.activate(mode);
        return stack;
    },


    // Activate all elements
    activate_all_mode: function(mode) {
        // Remember this choice in application state, so it will
        // persist across paging actions and even page reloads.
        this.set_intent_mode(mode);

        return this.update_content_view(mode);
    },
    activate_all_stack: function() {
        this.activate_all_mode(StackDisplayMode.STACK);
    },
    activate_all_rating: function() {
        this.activate_all_mode(StackDisplayMode.RATING);
    },


    // Update the user interface
    update_content_view: function(mode) {

        // Iterate list of visible result elements and activate
        // the designated mode on each of them.
        var _this = this;
        this.view.children.forEach(function(itemview) {
            _this.activate_by_element(itemview.$el, mode);
        });

        this.update_opener_view(mode);
    },

    update_opener_view: function(mode) {

        //log('StackPlugin::update_opener_view mode:', mode);

        mode = mode || this.get_intent_mode();

        // Toggle stack opener widget
        if (mode == StackDisplayMode.STACK) {
            this.show_opener();
        } else if (mode == StackDisplayMode.RATING) {
            this.close_opener();
        }
    },

    // Toggle stack opener widget
    show_opener: function() {

        // Hack for destroying the old instance.
        this.close_opener();

        // Create stack menu opener button.
        var opener_widget = new StackOpenerWidget({
            collection: this.store,
        });

        // When clicked, open the menu widget.
        opener_widget.listenTo(opener_widget, 'view:clicked', _.bind(this.open_menu, this));

        // Render and show the button in its designated region.
        this.application.metadataView.region_stack_opener.show(opener_widget);
    },

    close_opener: function() {
        // Close menu opener button by shutting down its region.
        this.application.metadataView.region_stack_opener.reset();
    },

    open_menu: function(event) {

        // Close menu widget before (re)opening, making this effectively a singleton.
        if (this.menu_widget) {
            this.menu_widget.close();
        }

        // Create menu widget.
        var opener_widget = event.view.$el;
        this.menu_widget = new StackMenuWidget({
            collection: this.store,
            container: opener_widget.parent(),
        });

        // Wire menu events.
        this.listenTo(this.menu_widget, 'action:edit', _.bind(navigatorApp.ui.work_in_progress, navigatorApp.ui));
        this.listenTo(this.menu_widget, 'action:share', _.bind(navigatorApp.ui.work_in_progress, navigatorApp.ui));
        this.listenTo(this.menu_widget, 'action:xpexport', _.bind(navigatorApp.ui.work_in_progress, navigatorApp.ui));
        this.listenTo(this.menu_widget, 'action:reset', this.reset);

        // Open/show/display widget.
        this.menu_widget.open();
    },

});


// Setup plugin
navigatorApp.addInitializer(function(options) {

    var stack_enabled = navigatorApp.theme.get('feature.stack.enabled');

    // Skip starting the stack subsystem.
    if (!stack_enabled) { return; }

    this.listenToOnce(this, "application:init", function() {
        this.stack = new StackPlugin({application: this, view: this.collectionView});
    });

});
