// -*- coding: utf-8 -*-
// (c) 2018 Andreas Motl <andreas.motl@ip-tools.org>
require('patzilla.navigator.components.storage');
require('backbone-dom-to-view');


StackModel = Backbone.RelationalModel.extend({

    sync: Backbone.localforage.sync('Stack'),

    relations: [
    ],

    defaults: {
        items: [],
    },

    initialize: function() {
        console.log('StackModel.initialize');
    },

});


StackCollection = Backbone.Collection.extend({
    sync: Backbone.localforage.sync('Stack'),
    find: Backbone.localforage.find,
    model: StackModel,

    // initialize model
    initialize: function() {
        console.log('StackCollection.initialize');
    },

    // TODO: refactor to common base class or mixin
    get_or_create: function(attributes) {
        var model = _(this.where(attributes)).first();
        if (!model) {
            model = this.model.build(attributes, { collection: this, parsed: false });
            this.create(model, {success: function() {
                log('StackCollection::get_or_create: SUCCESS');
            }});

        }
        return model;
    },

    by_name: function(name) {
        return this.get_or_create({name: name});
    },

});


StackManager = Marionette.Controller.extend({

    initialize: function(options) {

        log('StackManager.initialize');

        this.collection = options.collection;
        this.itemview = options.itemview;

        // Find DOM elements
        var rating_stack_container = this.itemview.$el.find('.document-rating-stack');
        this.rating_element = rating_stack_container.find('.document-rating-widget');
        this.stack_element = rating_stack_container.find('.document-stack-widget');

        // Setup data model
        this.model = this.get_model();

        // Debugging: Activate immediately
        //this.toggle_checkbox();

    },

    get_model: function() {
        var model = this.collection.by_name('default');
        return model;
    },

    show_toggle: function() {
        this.rating_element.toggle('fast');
        this.stack_element.toggle('fast');
    },

    show_stack: function() {
        this.rating_element.hide('fast');
        this.stack_element.show('fast');
    },

    show_rating: function() {
        this.stack_element.hide('fast');
        this.rating_element.show('fast');
    },

    select: function() {
        log('StackManager::select');

        // Visual representation
        this.stack_element.find('input').prop('checked', true);
        this.itemview.$el.addClass('document-stack-decorated');

        // Data model manipulation
        var docnumber = this.stack_element.data('document-number');
        this.add(docnumber);
    },

    unselect: function() {
        log('StackManager::unselect');

        // Visual representation
        this.stack_element.find('input').prop('checked', false);
        this.itemview.$el.removeClass('document-stack-decorated');

        // Data model manipulation
        var docnumber = this.stack_element.data('document-number');
        this.remove(docnumber);
    },

    add: function(item) {
        var items = this.model.get('items');
        //log('items:', items);
        if (!_.contains(items, item)) {
            items.push(item);
            this.model.set('items', items);
            this.model.save();
        }
    },
    remove: function(item) {
        var items = this.model.get('items');
        //log('items:', items);
        if (_.contains(items, item)) {
            items = _.without(items, item);
            this.model.set('items', items);
            this.model.save();
        }
    },

});


StackPlugin = Marionette.Controller.extend({

    initialize: function(options) {
        var _this = this;

        console.log('StackPlugin::initialize');

        this.view = options.view;

        // Setup the data store
        this.listenTo(navigatorApp, 'localforage:ready', function() {
            log('localforage:ready-stack');
            _this.setup_component(options);
        });

    },

    setup_component: function(options) {

        log('StackPlugin::setup_component');
        this.store = new StackCollection();

        // Setup the data store
        this.store.fetch({success: function(response) {
            log('StackPlugin: fetch ready');
            // FIXME: nobody currently waits for this to happen
        }});

        // Forward control to a new item-specific StackManager after itemview got rendered
        this.listenTo(this.view, 'itemview:item:rendered', function(itemview) {

            // place StackManager inside itemview for external access (e.g. viewport)
            itemview.stack_manager = this.stack_factory(itemview);

        });


        // register global hotkeys
        this.bind_hotkeys();
    },

    stack_factory: function(itemview) {
        return new StackManager({
            collection: this.store,
            itemview: itemview,
        });
    },

    stack_by_element: function(element) {
        var backbone_view = element.backboneView();
        if (backbone_view.stack_manager) {
            return backbone_view.stack_manager;
        }
    },

    // register global hotkeys
    bind_hotkeys: function() {
        var _this = this;
        $(document).on('keydown', null, 'S', function() {

            // Display checkbox and obtain StackManager object
            var stack = _this.activate_stack_by_viewport();

            // Select checkbox
            stack.select();
        });

        $(document).on('keydown', null, 'X', function() {
            // Display checkbox and obtain StackManager object
            var stack = _this.activate_stack_by_viewport();

            // Unselect checkbox
            stack.unselect();
        });

    },

    // Toggle comment currently in viewport

    activate_stack_by_viewport: function() {
        var stack = this.stack_by_viewport();
        stack.show_stack();
        return stack;
    },

    activate_rating_by_viewport: function() {
        var stack = this.stack_by_viewport();
        stack.show_rating();
        return stack;
    },

    stack_by_viewport: function() {
        // Display checkbox
        var element = this.content_element_by_viewport();

        // Resolve StackManager object
        var stack = this.stack_by_element(element);

        return stack;
    },

    content_element_by_viewport: function() {
        // Resolve the closest Backbone view
        var element = $('.document-anchor:in-viewport').closest('.ops-collection-entry');
        return element;
    },

    toggle_by_element: function(element, show_stack) {

        var stack = this.stack_by_element(element);

        if (!stack) return;

        if (show_stack) {
            stack.show_stack();
        } else {
            stack.show_toggle();
        }
    },

    toggle_all: function(show_stack) {
        var _this = this;
        $('.ops-collection-entry').each(function(index, element) {
            _this.toggle_by_element($(element), show_stack);
        });
    },

    enable_stack_mode: function() {
        this.toggle_all(true);
    },

});


// Setup plugin
navigatorApp.addInitializer(function(options) {

    this.listenToOnce(this, "application:init", function() {
        this.stack = new StackPlugin({view: this.collectionView});
    });

    this.register_component('stack');

});
