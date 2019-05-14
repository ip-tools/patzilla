// -*- coding: utf-8 -*-
// (c) 2014-2018 Andreas Motl <andreas.motl@ip-tools.org>
require('patzilla.navigator.components.storage');
require('x-editable/dist/bootstrap-editable/js/bootstrap-editable');
require('x-editable/dist/bootstrap-editable/css/bootstrap-editable');
var slugify = require('slugify');


QueryModel = Backbone.RelationalModel.extend({

    sync: Backbone.localforage.sync('Query'),

    defaults: {
        flavor: undefined,              // comfort, expert
        datasource: undefined,          // data source name
        query_data: undefined,          // comfort mode form dictionary
        query_expert: undefined,        // expert mode query expression and filter
        query_expression: undefined,    // expert mode query expression, deprecated
        created: undefined,
        result_count: undefined,
    },

    initialize: function() {
        console.log('QueryModel.initialize');
        // backbone-relational backward-compat
        if (!this.fetchRelated) this.fetchRelated = this.getAsync;
    },

    equals: function(obj) {
        var proplist = ['flavor', 'datasource', 'query_data', 'query_expert', 'query_expression'];
        var picked_this = _.pick(this.attributes, proplist);
        var picked_obj = _.pick(obj.attributes, proplist);
        var result = _.isEqual(picked_this, picked_obj);
        return result;
    },

});


ProjectModel = Backbone.RelationalModel.extend({

    sync: Backbone.localforage.sync('Project'),
    //collection: ProjectCollection,

    relations: [
        {
            type: Backbone.HasOne,
            key: 'basket',
            relatedModel: 'BasketModel',
            //autoFetch: true,

            includeInJSON: Backbone.Model.prototype.idAttribute,

            reverseRelation: {
                type: Backbone.HasOne,
                key: 'project',
                // 'relatedModel' is automatically set to 'ProjectModel'
                includeInJSON: Backbone.Model.prototype.idAttribute,
            },

        },

        {
            type: Backbone.HasMany,
            key: 'queries',
            relatedModel: 'QueryModel',
            includeInJSON: Backbone.Model.prototype.idAttribute,

            // reverseRelation *must not* be defined for HasMany relationships, otherwise this will yield
            // empty collections unconditionally, especially after creating new parent objects
            /*
            reverseRelation: {
                type: Backbone.HasOne,
                key: 'project',
                // 'relatedModel' is automatically set to 'ProjectModel'
                includeInJSON: Backbone.Model.prototype.idAttribute,
            },
            */

        },

    ],

    defaults: {
        name: null,
        created: null,
        modified: null,
        mode_fade_seen: undefined,
    },

    // initialize model
    initialize: function() {
        console.log('ProjectModel.initialize', this);
        // backbone-relational backward-compat
        if (!this.fetchRelated) this.fetchRelated = this.getAsync;
    },

    record_query: function(search_info) {

        log('ProjectModel.record_query search_info:', search_info);

        var flavor = search_info.flavor;
        var datasource = search_info.datasource;

        if (!flavor || !datasource) {
            return;
        }

        var dirty = false;
        var _this = this;
        $.when(this.fetch_queries()).then(function() {
            var query_collection = _this.get('queries');
            query_collection = sortCollectionByField(query_collection, 'created', 'desc');
            var recent = query_collection.first();

            var query = new QueryModel({
                flavor: flavor,
                datasource: datasource,
                query_data: search_info.query_data,
                query_expert: search_info.query,
                query_expression: search_info.query.expression,
                created: now_iso(),
                result_count: search_info.result_count,
                //project: _this,
            });

            // don't record the same queries multiple times
            var equals = recent && query.equals(recent);
            if (!equals) {
                _this.history_add_query(query);
            } else {
                query.destroy();
            }

        });

    },

    history_add_query: function(query) {

        log('ProjectModel.record_query model:', query);

        var _this = this;
        query.save(null, {success: function() {
            var queries = _this.get('queries');
            queries.add(query);
            _this.save({'queries': queries}, {
                success: function() {
                    log('ProjectModel.record_query SUCCESS!');
                },
                error: function(error) {
                    log('ProjectModel.record_query ERROR!', error);
                },
            });
        }});

    },

    // automatically update "modified" field on save
    save: function(key, val, options) {
        // http://jstarrdewar.com/blog/2012/07/20/the-correct-way-to-override-concrete-backbone-methods/
        this.set('modified', now_iso());
        //this.set('modified', now_iso(), {silent: true});
        return Backbone.Model.prototype.save.call(this, key, val, options);
    },

    destroy: function(options) {
        var basket = this.get('basket');
        if (basket) {

            // Remove all basket entries
            var entries = [];
            basket.get('entries').each(function(entry) {
                entries.push(entry);
            });
            _.each(entries, function(entry) {
                entry.destroy();
            });

            // Remove basket
            basket.destroy();
        }

        // Remove project
        return Backbone.Model.prototype.destroy.call(this, options);
    },

    fetch_queries: function() {
        var main_deferred = $.Deferred();

        // Fetch associated QueryModel objects
        var _this = this;
        $.when(this.fetchRelated('queries')).then(function() {
            var query_collection = _this.get('queries');
            var deferreds = [];
            query_collection.each(function(query) {

                // prepare a deferred which will get resolved after successfully fetching an item from datastore
                var deferred = $.Deferred();
                deferreds.push(deferred.promise());

                query.fetch({
                    success: function() {
                        deferred.resolve(query);
                    },
                    error: function(error) {
                        deferred.resolve(query);
                    },
                });

            });

            $.when.apply($, deferreds).then(function() {
                main_deferred.resolve();
            });


        }).fail(function() {
            main_deferred.reject();
        });

        return main_deferred.promise();
    },

    get_queries: function() {

        var deferred = $.Deferred();

        // fetch query objects and sort descending by creation date
        var _this = this;
        $.when(_this.fetch_queries()).then(function() {
            var query_collection = _this.get('queries');
            query_collection = sortCollectionByField(query_collection, 'created', 'asc');
            var chooser_data = query_collection.map(function(query) {
                return query.toJSON();
            });
            deferred.resolve(chooser_data);

        }).fail(function() {
            deferred.reject();
        });

        return deferred.promise();
    },

    get_comments: function() {
        return navigatorApp.comments.store.get_by_project(this);
    },

});

Backbone.Relational.store.addModelScope({QueryModel: QueryModel, ProjectModel: ProjectModel});


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
        log('ProjectCollection.get_or_create records:', records);

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
            }});

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

                            }, error: function(project) {
                                console.error('Could not fetch project: ' + JSON.stringify(project));
                                deferred.reject(project);
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

    template: require('./project.html'),

    initialize: function() {
        console.log('ProjectChooserView.initialize');

        this.data_list_selector = '#project-chooser-list ul';

        // TODO: Optimize this!
        this.listenTo(this.model, "change", this.render);
        this.listenTo(this, "item:rendered", this.setup_ui);
    },

    render_attempt: function(item) {
        // Suppress rendering if model is present but nothing actually changed
        if (item && item.changed && _.isEmpty(item.changed)) {
            log('ProjectChooserView: Skip rendering');
            return;
        }
        return Backbone.Marionette.ItemView.prototype.render.call(this);
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

        // make project entry links switch to the selected project
        var project_links = container.find('a');
        project_links.off('click');
        project_links.on('click', function() {
            var projectname = $(this).data('value').toString();
            console.info('Switching to project:', projectname);
            navigatorApp.trigger('project:load', projectname);
        });


        // 4. setup mode buttons
        var mode_seen_button = $(this.el).find('#mode-seen-fade-button');
        var mode_seen_checkbox = mode_seen_button.find('#mode-seen-fade');

        // propagate checkbox state from data model to user interface
        var mode_seen_user = _this.model.get('mode_fade_seen');
        if (mode_seen_user) {
            mode_seen_checkbox.prop('checked', true);
        }

        // bind click event
        mode_seen_button.off('click');
        mode_seen_button.on('click', function(e) {

            //log('CLICK SEEN');

            // boilerplate
            e.stopPropagation();
            e.preventDefault();
            //$(this).popover('hide');

            // manually toggle ui state, was suppressed by e.stopPropagation() and e.preventDefault()
            mode_seen_checkbox.toggleCheck();

            // propagate checkbox state from user interface to data model
            var mode_seen_ui = mode_seen_checkbox.prop('checked');
            //log('mode_seen_ui:', mode_seen_ui);
            _this.model.set('mode_fade_seen', mode_seen_ui);
            _this.model.save();

            if (!mode_seen_ui) {
                navigatorApp.document_base.bright('.ops-collection-entry');
            }

        });


        // 5. bind project action buttons
        var delete_button = $(this.el).find('#project-delete-button');
        delete_button.off('click');
        delete_button.on('click', function(e) {

            var projectname = navigatorApp.config.get('project');
            navigatorApp.ui.confirm('This will delete the current project "' + projectname + '". Are you sure?').then(function() {

                _this.model.destroy({success: function() {

                    navigatorApp.ui.notify(
                        'Project "' + _this.model.get('name') + '" deleted.',
                        {type: 'success', icon: 'icon-trash'});

                    // select the next available project
                    var selected = _this.collection.sortByField('modified', 'desc').first();
                    if (selected) {
                        var projectname = selected.get('name');
                        navigatorApp.trigger('project:load', projectname);

                    // if no project is left, autocreate the canonical one (named by current date) again
                    } else {

                        // HACK: aid in destroying a freshly created BasketModel
                        navigatorApp.basketModel.destroy();
                        delete navigatorApp.basketModel;

                        var projectname = navigatorApp.config._originalAttributes.project;
                        navigatorApp.config.set('project', projectname);

                        navigatorApp.trigger('projects:initialize');

                        // notify user about the completed action
                        navigatorApp.ui.notify(
                            'Project "' + _this.model.get('name') + '" deleted.<br/>Recreated default project.',
                            {type: 'success', icon: 'icon-trash'});

                    }
                }});

            });
        });

        $(this.el).find('#project-create-button').off();
        $(this.el).find('#project-create-button').on('click', function(e) {

            e.stopPropagation();
            e.preventDefault();
            $(this).popover('hide');

            // swap projectname chooser from renaming to creation functionality
            var chooser = $('#project-chooser-name');
            chooser.off();

            var value_old = chooser.editable('getValue', true);
            chooser.editable('destroy');
            chooser.editable({
                mode: 'inline',
                toggle: 'manual',
                placeholder: 'Enter project name',
                success: function(response, projectname) {
                    navigatorApp.trigger('project:load', projectname);
                    navigatorApp.ui.notify(
                        'Project "' + projectname + '" created.',
                        {type: 'success', icon: 'icon-plus'});
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

        // Import database from file.
        // https://developer.mozilla.org/en-US/docs/Using_files_from_web_applications
        $('#project-import-file').off('change');
        $('#project-import-file').on('change', function(e) {
            e.stopPropagation();
            e.preventDefault();

            var element = this;

            // Deactivate project / windows.onfocus.
            // Otherwise, the default project (e.g. "ad-hoc") would be recreated almost instantly.
            navigatorApp.project_deactivate();

            // Open file dialog.
            $.when(navigatorApp.storage.open_json_file(element)).then(function(payload) {

                // Import database payload.
                $.when(navigatorApp.storage.dbimport('project', payload)).then(function() {

                    // Reload environment.
                    $(element).trigger('import:ready');
                });
            });

        });


        $(this.el).find('#project-import-button').off();
        $(this.el).find('#project-import-button').on('click', function(e) {

            navigatorApp.storage.confirm_load_data().then(function() {

                // Event handler for "import ready"
                $('#project-import-file').off('import:ready');
                $('#project-import-file').on('import:ready', function(e) {
                    setTimeout(function() {
                        window.location.reload();
                    }, 750);
                });

                // Start import by displaying file dialog.
                navigatorApp.project_deactivate();
                $('#project-import-file').trigger('click');

            });

        });

        $(this.el).find('#project-export-button').off();
        $(this.el).find('#project-export-button').on('click', function(e) {

            e.stopPropagation();
            e.preventDefault();
            $(this).popover('hide');

            _this.export_file(_this.model.get('id'));

        });

    },

    export_file: function(project_id) {
        var _this = this;
        navigatorApp.storage.dump().then(function(backup) {
            var project_data = _this.export_get_project(backup, project_id);
            backup.database = project_data.database;
            backup.metadata.description = 'IP Navigator Project';
            backup.metadata.type = 'patzilla.navigator.project';
            var project_slug = slugify(project_data.name);
            navigatorApp.storage.export_json_file('ip-navigator-project_' + project_slug, backup);
        });
    },

    export_get_project: function(backup, project_id) {

        var mkitem = function(key, value) {
            var item = {};
            item[key] = value;
            return item;
        };

        var items = [];

        // Project index.
        var project_key = 'Project/' + project_id;
        items.push(mkitem("Project", [project_key]));

        // Project.
        var database = backup.database;
        var project = database[project_key];
        items.push(mkitem(project_key, project));

        // Query.
        _.each(project.queries, function(entry) {
            var query_key = 'Query/' + entry;
            var query = database[query_key];
            items.push(mkitem(query_key, query));
        });

        // Basket.
        var basket_key = 'Basket/' + project.basket;
        var basket = database[basket_key];
        items.push(mkitem(basket_key, basket));

        // BasketEntry
        _.each(basket.entries, function(entry) {
            var basket_entry_key = 'BasketEntry/' + entry;
            var basket_entry = database[basket_entry_key];
            items.push(mkitem(basket_entry_key, basket_entry));
        });

        // Scan for comments.
        var comment_index = [];
        _.each(database, function(comment, key) {
            if (_.string.startsWith(key, 'Comment/')) {
                if (comment.project == project_id) {
                    items.push(mkitem(key, comment));
                    comment_index.push(key);
                }
            }
        });
        items.push(mkitem("Comment", comment_index));

        var result = {
            database: items,
            project: project,
            name: project.name,
        };

        return result;

    },

    set_name: function(name) {
        // set project name
        if (name) {
            $('#project-chooser-name').editable('setValue', name);
        } else {
            $('#project-chooser-name').hide();
        }
    },

    clear: function() {
        this.set_name();
        $(this.data_list_selector).empty();
    },

});


navigatorApp.addInitializer(function(options) {

    var _this = this;

    // data storage / project bootstrapper
    // 1. load data from ProjectCollection
    // 2. compute project name to be initialized, from "project=" url query parameter; otherwise use <today>, e.g. "2014-05-22"
    // 3. get project object; otherwise create a new one
    // 4. emit "project:ready" event

    // load project when receiving "project:load" event
    this.listenTo(this, 'project:load', function(projectname) {

        log('project:load happened for:', projectname);

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

        }).fail(function(project) {
            _this.trigger('project:ready');

        });

    });

    // fetch all projects and activate designated one
    this.listenTo(this, 'projects:initialize', function(projectname) {

        log('projects:initialize received');

        var _this = this;

        // use project name from config (propagated from current url)
        if (!projectname) {
            projectname = this.config.get('project');
        }
        // use default project name
        /*
        if (!projectname) {
            projectname = 'ad-hoc;
        }
        */

        this.listenTo(navigatorApp, 'localforage:ready', function() {
            log('localforage:ready-project');
            _this.projects = new ProjectCollection();
            _this.projects.fetch({
                success: function(response) {
                    // load designated project
                    _this.trigger('project:load', projectname);
                },
                error: function(response) {
                    console.log('fetch-error');
                    // load designated project
                    //_this.trigger('project:load', projectname);
                },
            });
        });

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
