// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG
require('patzilla.navigator.components.storage');
require('backbone-dom-to-view');


CommentModel = Backbone.RelationalModel.extend({

    sync: Backbone.localforage.sync('Comment'),

    relations: [
        {
            type: Backbone.HasOne,
            key: 'project',
            relatedModel: 'ProjectModel',
            includeInJSON: Backbone.Model.prototype.idAttribute,
        },
    ],

    defaults: {
        parent: undefined,
        created: undefined,
        modified: undefined,
        author: undefined,
        text: undefined,
    },

    initialize: function() {
        console.log('CommentModel.initialize');
    },

    // TODO: refactor to common base class or mixin
    // automatically set "created" and "modified" fields
    // automatically create model in collection
    // http://jstarrdewar.com/blog/2012/07/20/the-correct-way-to-override-concrete-backbone-methods/
    save: function(key, val, options) {

        // Handle both `"key", value` and `{key: value}` -style arguments.
        if (key == null || typeof key === 'object') {
            attrs = key;
            options = val;
        } else {
            (attrs = {})[key] = val;
        }

        options = _.extend({}, options);

        var _this = this;

        var now = timestamp();
        var isNew = this.isNew();

        var data = {};
        if (isNew) {
            data.created = now;
        }
        data.modified = now;
        this.set(data);


        var project = this.get('project');

        var success = options.success;
        options.success = function(model, resp, options) {

            if (isNew) {

                _this.collection.create(model, {success: function() {

                    // forward "isNew" indicator via options object
                    options.isNew = isNew;

                    // FIXME: HACK ported from project/basket saving; check whether this is really required
                    _this.collection.add(model);

                    // FIXME: IMPORTANT HACK to reset project reference after it has vanished through collection.create
                    model.set('project', project);

                    _this.trigger('saved', model, resp, options);
                    if (success) success(model, resp, options);

                }});

            } else {
                _this.trigger('saved', model, resp, options);
                if (success) success(model, resp, options);
            }
        };

        return Backbone.Model.prototype.save.call(this, attrs, options);

    },

});

CommentCollection = Backbone.Collection.extend({
    sync: Backbone.localforage.sync('Comment'),
    find: Backbone.localforage.find,
    model: CommentModel,

    // initialize model
    initialize: function() {
        console.log('CommentCollection.initialize');
    },

    // TODO: refactor to common base class or mixin
    get_or_create: function(attributes) {
        var model = _(this.where(attributes)).first();
        if (!model) {
            model = this.model.build(attributes, { collection: this, parsed: false });
        }
        return model;
    },

    by_project_and_document_number: function(project, document_number) {
        return this.get_or_create({project: project, parent: document_number});
    },

    get_by_project: function(project) {
        return this.search({project: project});
    },

    search: function(options) {
        // "collection.where" would return an array of models, but we want to continue working with a collection.
        // https://stackoverflow.com/questions/10548685/tojson-on-backbone-collectionwhere/10549086#10549086
        var result = this.where(options);
        var resultCollection = new CommentCollection(result);
        return resultCollection;
    },

});

CommentButtonView = Backbone.Marionette.ItemView.extend({
    template: require('./comment-button.html'),
    tagName: 'span',

    // forward the "click" dom event to a "toggle" application event
    triggers: {
        'click': 'toggle',
    },

});

CommentTextView = Backbone.Marionette.ItemView.extend({
    template: require('./comment-widget.html'),
    tagName: 'span',

    initialize: function() {
        console.log('CommentTextView.initialize');
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

        // show the widget with animation
        this.get_widget().slideToggle();

        // save the comment when loosing focus by connecting
        // the textarea element's blur event to the item save action
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

        log('CommentManager.initialize');

        this.collection = options.collection;
        this.project = options.project;
        this.itemview = options.itemview;

        // query store
        this.model = this.get_or_create();

        // setup descendant views
        this.comment_button = new CommentButtonView();
        this.comment_text = new CommentTextView({
            model: this.model,
            collection: this.collection,
        });

        // show views in regions
        this.itemview.region_comment_button.show(this.comment_button);
        this.itemview.region_comment_text.show(this.comment_text);

        // wire events

        // show text on button press
        this.listenTo(this.comment_button, 'toggle', this.toggle_edit);

    },

    toggle_edit: function() {
        this.comment_text.toggle();
    },

    get_or_create: function() {
        var document_number = this.itemview.model.get_document_number();
        var model = this.collection.by_project_and_document_number(this.project, document_number);
        return model;
    },

});


CommentsPlugin = Marionette.Controller.extend({

    initialize: function(options) {

        console.log('CommentsPlugin.initialize');
        var _this = this;

        this.view = options.view;

        // remember the itemviews used for this collection
        // this will get used later for renewing the comment managers when a project switch occurs
        this.itemviews = [];

        // Setup the data store
        this.listenTo(opsChooserApp, 'localforage:ready', function() {
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
        this.listenTo(opsChooserApp, 'project:changed', function(project) {
            var _this = this;
            _(this.itemviews).each(function(itemview) {
                itemview.comment_manager = _this.comment_factory(itemview);
            });
        });


        // register global hotkeys
        this.bind_hotkeys();
    },

    comment_factory: function(itemview) {
        var project = opsChooserApp.project;
        //log('comment_factory using project:', project);
        return new CommentManager({
            collection: this.store,
            project: project,
            itemview: itemview,
        });
    },

    // register global hotkeys
    bind_hotkeys: function() {
        var _this = this;
        $(document).on('keydown', null, 'C', function() {
            _this.viewport_toggle_comment();
        });
    },

    // toggle comment currently in viewport
    viewport_toggle_comment: function() {

        // resolve the closest backbone view
        var view = $('.document-actions:in-viewport').closest('.ops-collection-entry').backboneView();

        // edit-toggle the comment manager
        if (view.comment_manager) {
            view.comment_manager.toggle_edit();
        }
    },

});


// setup plugin
opsChooserApp.addInitializer(function(options) {

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

});
