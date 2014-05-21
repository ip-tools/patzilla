// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG

// Set driver (optional, but we use Local Storage here so developers can more easily inspect it).
// TODO: disable on production
localforage.setDriver('localStorageWrapper');

QueryModel = Backbone.Model.extend({

});

ProjectModel = Backbone.Model.extend({

    sync: Backbone.localforage.sync('Project'),
    //collection: ProjectCollection,

    defaults: {
        name: null,
        queries: [],
        basket: null,
        created: null,
        modified: null,
    },

    // initialize model
    initialize: function() {
        console.log('ProjectModel::initialize');
        // TODO: how to make this not reference "opsChooserApp"?
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

    get_or_create: function(name) {
        console.log('ProjectCollection::get_or_create: ' + name);
        var records = this.where({name: name});

        // FIXME: raise an exception in this case
        if (!records) return;

        var record = records[0];
        if (!record) {
            console.log('create');
            record = this.create({ name: name, created: now_iso() });
        }
        return record;
    },

});

// TODO: how to make this not reference "opsChooserApp"?
opsChooserApp.addInitializer(function(options) {

    var collection = new ProjectCollection();
    //opsChooserApp.dbprojects = collection;

    var self = this;
    collection.fetch({success: function(abc) {
        var today = today_iso();
        var project = collection.get_or_create(today);
        //opsChooserApp.project = project;
        console.log('project:ready');
        self.trigger('project:ready', project);

        console.log('queries:', project.get('queries'));
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
