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

            reverseRelation: {
                type: Backbone.HasOne,
                key: 'project',
                // 'relatedModel' is automatically set to 'ProjectModel'
                includeInJSON: Backbone.Model.prototype.idAttribute,
            },

        }
    ],

    defaults: {
        name: null,
        created: null,
        modified: null,
        queries: [],
    },

    // initialize model
    initialize: function() {
        console.log('ProjectModel.initialize');
    },

    record_query: function(query, range) {
        console.log('ProjectModel.record_query: ' + query);

        var dirty = false;

        var queries = this.get('queries');

        // don't record the same queries multiple times
        if (_(queries).last() != query) {
            queries.push(query);
            dirty = true;
        }

        if (dirty) {
            this.set('queries', queries);
            this.save();
        }

    },

    // automatically update "modified" field on save
    save: function(key, val, options) {
        // http://jstarrdewar.com/blog/2012/07/20/the-correct-way-to-override-concrete-backbone-methods/
        this.set('modified', now_iso());
        return Backbone.Model.prototype.save.call(this, key, val, options);
    }

});

ProjectCollection = Backbone.Collection.extend({
    sync: Backbone.localforage.sync('Project'),
    find: Backbone.localforage.find,
    model: ProjectModel,

    // initialize model
    initialize: function() {
        console.log('ProjectCollection.initialize');
    },

    // TODO: refactor this to a generic base class
    sortByField: function(fieldName, direction) {
        var _this = this;
        var _comparator_ascending = function(a, b) {
            a = a.get(_this.sort_key);
            b = b.get(_this.sort_key);
            return a > b ?  1
                 : a < b ? -1
                 :          0;
        };
        var _comparator_descending = function(a, b) { return _comparator_ascending(b, a); }
        this.comparator = _comparator_ascending;
        if (_.str.startsWith(direction, 'd')) {
            this.comparator = _comparator_descending;
        }
        this.sort_key = fieldName;
        this.sort();
        return this;
    },

    // get project object from storage or create new one
    // TODO: maybe make it more generic, esp. the uniqueness checking
    get_or_create: function(name) {

        var records = this.where({name: name});

        // FIXME: should raise an exception in this case, right?
        if (!records) return;

        var project = records[0];

        // create new project
        if (project) {

            // refetch project to work around localforage.backbone vs. backbone-relational woes
            // otherwise, data storage mayhem may happen, because of model.id vs. model.sync.localforageKey mismatch
            project.fetch();

        } else {
            console.log('ProjectModel.create');

            // create basket for new project
            var basket = new BasketModel();

            // create new project
            project = new ProjectModel({ name: name, created: now_iso(), basket: basket });
            this.create(project);

            // update backreference to project object on basket object
            basket.set('project', project);
            basket.save();
        }

        project.fetchRelated('basket');
        var basket = project.get('basket');

        return project;

    },

});


ProjectChooserView = Backbone.Marionette.ItemView.extend({

    template: "#project-chooser-template",

    initialize: function() {
        console.log('ProjectChooserView.initialize');
        this.listenTo(this.model, "change", this.render);
        this.listenTo(this, "item:rendered", this.setup_ui);
    },

    onDomRefresh: function() {
        console.log('ProjectChooserView.onDomRefresh');
    },

    setup_ui: function() {
        console.log('ProjectChooserView.setup_ui');

        var _this = this;

        // 1. rename a project by making the project name inline-editable
        $('#project-chooser-name').editable({
            mode: 'inline',
            success: function(response, projectname_new) {

                // reject renaming if project name already exists
                var results = _this.collection.where({name: projectname_new});
                if (!_.isEmpty(results)) {
                    $('.editable-container input').tooltip({title: 'Project already exists'}).tooltip('show');
                    changeTooltipColorTo('#DF0101');
                    return false;
                }

                // rename project
                _this.model.set('name', projectname_new);
                _this.model.save();
            },
        });

        // 2. set project name
        $('#project-chooser-name').editable('setValue', this.model.get('name'));


        // 3. populate dropdown-menu

        // where to append the project entries
        var container = $('#project-chooser-list ul');
        var collection = this.collection;

        // sort collection by modification date, descending
        // TODO: refactor to ProjectChooserItemView, introduce ProjectChooserModel
        container.empty();
        collection.sortByField('modified', 'desc').each(function(project) {
            var name = project.get('name');
            var modified = project.get('modified');
            var entry = _.template(
                '<li>' +
                    '<a class="span12" href="javascript: void(0);" data-value="<%= name %>">' +
                    '<%= name %> ' +
                    '<span class="pull-right"><%= modified %></span>' +
                    '</a>' +
                    '</li>')({name: name, modified: moment(modified).fromNow()});
            container.append(entry);
        });

        // make project entry links switch the current project
        container.find('a').click(function() {
            var projectname = $(this).data('value');
            var project = collection.get_or_create(projectname);
            opsChooserApp.trigger('project:ready', project);
        });
    },

});


// TODO: how to make this not reference "opsChooserApp"?
opsChooserApp.addInitializer(function(options) {

    // data storage bootstrapper
    // 1. load data from ProjectCollection
    // 2. get or create current default project (named <today>, e.g. "2014-05-22")
    // 3. emit "project:ready" event

    // TODO: establish settings store (e.g. JQuery-rememberme)
    // TODO: run this logic only if not being able to get "current" project name from settings store

    this.projects = new ProjectCollection();

    var _this = this;
    console.log('App.projects.fetch');
    this.projects.fetch({success: function(response) {
        var today = today_iso();
        var project = _this.projects.get_or_create(today);
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
