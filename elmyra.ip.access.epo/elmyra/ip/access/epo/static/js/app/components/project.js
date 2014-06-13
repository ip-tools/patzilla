// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG

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
        // backbone-relational backward-compat
        if (!this.fetchRelated) this.fetchRelated = this.getAsync;
    },

    record_query: function(query_data) {

        var query = query_data.query + ' (' + query_data.datasource + ')';

        console.log('ProjectModel.record_query:', query);

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
    },

    destroy: function(options) {
        var basket = this.get('basket');
        if (basket) {

            // remove basket entries
            basket.get('entries').each(function(entry) {
                if (entry) {
                    entry.destroy();
                }
            });

            // remove basket
            basket.destroy();
        }
        return Backbone.Model.prototype.destroy.call(this, options);
    },

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
    get_or_create: function(name, options) {

        var _this = this;

        var records = this.where({name: name});

        // FIXME: should raise an exception in this case, right?
        if (!records) return;

        var project = records[0];


        // deferred which will get signalled when we're done with everything object storage
        var deferred = $.Deferred();
        var succeed = function() {
            if (options && options.success) {
                options.success(project);
            }
            deferred.resolve(project);
        };

        // load existing project
        if (project) {
            console.log('ProjectModel.load');

            // refetch project to work around localforage.backbone vs. backbone-relational woes
            // otherwise, data storage mayhem may happen, because of model.id vs. model.sync.localforageKey mismatch
            project.fetch({success: function() {
                $.when(project.fetchRelated('basket')).then(succeed);
            }})

        // create new project
        } else {
            console.log('ProjectModel.create');

            // create basket for new project
            var basket = new BasketModel();

            // save basket
            basket.save(null, {success: function() {

                // create new project instance
                project = new ProjectModel({ name: name, created: now_iso(), basket: basket });

                // create project in collection
                _this.create(project, {success: function() {

                    // workaround: this makes deleting a freshly created project work
                    _this.add(project);

                    // fetch associated basket objects
                    $.when(project.fetchRelated('basket')).then(function() {

                        // update backreference to project object on basket object
                        var basket = project.get('basket');
                        basket.save({'project': project}, {success: function() {

                            // refetch project again and finally end this damn chain
                            project.fetch({success: function() {
                                $.when(project.fetchRelated('basket')).then(succeed);
                            }});

                        }});
                    });

                }});

            }});

        }

        return deferred;

    },

});


ProjectChooserView = Backbone.Marionette.ItemView.extend({

    template: "#project-chooser-template",

    initialize: function() {
        console.log('ProjectChooserView.initialize');

        this.data_list_selector = '#project-chooser-list ul';

        this.listenTo(this.model, "change", this.render);
        this.listenTo(this, "item:rendered", this.setup_ui);
    },

    onDomRefresh: function() {
        console.log('ProjectChooserView.onDomRefresh');
    },

    projectname_validate: function(projectname) {

        // reject empty project names
        if (!projectname) {
            return 'Project name must not be empty';
        }

        // reject renaming if project name already exists
        var results = this.collection.where({name: projectname});
        if (!_.isEmpty(results)) {
            return 'Project name already exists';
        }

    },

    setup_ui: function() {
        console.log('ProjectChooserView.setup_ui');

        var _this = this;

        // 1. rename a project by making the project name inline-editable
        $('#project-chooser-name').editable({
            mode: 'inline',
            placeholder: 'Enter project name',
            success: function(response, projectname) {
                // rename project
                _this.model.set('name', projectname);
                _this.model.save();
            },
            validate: function(value) {
                return _this.projectname_validate(value);
            },
        });

        // 2. set project name
        this.set_name(this.model.get('name'));


        // 3. populate dropdown-menu for switching the current project

        // where to append the project entries
        var container = $(this.data_list_selector);
        var collection = this.collection;

        // sort collection by modification date, descending
        // TODO: refactor to ProjectChooserItemView, introduce ProjectChooserModel
        container.empty();
        collection.sortByField('modified', 'desc').each(function(project) {
            var name = project.get('name');
            var modified = project.get('modified');
            // TODO: refactor to project.html
            var entry = _.template(
                '<li>' +
                    '<a class="incognito" href="javascript: void(0);" data-value="<%= name %>">' +
                        '<%= name %> ' +
                        '<span class="pull-right"><%= modified %></span>' +
                    '</a>' +
                '</li>')({name: name, modified: moment(modified).fromNow()});
            container.append(entry);
        });

        // make project entry links switch the current project
        container.find('a').click(function() {
            var projectname = $(this).data('value');
            opsChooserApp.trigger('project:load', projectname);
        });


        // 4. activate project action buttons
        $(this.el).find('#project-delete-button').click(function(e) {

            _this.model.destroy({success: function() {

                // select the next available project
                var selected = _this.collection.sortByField('modified', 'desc').first();
                if (selected) {
                    var projectname = selected.get('name');
                    opsChooserApp.trigger('project:load', projectname);

                // if no project is left, autocreate the canonical one (named by current date) again
                } else {

                    // HACK: aid in destroying a freshly created BasketModel
                    opsChooserApp.basketModel.destroy();
                    delete opsChooserApp.basketModel;

                    opsChooserApp.trigger('projects:initialize');

                    var notification_container = $('#project-chooser-name').parent().parent();
                    $(notification_container).notify('recreated default project', {className: 'info', position: 'top'});

                }
            }});
        });

        $(this.el).find('#project-create-button').unbind();
        $(this.el).find('#project-create-button').click(function(e) {

            e.stopPropagation();
            e.preventDefault();
            $(this).popover('hide');

            // swap projectname chooser from renaming to creation functionality
            var chooser = $('#project-chooser-name');
            chooser.unbind();

            var value_old = chooser.editable('getValue', true);
            chooser.editable('destroy');
            chooser.editable({
                mode: 'inline',
                toggle: 'manual',
                placeholder: 'Enter project name',
                success: function(response, projectname) {
                    opsChooserApp.trigger('project:load', projectname);
                },
                validate: function(value) {
                    return _this.projectname_validate(value);
                },
            });

            chooser.editable('show');
            chooser.editable('setValue', '');

            chooser.on('hidden', function(event, reason) {
                if (reason != 'save') {
                    chooser.editable('destroy');
                    _this.setup_ui();
                }
            });

        });

    },

    set_name: function(name) {
        // set project name
        if (name) {
            $('#project-chooser-name').editable('setValue', name);
        } else {
            $('#project-chooser-name').hide();
        }
    },

});


opsChooserApp.addInitializer(function(options) {

    var _this = this;

    // data storage / project bootstrapper
    // 1. load data from ProjectCollection
    // 2. compute project name to be initialized, from "project=" url query parameter; otherwise use <today>, e.g. "2014-05-22"
    // 3. get project object; otherwise create a new one
    // 4. emit "project:ready" event

    // load project when receiving "project:load" event
    this.listenTo(this, 'project:load', function(projectname) {

        // remember current project name to detect project-switch later
        var projectname_before;
        if (this.project) {
            projectname_before = this.project.get('name');
        }

        var _this = this;
        $.when(this.projects.get_or_create(projectname)).done(function(project) {
            _this.trigger('project:ready', project);

            // if project names differ, emit changed event
            if (projectname != projectname_before) {
                _this.trigger('project:changed', project);
            }
        });

    });

    // fetch all projects and activate designated one
    this.listenTo(this, 'projects:initialize', function(projectname) {
        console.log('projects:initialize');

        // use project name from config (propagated from current url)
        if (!projectname) {
            projectname = this.config.get('projectname');
        }
        // use default project name
        /*
        if (!projectname) {
            projectname = 'ad-hoc;
        }
        */

        this.projects = new ProjectCollection();

        var _this = this;
        this.projects.fetch({success: function(response) {
            // load designated project
            _this.trigger('project:load', projectname);
        }});
    });

    // Fetch all projects on application start and initialize designated or default project.
    // HACK: Skip initialization if another load operation (e.g. by database-transfer) is already
    //       in progress. database-transfer will trigger projects:initialize after import happened.
    // TODO: project and comment loading vs. application bootstrapping are not synchronized yet
    if (!this.LOAD_IN_PROGRESS) {
        this.trigger('projects:initialize');
    }

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
