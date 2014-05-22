// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG

// Set driver (optional, but we use Local Storage here so developers can more easily inspect it).
// TODO: disable on production
localforage.setDriver('localStorageWrapper');

QueryModel = Backbone.Model.extend({

});

ProjectModel = Backbone.RelationalModel.extend({

    sync: Backbone.localforage.sync('Project'),
    //collection: ProjectCollection,

    relations: [
        {
            type: Backbone.HasOne,
            key: 'basket',
            relatedModel: 'BasketModel',
            includeInJSON: Backbone.Model.prototype.idAttribute,
            collectionType: 'ProjectCollection',

            reverseRelation: {
                key: 'project',
                includeInJSON: Backbone.Model.prototype.idAttribute,
                // 'relatedModel' is automatically set to 'ProjectModel'
                type: Backbone.HasOne,
            }
        }
    ],

    defaults: {
        name: null,
        queries: [],
        created: null,
        modified: null,
    },

    // initialize model
    initialize: function() {
        console.log('ProjectModel::initialize');
        // TODO: how to make this not reference "opsChooserApp"?
        // TODO: should old bindings be killed first?
        //       - all queries will be recorded by all model instances otherwise
        //       - most probably just don't do this here!
        this.listenTo(opsChooserApp, "search:before", this.record_query);
    },

    record_query: function(query, range) {
        console.log('ProjectModel::record_query: ' + query);

        var dirty = false;

        var queries = this.get('queries');

        // don't record the same queries multiple times
        if (_(queries).last() != query) {
            queries.push(query);
            dirty = true;
        }

        if (dirty) {
            this.set('queries', queries);
            this.set('modified', now_iso());
            //this.sync();
            //this.set('basket', 'abc');
            this.save();
        }
    },

});

ProjectCollection = Backbone.Collection.extend({
    sync: Backbone.localforage.sync('Project'),
    find: Backbone.localforage.find,
    model: ProjectModel,

    // initialize model
    initialize: function() {
        console.log('ProjectCollection::initialize');
    },

    // get project object from storage or create new one
    // TODO: maybe make it more generic, esp. the uniqueness checking
    get_or_create: function(name) {
        console.log('ProjectCollection.get_or_create: ' + name);

        var records = this.where({name: name});

        // FIXME: should raise an exception in this case, right?
        if (!records) return;

        var project = records[0];

        // create new project
        if (!project) {
            console.log('ProjectModel.create');

            // fresh basket for new project
            var basket = new BasketModel();
            basket.save();

            // create instance
            project = this.create({ name: name, created: now_iso(), basket: basket });

            // update backreference to project on basket object
            basket.set('project', project);
            basket.save();
        }

        // bind basket change event to its save method when running in project mode
        project.fetchRelated('basket');
        var basket = project.get('basket');
        this.listenTo(basket, "change", function() { basket.save() });

        return project;
    },

});

// TODO: how to make this not reference "opsChooserApp"?
opsChooserApp.addInitializer(function(options) {

    // data storage bootstrapper
    // 1. load data from ProjectCollection
    // 2. get or create current default project (named <today>, e.g. "2014-05-22")
    // 3. emit "project:ready" event

    var collection = new ProjectCollection();

    var _this = this;
    collection.fetch({success: function(response) {
        var today = today_iso();
        var project = collection.get_or_create(today);
        console.log('project:ready');
        _this.trigger('project:ready', project);
    }});


    /*
    TODO

    // Instancing the collection and the view
    var collectionInstance = new MyCollection();
    var myFormView = new MyFormView({
        el: $('<div>', {'class': 'content'}).appendTo(document.body),
        collection: collectionInstance
    });

    myFormView.render();
    collectionInstance.fetch();
    */

});
