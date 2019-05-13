// -*- coding: utf-8 -*-
// (c) 2014-2018 Andreas Motl <andreas.motl@ip-tools.org>
require('patzilla.navigator.components.storage');
require('backbone-dom-to-view');
const DirectRenderMixin = require('patzilla.lib.marionette').DirectRenderMixin;
const SmartCollectionMixin = require('patzilla.lib.backbone').SmartCollectionMixin;


CommentModel = Backbone.RelationalModel.extend({

    sync: Backbone.localforage.sync('Comment'),

    // Automatically maintain "created" and "modified" model attributes
    timestamped: true,

    relations: [
        {
            type: Backbone.HasOne,
            key: 'project',
            relatedModel: 'ProjectModel',
            includeInJSON: Backbone.Model.prototype.idAttribute,
        },
    ],

    defaults: {
        author: undefined,
        text: undefined,
    },

    initialize: function() {
        //log('CommentModel::initialize');
    },

});


CommentCollection = Backbone.Collection.extendEach(SmartCollectionMixin, {
    sync: Backbone.localforage.sync('Comment'),
    find: Backbone.localforage.find,
    model: CommentModel,

    // initialize model
    initialize: function() {
        //log('CommentCollection::initialize');
    },

    by_project_and_document_number: function(project, document_number) {
        return this.get_or_create({project: project, parent: document_number});
    },

    get_by_project: function(project) {
        return this.search({project: project}, CommentCollection);
    },

});


CommentButtonView = Backbone.Marionette.ItemView.extend({
    template: require('./comment-button.html'),
    //tagName: null,

    // forward the "click" dom event to a "toggle" application event
    triggers: {
        'click': 'toggle',
    },

});
_.extend(CommentButtonView.prototype, DirectRenderMixin);


CommentTextView = Backbone.Marionette.ItemView.extend({
    template: require('./comment-widget.html'),
    tagName: 'span',

    initialize: function() {
        //log('CommentTextView::initialize');
        this.listenTo(this.model, 'remove', this.clear);
    },

    // propagate the stored comment text into the widget
    onRender: function() {
        var textarea = this.get_textarea();
        textarea.val(this.model.get('text'));
    },

    // clear widget value
    clear: function() {
        this.get_textarea().val(undefined);
    },

    // TODO: refactor this to a common base class or ItemView mixin
    get_widget: function() {
        return $(this.el).find(':first-child').first();
    },

    get_textarea: function() {
        return $(this.el).find('textarea');
    },

    toggle: function() {

        var _this = this;

        // Show the widget with animation.
        this.get_widget().slideToggle(function() {
            var element = _this.get_textarea();
            var is_visible = element.is(":visible");
            if (is_visible) {
                element.trigger('focus');

                element.off('keydown');
                element.on('keydown', null, 'meta+return', function() {
                    element.trigger('blur');
                });
                element.on('keydown', null, 'ctrl+return', function(event) {
                    element.trigger('blur');
                });

            }
        });

        // Save the comment when loosing focus by connecting
        // the textarea element's blur event to the item save action.
        var textarea = this.get_textarea();
        textarea.off('blur');
        textarea.on('blur', function() {
            var text = textarea.val();
            _this.save(text);
        });

    },

    save: function(text) {

        var _this = this;

        var oldtext = this.model.get('text');
        if (text == oldtext) {
            return;
        }

        this.model.set({'text': text});
        return this.model.save();
    },

});


CommentManager = Marionette.Controller.extend({

    initialize: function(options) {

        //log('CommentManager::initialize');

        this.collection = options.collection;
        this.project = options.project;
        this.view = options.view;

        // query store
        this.model = this.get_or_create();

        // setup descendant views
        this.comment_button = new CommentButtonView();
        this.comment_text = new CommentTextView({
            model: this.model,
            collection: this.collection,
        });

        // show views in regions
        this.view.region_comment_button.show(this.comment_button);
        this.view.region_comment_text.show(this.comment_text);

        // wire events

        // show text on button press
        this.listenTo(this.comment_button, 'toggle', this.toggle_edit);

    },

    toggle_edit: function() {
        this.comment_text.toggle();
    },

    get_or_create: function() {
        var document_number = this.view.model.get_document_number();
        var model = this.collection.by_project_and_document_number(this.project, document_number);
        return model;
    },

});


CommentsPlugin = Marionette.Controller.extend({

    initialize: function(options) {

        log('CommentsPlugin::initialize');
        var _this = this;

        this.view = options.view;

        // remember the itemviews used for this collection
        // this will get used later for renewing the comment managers when a project switch occurs
        this.itemviews = [];

        // Setup the data store
        this.listenTo(navigatorApp, 'localforage:ready', function() {
            log('localforage:ready-comment');
            _this.setup_component(options);
        });

    },

    setup_component: function(options) {

        this.store = new CommentCollection();

        // Setup the data store
        this.store.fetch({success: function(response) {
            log('CommentsPlugin: fetch ready');
            // FIXME: nobody currently waits for this to happen
        }});

        // Forward control to a new item-specific CommentManager after itemview got rendered
        this.listenTo(this.view, 'itemview:item:rendered', function(itemview) {

            // place CommentManager inside itemview for external access (e.g. viewport)
            itemview.comment_manager = this.comment_factory(itemview);

            // record itemviews for later renewal on project change
            this.itemviews.push(itemview);
        });

        // clear remembered itemviews
        this.listenTo(this.view, 'collection:before:render', function() {
            _.clear(this.itemviews);
        });
        this.listenTo(this.view, 'collection:before:close', function() {
            _.clear(this.itemviews);
        });

        // handle switching projects
        // renew all CommentManagers in remembered itemviews when new project gets ready
        this.listenTo(navigatorApp, 'project:changed', function(project) {
            var _this = this;
            _(this.itemviews).each(function(itemview) {
                itemview.comment_manager = _this.comment_factory(itemview);
            });
        });


        // register global hotkeys
        this.bind_hotkeys();
    },

    comment_factory: function(itemview) {
        var project = navigatorApp.project;
        //log('comment_factory using project:', project);
        return new CommentManager({
            collection: this.store,
            project: project,
            view: itemview,
        });
    },

    // register global hotkeys
    bind_hotkeys: function() {
        var _this = this;
        $(document).on('keydown', null, 'C', function() {
            _this.toggle_by_viewport();
        });
    },

    // toggle comment currently in viewport
    toggle_by_viewport: function() {

        // resolve the closest backbone view
        var element = $('.document-anchor:in-viewport').closest('.ops-collection-entry');

        // edit-toggle the comment manager
        this.toggle_by_element(element);
    },

    toggle_by_element: function(element) {

        var backbone_view = element.backboneView();

        // Edit-toggle the comment manager
        if (backbone_view && backbone_view.comment_manager) {
            backbone_view.comment_manager.toggle_edit();
        }
    },

    toggle_all: function() {
        var _this = this;
        $('.ops-collection-entry').each(function(index, element) {
            _this.toggle_by_element($(element));
        });
    },

});


// Setup plugin
navigatorApp.addInitializer(function(options) {

    this.listenToOnce(this, "application:init", function() {

        // Initialize comments plugin
        // HACK: Postpone initialization until projects:initialize happens, if another
        //       load operation (e.g. by database-transfer) is already in progress.
        // TODO: project and comment loading vs. application bootstrapping are not synchronized yet
        if (!this.LOAD_IN_PROGRESS) {
            this.comments = new CommentsPlugin({view: this.collectionView});

        } else {
            this.listenTo(this, 'projects:initialize', function() {
                this.comments = new CommentsPlugin({view: this.collectionView});
            });

        }


    });

    this.register_component('comments');

});
