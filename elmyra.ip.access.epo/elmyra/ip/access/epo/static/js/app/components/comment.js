// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG

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

        /*
         var success = options.success;
         options.success = function(model, resp, options) {
         if (isNew) {
         _this.collection.create(model, {success: function() {
         _this.collection.add(model);
         options.isnew = isNew;
         _this.trigger('saved', model, resp, options);
         if (success) success(model, resp, options);
         }});
         } else {
         _this.trigger('saved', model, resp, options);
         if (success) success(model, resp, options);
         }
         };

         return Backbone.Model.prototype.save.call(this, attrs, options);
         */

        var project = this.get('project');
        log('MODEL BEFORE SAVE:', this, this.get('project'));

        var success = options.success;
        options.success = function(model, resp, options) {
            log('MODEL AFTER SAVE:', model, model.get('project'));

            /*
            model.fetch({success: function(m) {
                log('=========== MODEL REFETCH SUCCESS');
                log(m);
                log(model);
                $.when(model.fetchRelated('project')).then(function() {
                    log('=========== MODEL RELATED REFETCH SUCCESS');
                    log(model);
                });
            }});

            if (success) success(model, resp, options);
            return;
             */

            if (isNew) {
                //model.set('project', project);
                log('before create:', model.get('project'));
                _this.collection.create(model, {success: function() {
                    _this.collection.add(model);
                    options.isnew = isNew;

                    // FIXME: IMPORTANT HACK to reset project reference after it has vanished through collection.create
                    model.set('project', project);

                    //Backbone.Relational.store.reset();
                    //_this.collection.fetch({reset: true, success: function(res) {
                        log('=========== MODEL COLLECTION REFETCH SUCCESS');
                        //log(res);
                        log(_this.collection);
                        //model.fetch({success: function(m) {
                            log('=========== MODEL REFETCH SUCCESS');
                            //log(m);
                            log(model);
                            if (!model.fetchRelated) model.fetchRelated = model.getAsync;
                            //$.when(model.fetchRelated('project')).then(function() {
                                log('=========== MODEL RELATED REFETCH SUCCESS');
                                log(model);
                                log(model.get('project'));
                                _this.trigger('saved', model, resp, options);
                                if (success) success(model, resp, options);
                            //});
                        //}});
                    //}});
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
        console.log('ModelCollection.initialize');
    },

    by_project_and_document_number: function(project, document_number) {
        var model = _(this.where({project: project, parent: document_number})).first();
        log('CommentCollection.by_project_and_document_number:', project.get('name'), document_number, model);
        if (!model) {
            var now = timestamp();
            model = new CommentModel({
                project: project,
                parent: document_number,
            }, { collection: this });
        }
        return model;
    },

});

CommentButtonView = Backbone.Marionette.ItemView.extend({
    template: "#template-comment-button",
    tagName: 'span',

    // forward the "click" dom event to a "toggle" application event
    triggers: {
        'click': 'toggle',
    },

    onClose: function() {
        log('====================== CommentButtonView.onClose');
    },

});

CommentTextView = Backbone.Marionette.ItemView.extend({
    template: "#template-comment-text",
    tagName: 'span',

    initialize: function() {
        console.log('CommentTextView.initialize');
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

        // propagate the stored comment text into the widget
        var textarea = this.get_textarea();
        textarea.val(this.model.get('text'));

        // save the comment when loosing focus by connecting
        // the textarea element's blur event to the item save action
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

        // save comment
        this.listenTo(this.comment_text, 'model:saved', this.save);

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

        // setup the data store
        this.store = new CommentCollection();
        this.store.fetch({success: function(response) {
            log('CommentsPlugin: fetch ready');
            // FIXME: nobody currently waits for this to happen
        }});

        // forward control to a new item-specific CommentManager after itemview got rendered
        this.listenTo(this.view, 'itemview:item:rendered', function(itemview) {

            log('itemview:item:rendered');

            // place CommentManager inside itemview for external access (e.g. viewport)
            itemview.comment_manager = this.comment_factory(itemview);

            // record itemviews for later renewal on project change
            this.itemviews.push(itemview);
        });

        // clear remembered itemviews
        this.listenTo(this.view, 'collection:before:render', function() {
            log('before:render');
            log('1');
            _.clear(this.itemviews);
            log('2');
        });
        this.listenTo(this.view, 'collection:before:close', function() {
            log('before:close');
            _.clear(this.itemviews);
        });

        // renew all CommentManagers when project gets ready
        this.listenTo(opsChooserApp, 'project:ready', function(project) {
            var _this = this;
            log('project:ready - itemviews:', this.itemviews);
            log('project:ready - collection:', this.store);
            _(this.itemviews).each(function(itemview) {
                itemview.comment_manager = _this.comment_factory(itemview);
            });
        });


        // register global hotkeys
        this.bind_hotkeys();
    },

    comment_factory: function(itemview) {
        var project = opsChooserApp.project;
        log('comment_factory using project:', project);
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

    // handles the mechanics for all comment widgets on a whole result list
    this.comments = new CommentsPlugin({view: this.collectionView});

});
