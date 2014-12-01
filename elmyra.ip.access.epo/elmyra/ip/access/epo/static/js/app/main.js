// -*- coding: utf-8 -*-
// (c) 2013,2014 Andreas Motl, Elmyra UG

/**
 * ------------------------------------------
 *          main application object
 * ------------------------------------------
 */
OpsChooserApp = Backbone.Marionette.Application.extend({

    get_datasource: function() {
        var datasource = $('#datasource > .btn.active').data('value');
        return datasource;
    },

    set_datasource: function(datasource) {
        $("#datasource .btn[data-value='" + datasource + "']").button('toggle');
        this.queryBuilderView.cql_field_chooser_setup();
        this.queryBuilderView.setup_comfort_form();
    },

    get_query: function() {
        return $('#query').val();
    },

    disable_reviewmode: function() {
        this.metadata.set('reviewmode', false);
    },

    // perform ops search and process response
    perform_search: function(options) {

        options = options || {};
        // propagate datasource
        options.datasource = datasource;


        // 1. initialize search
        var query = this.get_query();
        var datasource = this.get_datasource();
        this.metadata.set('datasource', datasource);
        this.metadata.resetSomeDefaults(options);


        // 2. handle review mode
        if (options && options.reviewmode != null) {
            this.metadata.set('reviewmode', options.reviewmode);
        }
        // TODO: maybe move to pagination.js
        var reviewmode = this.metadata.get('reviewmode');
        if (reviewmode == true) {
            this.basketModel.review(options);
            return;
        }


        // 3. perform search

        if (_.isEmpty(query)) {
            return;
        }

        console.log('App.perform_search: datasource=' + datasource, 'query=' + query, 'options=', options);

        // propagate keywords from comfort form for fallback mechanism
        options.keywords = $('#keywords').val();


        var self = this;

        if (datasource == 'ops') {
            var range = this.compute_range(options);
            this.trigger('search:before', {datasource: datasource, query: query, range: range});
            opsChooserApp.search.perform(this.documents, this.metadata, query, range).done(function() {

                var hits = self.metadata.get('result_count');
                if (hits > self.metadata.get('maximum_results')['ops']) {
                    self.user_alert('Total hits: ' + hits + '.    ' +
                        'The first 2000 hits are accessible from OPS.  ' +
                        'You can narrow your search by adding more search criteria.', 'warning');
                }
                self.metadata.set('keywords', opsChooserApp.search.keywords);

                // signal the results are ready
                self.trigger('results:ready');

            });

        } else if (datasource == 'depatisnet') {

            this.trigger('search:before', {datasource: datasource, query: query});

            // make the pager display the original query
            this.metadata.set('query_origin', query);

            var depatisnet = new DepatisnetSearch();
            depatisnet.perform(query, options).done(function(response) {

                self.propagate_datasource_message(response);
                self.metadata.set('keywords', depatisnet.keywords);
                console.log('depatisnet response:', response);

                var publication_numbers = response['numbers'];
                var hits = response['hits'];

                self.perform_listsearch(options, query, publication_numbers, hits, 'pn', 'OR').done(function() {
                    // need to propagate again, because "perform_listsearch" clears it; TODO: enhance mechanics!
                    self.propagate_datasource_message(response);
                });

            });

        } else if (datasource == 'google') {

            this.trigger('search:before', {datasource: datasource, query: query});

            // make the pager display the original query
            this.metadata.set('query_origin', query);

            var google = new GooglePatentSearch();
            google.perform(query, options).done(function(response) {
                options = options || {};

                self.propagate_datasource_message(response);

                // propagate keywords
                self.metadata.set('keywords', google.keywords);

                console.log('google response:', response);
                console.log('google keywords:', google.keywords);

                var publication_numbers = response['numbers'];
                var hits = response['hits'];

                if (publication_numbers) {

                    // TODO: return pagesize from backend
                    options.remote_limit = 100;

                    self.perform_listsearch(options, query, publication_numbers, hits, 'pn', 'OR').done(function() {

                        // propagate upstream message again, because "perform_listsearch" clears it; TODO: enhance mechanics!
                        self.propagate_datasource_message(response);

                        if (hits == null) {
                            self.user_alert(
                                'Result count unknown. At Google Patents, sometimes result counts are not displayed. ' +
                                "Let's assume 1000 to make the paging work.", 'warning');
                        }

                        if (hits > self.metadata.get('maximum_results')['google']) {
                            self.user_alert(
                                'Total results ' + hits + '. From Google Patents, the first 1000 results are accessible. ' +
                                'You might want to narrow your search by adding more search criteria.', 'warning');
                        }
                    });
                }

            });

        } else if (datasource == 'ftpro') {

            this.trigger('search:before', {datasource: datasource, query: query});

            // make the pager display the original query
            this.metadata.set('query_origin', query);

            var ftprosearch = new FulltextProSearch();
            ftprosearch.perform(query, options).done(function(response) {
                options = options || {};

                console.log('ftpro response:', response);

                self.propagate_datasource_message(response);

                // propagate keywords
                self.metadata.set('keywords', ftprosearch.keywords);

                var publication_numbers = response['details'];
                var hits = response['meta']['MemCount']; // + '<br/>(' + response['meta']['DocCount'] + ')';
                options['remote_limit'] = response['meta']['Limit'];

                self.perform_listsearch(options, query, publication_numbers, hits, 'pn', 'OR').done(function() {
                    // propagate upstream message again, because "perform_listsearch" clears it; TODO: enhance mechanics!
                    self.propagate_datasource_message(response);
                });

            });

        } else {
            this.ui.notify('Search provider "' + datasource + '" not implemented.', {type: 'error', icon2: 'icon-copy'});
        }

    },

    send_query: function(query, options) {
        if (query) {
            $('#query').val(query);
            opsChooserApp.perform_search(options);
            $(window).scrollTop(0);
        }
    },

    // perform ops search and process response
    perform_listsearch: function(options, query_origin, entries, hits, field, operator) {

        //log('perform_listsearch.options:', options);

        //this.set_datasource('ops');

        this.ui.indicate_activity(false);
        //this.ui.reset_content();
        this.ui.reset_content({keep_pager: true, documents: true});


        // compute slice values
        var range = options && options.range ? options.range : '1-10';
        //console.log('range:', range);
        var range_parts = range.split('-');
        var sstart = parseInt(range_parts[0]) - 1;
        var ssend = parseInt(range_parts[1]);

        if (options && options.remote_limit) {
            log('slice options.remote_limit:', options.remote_limit);
            sstart = sstart % options.remote_limit;
            ssend = ssend % options.remote_limit;
            if (ssend == 0) {
                ssend = options.remote_limit - 1;
            }
        }
        console.log('local slices:', sstart, ssend);

        if (entries && (entries.length == 0 || sstart > entries.length)) {

            var deferred = $.Deferred();
            deferred.resolve();

            //self.metadata.set('result_count', 0);

            if (_.isEmpty(query_origin) && _.isEmpty(entries)) {
                this.ui.reset_content({keep_pager: false, documents: true});
                this.user_alert('No results.', 'info');
                return deferred.promise();
            }

        }

        // result entries to display
        var entries_sliced = entries.slice(sstart, ssend);

        // propagate to generic result collection view
        //log('entries_sliced:', entries_sliced);
        if (!_.isEmpty(entries_sliced) && _.isObject(entries_sliced[0])) {
            try {
                this.results.reset(entries_sliced);
            } catch (ex) {
                console.error('Problem propagating data to results collection', ex);
                //throw(ex);
            }
        } else {
            this.results.reset();
        }

        // compute query expression to display documents from OPS
        var query_ops_constraints = _(_.map(entries_sliced, function(entry) {
            var number;
            if (_.isObject(entry)) {
                number = entry['publication_number'];
            } else {
                number = entry;
            }
            return field + '=' + number;
        }));
        var query_ops_cql = query_ops_constraints.join(' ' + operator + ' ');
        console.log('OPS CQL query:', query_ops_cql);

        if (!query_origin) {
            query_origin = query_ops_cql;
        }

        //$('#query').val(query_origin);

        // querying by single document numbers has a limit of 10 at OPS
        this.metadata.set('page_size', 10);

        // set parameter to control subsearch
        this.metadata.set('searchmode', 'subsearch');

        var self = this;
        //var range = this.compute_range(options);
        return this.search.perform(this.documents, this.metadata, query_ops_cql, '1-10').done(function() {

            // show the original query
            self.metadata.set('query_origin', query_origin);

            // show the original result size
            self.metadata.set('result_count', hits);

            // amend the current result range and paging parameter
            self.metadata.set('result_range', range);
            self.metadata.set('pagination_entry_count', 17);
            $('.pagination').removeClass('span10');
            $('.pagination').addClass('span12');

            // TODO: selecting page size with DEPATISnet is currently not possible
            //$('.page-size-chooser').parent().remove();

            // propagate list of found document numbers to results collection
            // in order to make it possible to indicate which documents are missing
            self.results.set_reference_document_numbers(self.documents.get_document_numbers());

            // signal the results are ready
            self.trigger('results:ready');

        });

    },

    // initialize model from url query parameters ("numberlist")
    parse_numberlist: function(payload) {
        if (!_.isEmpty(payload)) {
            var numberlist = _(payload.split(/[,\n]/)).map(function(entry) {
                return entry.trim();
            }).filter(function(entry) {
                return !(_.isEmpty(entry) || _.string.startsWith(entry, '//') || _.string.startsWith(entry, '#'));
            });
            return numberlist;
        }
    },

    perform_numberlistsearch: function(options) {
        var publication_numbers = this.parse_numberlist($('#numberlist').val());
        var hits = publication_numbers.length;
        //opsChooserApp.perform_listsearch(options, query, publication_numbers, hits, 'pn', 'OR')
        this.perform_listsearch(options, undefined, publication_numbers, hits, 'pn', 'OR');
    },

    compute_range: function(options) {
        var page_size = this.metadata.get('page_size');
        var default_range = '1-' + page_size;
        var range = options && options.range ? options.range : default_range;
        return range;
    },

    propagate_datasource_message: function(response) {
        log('propagate_datasource_message');
        this.user_alert(response['message'], 'warning');
    },

    user_alert: function(message, kind) {

        if (!message) {
            return;
        }

        var label = 'INFO';
        var clazz = 'alert-info';
        if (kind == 'warning') {
            label = 'WARNING';
            clazz = 'alert-warning';
        }
        var tpl = _.template($('#alert-template').html());
        var error = {
            'title': label,
            'description': message,
            'clazz': clazz,
        };
        var alert_html = tpl(error);
        $('#info-area').append(alert_html);
    },


    // TODO: move to project.js
    project_activate: function(project) {

        var _this = this;

        if (!project) {
            console.error('project is null, will not activate');
            return;
        }

        var projectname = project.get('name');
        console.log('App.project_activate:', projectname);

        // set project active in application scope
        // TODO: can this be further decoupled?
        if (this.project) {
            this.stopListening(this.project);
            delete this.project;
        }
        this.project = project;

        // set hook to record all queries
        this.stopListening(this, 'search:before');
        this.listenTo(this, 'search:before', function(arguments) {
            project.record_query(arguments);
        });

        // trigger project reload when window gets focus
        // FIXME: this interferes with rating actions into unfocused windows
        $(window).off('focus', this.project_reload);
        $(window).on('focus', this.project_reload);

        // setup views
        this.projectChooserView = new ProjectChooserView({
            el: $('#project-chooser-area'),
            model: project,
            collection: project.collection,
        });
        this.projectChooserView.render();

        // activate storage actions
        this.storage.setup_ui();

        // activate permalink actions
        this.permalink.setup_ui();

        // update project information metadata display
        $('#ui-project-name').html(
            'Review for project "' + project.get('name') + '".'
        );
        $('#ui-project-dates').html(
            'Created ' + moment(project.get('created')).fromNow() + ', ' +
            'modified ' + moment(project.get('modified')).fromNow() + '.'
        );
        $('#ui-opaquelink-expiry').html(
            'Link expires ' + moment(this.config.get('link_expires')).fromNow() + '.'
        );


        // Also update current application configuration model.
        // Be aware that the basket is not properly initialized yet at this point.
        // So potential listeners to configuration model change events currently
        // must not expect a *fully* initialized project/basket structure.
        this.config.set('project', project.get('name'));


        // activate basket
        var basket = project.get('basket');

        // refetch basket to work around localforage.backbone vs. backbone-relational woes
        // otherwise, data storage mayhem may happen, because of model.id vs. model.sync.localforageKey mismatch
        // FIXME: it's ridiculous that we don't receive stacktraces from within "then()"
        basket.fetch({
            success: function() {
                $.when(basket.fetch_entries()).then(function() {
                    _this.basket_activate(basket);
                });
            },
            error: function(e) {
                _this.basket_deactivate();
            },
        });

    },

    project_deactivate: function() {
        $(window).off('focus', this.project_reload);
    },

    project_reload: function() {
        // reload project
        var projectname = opsChooserApp.project.get('name');
        opsChooserApp.trigger('project:load', projectname);
    },

    // TODO: move to basket.js
    basket_deactivate: function() {

        // TODO: how to decouple this? is there something like a global utility registry?
        // TODO: is old model killed properly?
        if (this.basketModel) {
            this.stopListening(this.basketModel);
            delete this.basketModel;
        }

        // TODO: is old view killed properly?
        // https://stackoverflow.com/questions/14460855/backbone-js-listento-window-resize-throwing-object-object-has-no-method-apply/17472399#17472399
        if (this.basketView) {
            this.basketView.close();
            this.stopListening(this.basketView);
            //this.basketView.destroy();
            //this.basketView.remove();
            delete this.basketView;
        }
    },

    basket_activate: function(basket) {

        console.log('App.basket_activate');

        if (!basket) {
            console.error('basket is null, will not activate');
            return;
        }

        this.basket_deactivate();

        // A. model and view
        this.basketModel = basket;
        this.basketView = new BasketView({
            //el: $('#basket-area'),
            model: basket,
        });
        this.basketRegion.show(this.basketView);


        // B. event listeners

        // toggle appropriate Add/Remove button when entries get added or removed from basket
        // TODO: are old bindings killed properly?
        // FIXME: this stopListening is brutal!
        this.stopListening(null, "change:add");
        this.stopListening(null, "change:remove");
        this.listenTo(basket, "change:add", this.basketController.link_document);
        this.listenTo(basket, "change:remove", this.basketController.link_document);
        this.listenTo(basket, "change:rate", this.basketController.link_document);

        // save project when basket changed to update the "modified" attribute
        this.stopListening(null, "change");
        this.listenTo(basket, "change", function() {
            this.project.save();
        });

        // focus added number in basket
        this.listenTo(basket, "change:add", function(entry, number) {
            this.basketView.textarea_scroll_text(number);
        });



        // C. user interface
        this.basketView.render();

        // update some other gui components after basket view is ready
        this.basket_bind_actions();

        this.trigger('basket:activated', basket);

    },

    basket_bind_actions: function() {

        // TODO: maybe use an event handler for this, instead of a direct method call (e.g. "item:rendered")

        var _this = this;

        // handle checkbox clicks by add-/remove-operations on basket
        /*
        $(".chk-patent-number").click(function() {
            var patent_number = this.value;
            if (this.checked)
                _this.basketModel.add(patent_number);
            if (!this.checked)
                _this.basketModel.remove(patent_number);
        });
        */

        // handle button clicks by add-/remove-operations on basket
        $(".add-patent-number").unbind('click');
        $(".add-patent-number").click(function() {
            var patent_number = $(this).data('patent-number');
            _this.basketModel.add(patent_number);
        });
        $(".remove-patent-number").unbind('click');
        $(".remove-patent-number").click(function() {
            var patent_number = $(this).data('patent-number');
            _this.basketModel.remove(patent_number);
        });

        // handle "add all documents"
        $("#basket-add-all-documents").unbind('click');
        $("#basket-add-all-documents").click(function() {
            // collect all document numbers
            _this.documents.each(function(document) {
                var number = document.attributes.get_patent_number();
                _this.basketModel.add(number);
            });

        });

        // setup rating widget
        console.log('setup rating widget');
        //$('.rating-widget').raty('destroy');
        $('.rating-widget').raty({
            number: 3,
            hints: ['slightly relevant', 'relevant', 'important'],
            cancel: true,
            cancelHint: 'not relevant',
            dismissible: true,
            path: '/static/widget/raty/img',
            action: function(data, evt) {
                var score = data.score;
                var dismiss = data.dismiss;
                var document_number = $(this).data('document-number');
                _this.document_rate(document_number, score, dismiss);
            },
        });

        // propagate basket contents to Add/Remove button states once when activating the basket
        // TODO: do this conditionally - only if Basket is enabled
        this.documents.each(function(document) {
            var number = document.attributes.get_patent_number();
            if (_this.basketModel) {
                var entry = _this.basketModel.get_entry_by_number(number);
                _this.basketController.link_document(entry, number);
            } else {
                _this.basketController.link_document(undefined, number);
            }
        });

    },


    document_rate: function(document_number, score, dismiss) {
        var _this = this;
        if (document_number) {
            this.basketModel.add(document_number).then(function(item) {
                item.save({score: score, dismiss: dismiss}, {
                    success: function() {
                        _this.basketModel.trigger('change:rate', item, document_number);
                        _this.basketView.textarea_scroll_text(document_number);

                    }, error: function() {
                        console.error('rating save error', document_number, item);
                    }
                });

            });
        }
    },


    // tear down user interface, clear all widgets
    shutdown_gui: function() {

        // basket and associated document indicators
        this.basketModel.destroy();
        this.basket_bind_actions();
        this.basketView.render();

        // comments
        this.comments.store.set();

        // projects
        this.projects.reset();
        this.projectChooserView.clear();

    },

});


/**
 * ------------------------------------------
 *           bootstrap application
 * ------------------------------------------
 */

opsChooserApp = new OpsChooserApp({config: ipsuiteNavigatorConfig});

opsChooserApp.addRegions({
    queryBuilderRegion: "#querybuilder-region",
    basketRegion: "#basket-region",
    metadataRegion: "#ops-metadata-region",
    listRegion: "#ops-collection-region",
    paginationRegionTop: "#ops-pagination-region-top",
    paginationRegionBottom: "#ops-pagination-region-bottom",
});


// global universal helpers, able to boot early
opsChooserApp.addInitializer(function(options) {
    this.storage = new StoragePlugin();

    this.listenTo(this, 'application:ready', function() {
        this.storage.setup_ui();
    });

    this.listenTo(this, 'results:ready', function() {
        this.storage.setup_ui();
    });
});

// data storage
opsChooserApp.addInitializer(function(options) {

    // Set driver (optional)
    // We use Local Storage here to make introspection easier.
    // TODO: disable on production
    localforage.setDriver('localStorageWrapper');

    // set database name from "context" query parameter
    localforage.config({name: this.config.get('context')});

    // import database from url :-)
    // TODO: i'd like this to have storage.js make it on its own, but that'd be too late :-(
    //       check again what we could achieve...
    var database_dump = this.config.get('database');
    if (database_dump) {

        // When importing a database dump, we assign "context=viewer" a special meaning here:
        // the database scope will always be cleared beforehand to avoid project name collisions.
        // Ergo the "viewer" context is considered a *very transient* datastore.
        if (this.config.get('context') == 'viewer') {
            this.storage.dbreset();
        }

        // TODO: project and comment loading vs. application bootstrapping are not synchronized yet
        this.LOAD_IN_PROGRESS = true;

        // TODO: resolve project name collisions!
        this.storage.dbimport(database_dump);
    }

});

// initialize models
opsChooserApp.addInitializer(function(options) {

    // application domain model objects
    this.search = new OpsPublishedDataSearch();
    this.metadata = new OpsExchangeMetadata();
    this.documents = new OpsExchangeDocumentCollection();
    this.results = new ResultCollection();

});

// initialize views
opsChooserApp.addInitializer(function(options) {

    // bind model objects to view objects
    this.metadataView = new MetadataView({
        model: this.metadata
    });
    this.collectionView = new OpsExchangeDocumentCollectionView({
        collection: this.documents
    });
    this.resultView = new ResultCollectionView({
        collection: this.results
    });

    this.paginationViewTop = new PaginationView({
        model: this.metadata
    });
    this.paginationViewBottom = new PaginationView({
        model: this.metadata
    });

    // bind view objects to region objects
    this.metadataRegion.show(this.metadataView);
    this.paginationRegionTop.show(this.paginationViewTop);
    this.paginationRegionBottom.show(this.paginationViewBottom);
});

// activate anonymous basket (non-persistent/project-associated)
opsChooserApp.addInitializer(function(options) {
    // remark: the model instance created here will get overwritten later
    //         by a project-specific basket when activating a project
    // reason: we still do it here for the case we decide to deactivate the project
    //         subsystem in certain modes (dunno whether this will work out)
    // update [2014-06-08]: deactivated anonymous basket until further
    //this.basket_activate(new BasketModel());
});

// main component event wiring
opsChooserApp.addInitializer(function(options) {

    this.listenTo(this, 'results:ready', function() {

        // commit metadata, this will trigger e.g. PaginationView rendering
        this.metadata.trigger('commit');

        // show documents (ops results) in collection view
        // explicitly switch list region to OPS collection view
        if (this.listRegion.currentView !== this.collectionView) {
            this.listRegion.show(this.collectionView);
        }

    });

    // activate project as soon it's loaded from the datastore
    this.listenTo(this, "project:ready", this.project_activate);

    // kick off the search process immediately after initial project was created
    this.listenToOnce(this, "project:ready", function() { this.perform_search(); });

});


$(document).ready(function() {

    console.log("document.ready");

    // process and propagate application ingress parameters
    //var url = $.url(window.location.href);
    //var query = url.param('query');
    //query = 'applicant=IBM';
    //query = 'publicationnumber=US2013255753A1';

    opsChooserApp.start();

    boot_application();

    // Automatically run search after bootstrapping application.
    // However, from now on [2014-05-21] this gets triggered by "project:ready" events.
    // We keep this here in case we want to switch gears / provide a non-persistency
    // version of the tool for which the chance is likely, i.e. for a website embedding
    // component.
    //opsChooserApp.perform_search();

});
