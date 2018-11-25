// -*- coding: utf-8 -*-
// (c) 2018 Andreas Motl <andreas.motl@ip-tools.org>
require('backbone-dom-to-view');
require('patzilla.lib.hero-checkbox');
require('patzilla.lib.marionette');
require('patzilla.navigator.components.storage');


StackModel = Backbone.RelationalModel.extend({

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


StackCollection = Backbone.Collection.extendEach(SmartCollectionMixin, {
    sync: Backbone.localforage.sync('StackEntry'),
    find: Backbone.localforage.find,
    model: StackModel,

    // initialize model
    initialize: function() {
        //log('StackCollection::initialize');
    },

});





// TODO: Use https://github.com/rafeememon/marionette-checkbox-behavior
StackCheckboxWidget = CheckboxWidget.extend({
    /*
    Contemporary <input type="checkbox"> elements with bidirectional data binding.
    Derived from https://github.com/rafeememon/marionette-checkbox-behavior
    */

    inputSelector: '> input',
    labelSelector: '> .text_label',

    // Forward the "click" dom event to a "toggle" application event
    triggers: {
        //'click': 'toggle',
    },

    initialize: function() {
        //log('StackCheckboxWidget::initialize');
        // https://makandracards.com/makandra/22121-how-to-call-overwritten-methods-of-parent-classes-in-backbone-js
        // https://stackoverflow.com/questions/15987490/backbone-view-inheritance-call-parent-leads-to-recursion/15988038#15988038
        StackCheckboxWidget.__super__.initialize.apply(this, arguments);
    },

});


StackDisplayMode = {
    RATING: 'mode-rating',
    STACK:  'mode-stack',
};

StackManager = NamedViewController.extend({

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

        // Wire events
        this.listenTo(this.model, 'change:selected', this.save_model);
        this.listenTo(this.model, 'change:selected', this.update_sidecar_indicator);

        this.update_sidecar_indicator();
        //this.listenTo(this.checkbox_widget, 'render', this.update_sidecar_indicator);

        // Debug events
        /*
        this.listenTo(this, 'all', this.on_manager_event);
        this.listenTo(this.model, 'all', this.on_model_event);
        this.listenTo(this.checkbox_widget, 'all', this.on_widget_event);
        */

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
        this.hide_checkbox();
        this.rating_element.show('fast');
    },

    show_checkbox: function() {
        this.view.region_stack_checkbox.show(this.checkbox_widget);
    },
    hide_checkbox: function() {
        this.view.region_stack_checkbox.reset();
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


StackPlugin = Backbone.Marionette.Controller.extendEach(MarionetteFuture, {

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
        if (this.application.component_enabled('profile')) {
            var mode = this.application.profile.get_intent('work.mode');
            log('StackPlugin::intent_hook mode:', mode);
            if (mode) {
                this.activate_all_real(mode);
            }
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
        if (this.application.component_enabled('profile')) {
            this.application.profile.set_intent('work.mode', mode);
        }

        return this.activate_all_real(mode);
    },

    activate_all_real: function(mode) {
        // Iterate list of visible result elements and activate
        // the designated mode on each of them.
        var _this = this;
        $('.ops-collection-entry').each(function(index, element) {
            _this.activate_by_element($(element), mode);
        });
    },

    activate_all_stack: function() {
        this.activate_all_mode(StackDisplayMode.STACK);
    },
    activate_all_rating: function() {
        this.activate_all_mode(StackDisplayMode.RATING);
    },

});


// Setup plugin
navigatorApp.addInitializer(function(options) {

    this.listenToOnce(this, "application:init", function() {
        this.stack = new StackPlugin({application: this, view: this.collectionView});
    });

    this.register_component('stack');

});
