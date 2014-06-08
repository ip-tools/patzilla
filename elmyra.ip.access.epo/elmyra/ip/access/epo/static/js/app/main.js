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
        $("#datasource > .btn[data-value='" + datasource + "']").button('toggle');
        cql_field_chooser_setup();
        if (datasource == 'review') {
            $('#query').prop('disabled', true);
        } else {
            $('#query').prop('disabled', false);
        }
    },

    // perform ops search and process response
    perform_search: function(options) {

        this.metadata.resetSomeDefaults();

        var query = $('#query').val();
        var datasource = this.get_datasource();

        console.log('App.perform_search: datasource=' + datasource + ', query=' + query);

        // handle basket review mode specially
        if (options && options.reviewmode != null) {
            this.metadata.set('reviewmode', options.reviewmode);
        }
        var reviewmode = this.metadata.get('reviewmode');
        if (reviewmode == true) {
            this.basketModel.review(options);
            return;
        }

        if (!_.isEmpty(query)) {

            var self = this;
            this.metadata.set('datasource', datasource);

            if (datasource == 'ops') {
                var range = this.compute_range(options);
                console.log('App.perform_search: trigger search:before');
                this.trigger('search:before', query, range);
                opsChooserApp.search.perform(this.documents, this.metadata, query, range).done(function() {

                    self.metadata.set('keywords', opsChooserApp.search.keywords);

                    // run action bindings here after rendering data entries
                    listview_bind_actions();
                });

            } else if (datasource == 'depatisnet') {

                indicate_activity(true);

                // make the pager display the original query
                this.metadata.set('query_origin', query);

                var depatisnet = new DepatisnetSearch();
                depatisnet.perform(query).done(function(response) {

                    self.propagate_depatisnet_message(response);
                    self.metadata.set('keywords', depatisnet.keywords);
                    console.log(response);

                    var publication_numbers = response['data'];
                    var hits = response['hits'];

                    self.perform_listsearch(options, query, publication_numbers, hits, 'pn', 'OR').done(function() {
                        self.propagate_depatisnet_message(response);
                    });

                });
            }

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

        //this.set_datasource('ops');

        indicate_activity(false);
        //reset_content();
        reset_content({keep_pager: true});


        // compute slice values
        var range = options && options.range ? options.range : '1-10';
        //console.log('range:', range);
        var range_parts = range.split('-');
        var sstart = parseInt(range_parts[0]) - 1;
        var ssend = parseInt(range_parts[1]);
        //console.log('range:', sstart, ssend);

        if (entries && (entries.length == 0 || sstart > entries.length)) {

            //self.metadata.set('result_count', 0);

            var msg = _.template(
                'No results with query "<%= query %>", range "<%= range %>".')
                ({query: query, range: range});
            console.warn(msg);

            this.user_alert(msg, 'warning');
            return;
        }

        var query_ops_constraints = _(_.map(entries, function(entry) { return field + '=' + entry}));
        var query_ops_cql_full = query_ops_constraints.join(' ' + operator + ' ');
        var query_ops_cql_sliced = query_ops_constraints.slice(sstart, ssend).join(' ' + operator + ' ');
        console.log('OPS sliced CQL query:', query_ops_cql_sliced);

        if (!query_origin) {
            query_origin = query_ops_cql_full;
        }

        //$('#query').val(query_origin);

        // querying by single document numbers has a limit of 10 at OPS
        this.metadata.set('page_size', 10);

        // set parameter to control subsearch
        this.metadata.set('searchmode', 'subsearch');

        var self = this;
        //var range = this.compute_range(options);
        return opsChooserApp.search.perform(this.documents, this.metadata, query_ops_cql_sliced, '1-10').done(function() {

            // show the original query
            self.metadata.set('query_origin', query_origin);

            // show the original result size
            self.metadata.set('result_count', hits);

            // amend the current result range and paging parameter
            self.metadata.set('result_range', range);
            self.metadata.set('pagination_entry_count', 17);
            $('.pagination').removeClass('span10');
            $('.pagination').addClass('span12');

            // run action bindings here after rendering data entries
            listview_bind_actions();

            // TODO: selecting page size with DEPATISnet is currently not possible
            //$('.page-size-chooser').parent().remove();

        });

    },


    compute_range: function(options) {
        var page_size = this.metadata.get('page_size');
        var default_range = '1-' + page_size;
        var range = options && options.range ? options.range : default_range;
        return range;
    },

    propagate_depatisnet_message: function(response) {
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
        $(window).off('focus', this.project_reload);
        $(window).on('focus', this.project_reload);

        // setup views
        var projectChooserView = new ProjectChooserView({
            el: $('#project-chooser-area'),
            model: project,
            collection: project.collection,
        });
        projectChooserView.render();

        // activate basket
        var basket = project.get('basket');

        // refetch basket to work around localforage.backbone vs. backbone-relational woes
        // otherwise, data storage mayhem may happen, because of model.id vs. model.sync.localforageKey mismatch
        basket.fetch({success: function() {
            $.when(basket.fetch_entries()).then(function() {
                _this.basket_activate(basket);
            });
        }});

    },

    project_reload: function() {
        // reload project
        var projectname = opsChooserApp.project.get('name');
        opsChooserApp.trigger('project:load', projectname);
    },


    // TODO: move to basket.js
    basket_activate: function(basket) {

        console.log('App.basket_activate');

        if (!basket) {
            console.error('basket is null, will not activate');
            return;
        }

        // propagate "numberlist" query parameter to basket content
        basket.init_from_query();


        // A. model and view

        // TODO: how to decouple this? is there something like a global utility registry?
        // TODO: is old model killed properly?
        if (this.basketModel) {
            this.stopListening(this.basketModel);
            delete this.basketModel;
        }
        this.basketModel = basket;

        // TODO: is old view killed properly?
        // https://stackoverflow.com/questions/14460855/backbone-js-listento-window-resize-throwing-object-object-has-no-method-apply/17472399#17472399
        if (this.basketView) {
            this.stopListening(this.basketView);
            //this.basketView.destroy();
            //this.basketView.remove();
            delete this.basketView;
        }
        this.basketView = new BasketView({
            el: $('#basket-area'),
            model: basket,
        });


        // B. event listeners

        // toggle appropriate Add/Remove button when entries get added or removed from basket
        // TODO: are old bindings killed properly?
        this.stopListening(null, "change:add");
        this.stopListening(null, "change:remove");
        this.listenTo(basket, "change:add", this.basketView.link_document);
        this.listenTo(basket, "change:remove", this.basketView.link_document);

        // save project when basket changed to update the "modified" attribute
        this.stopListening(null, "change");
        this.listenTo(basket, "change", function() {
            this.project.save();
        });


        // C. user interface
        this.basketView.render();

        // update some other gui components after basket view is ready
        this.basket_bind_actions();

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

        // propagate basket contents to Add/Remove button states once when activating the basket
        this.documents.each(function(document) {
            var entry = document.attributes.get_patent_number();
            _this.basketView.link_document(entry);
        });

    },

});


/**
 * ------------------------------------------
 *           bootstrap application
 * ------------------------------------------
 */

opsChooserApp = new OpsChooserApp();

opsChooserApp.addRegions({
    metadataRegion: "#ops-metadata-region",
    listRegion: "#ops-collection-region",
    paginationRegionTop: "#ops-pagination-region-top",
    paginationRegionBottom: "#ops-pagination-region-bottom",
});

// initialize models
opsChooserApp.addInitializer(function(options) {

    // application domain model objects
    this.search = new OpsPublishedDataSearch();
    this.metadata = new OpsExchangeMetadata();
    this.documents = new OpsExchangeDocumentCollection();

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
    this.paginationViewTop = new PaginationView({
        model: this.metadata
    });
    this.paginationViewBottom = new PaginationView({
        model: this.metadata
    });

    // bind view objects to region objects
    opsChooserApp.metadataRegion.show(this.metadataView);
    opsChooserApp.listRegion.show(this.collectionView);
    opsChooserApp.paginationRegionTop.show(this.paginationViewTop);
    opsChooserApp.paginationRegionBottom.show(this.paginationViewBottom);
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

    // activate project as soon it's loaded from the datastore
    this.listenTo(this, "project:ready", this.project_activate);

    // kick off the search process immediately after initial project was created
    this.listenToOnce(this, "project:ready", this.perform_search);
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
