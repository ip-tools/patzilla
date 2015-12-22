// -*- coding: utf-8 -*-
// (c) 2013-2015 Andreas Motl, Elmyra UG

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
        this.queryBuilderView.setup_cql_field_chooser();
        this.queryBuilderView.setup_common_form();
        this.queryBuilderView.setup_comfort_form();
    },

    get_query: function() {
        return $('#query').val();
    },

    disable_reviewmode: function() {
        this.metadata.set('reviewmode', false);
    },

    populate_metadata: function() {
        var query_data = this.queryBuilderView.get_common_form_data();
        this.metadata.set('query_data', query_data);
    },


    // TODO: move to search.js

    // perform ops search and process response
    perform_search: function(options) {

        options = options || {};
        // propagate datasource
        options.datasource = datasource;


        // 1. initialize search
        var query = this.get_query();
        var datasource = this.get_datasource();
        this.metadata.set('datasource', datasource);

        // it's probably important to reset e.g. "result_range",
        // because we have to fetch 1-10 for each single result page from OPS
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

        // propagate bunches of options around
        // a) to metadata object
        // b) to search_info summary object
        // TODO: consolidate somehow
        var search_info = {datasource: datasource, query: query};
        if (options.flavor) {
            this.metadata.set('flavor', options.flavor);
            search_info.flavor = options.flavor;
        }
        if (options.query_data) {
            this.metadata.set('query_data', options.query_data);
            search_info.query_data = options.query_data;
        }

        var self = this;

        if (datasource == 'ops') {
            var range = this.compute_range(options);
            this.trigger('search:before', _(search_info).extend({range: range}));

            opsChooserApp.search.perform(this.documents, this.metadata, query, range).done(function() {

                var hits = self.metadata.get('result_count');
                if (hits > self.metadata.get('maximum_results')['ops']) {
                    self.ui.user_alert('Total hits: ' + hits + '.    ' +
                        'The first 2000 hits are accessible from OPS.  ' +
                        'You can narrow your search by adding more search criteria.', 'warning');
                }
                self.metadata.set('keywords', opsChooserApp.search.keywords);

                // signal the results are ready
                self.trigger('results:ready');

            });

        } else if (datasource == 'depatisnet') {

            this.trigger('search:before', search_info);

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

            this.trigger('search:before', search_info);

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
                            self.ui.user_alert(
                                'Result count unknown. At Google Patents, sometimes result counts are not displayed. ' +
                                "Let's assume 1000 to make the paging work.", 'warning');
                        }

                        if (hits > self.metadata.get('maximum_results')['google']) {
                            self.ui.user_alert(
                                'Total results ' + hits + '. From Google Patents, the first 1000 results are accessible. ' +
                                'You might want to narrow your search by adding more search criteria.', 'warning');
                        }
                    });
                }

            });

        } else if (datasource == 'ftpro') {

            this.trigger('search:before', search_info);

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

        } else if (datasource == 'sdp') {

            this.trigger('search:before', search_info);

            // make the pager display the original query
            this.metadata.set('query_origin', query);

            var sdpsearch = new SdpSearch();
            sdpsearch.perform(query, options).done(function(response) {
                options = options || {};

                console.log('sdp response:', response);

                self.propagate_datasource_message(response);

                // propagate keywords
                self.metadata.set('keywords', sdpsearch.keywords);

                var publication_numbers = response['details'];
                var hits = response['meta']['pager']['totalEntries'];
                options['remote_limit'] = response['meta']['Limit'];

                self.perform_listsearch(options, query, publication_numbers, hits, 'pn', 'OR').done(function() {
                    // propagate upstream message again, because "perform_listsearch" clears it; TODO: enhance mechanics!
                    self.propagate_datasource_message(response);
                });

            });

        } else {
            this.ui.notify('Search provider "' + datasource + '" not implemented.', {type: 'error', icon: 'icon-search'});
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
        this.ui.reset_content();
        //this.ui.reset_content({keep_pager: true, documents: true});


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
                this.ui.user_alert('No results.', 'info');
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

        // compute list of requested publication numbers for this slice
        var publication_numbers = _.map(entries_sliced, function(entry) {
            var number;
            if (_.isObject(entry)) {
                number = entry['publication_number'];
            } else if (!_.isEmpty(entry)) {
                number = entry;
            }
            return number;
        });
        //log('publication_numbers:', publication_numbers);

        // compute query expression to display documents from OPS
        var query_ops_constraints = _(_.map(publication_numbers, function(publication_number) {
            if (publication_number) {
                return field + '=' + '"' + _.string.trim(publication_number, '"') + '"';
            }
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


        // for having a reference to ourselves in nested scopes
        var self = this;
        var _this = this;

        // establish comparator to bring collection items into same order of upstream result list
        // TODO: decouple/isolate this behavior from "global" scope, i.e. this is not reentrant
        this.documents_apply_comparator(publication_numbers);

        //var range = this.compute_range(options);
        return this.search.perform(this.documents, this.metadata, query_ops_cql, '1-10', {silent: true}).done(function() {

            // ------------------------------------------
            //   metadata propagation
            // ------------------------------------------

            // show the original query
            self.metadata.set('query_origin', query_origin);

            // show the original result size
            self.metadata.set('result_count', hits);

            // amend the current result range and paging parameter
            self.metadata.set('result_range', range);

            // FIXME: WTF - 17?
            self.metadata.set('pagination_entry_count', 17);


            // ------------------------------------------
            //   placeholders
            // ------------------------------------------
            // add placeholders for missing documents to model
            _this.documents_add_placeholders(publication_numbers);


            // ------------------------------------------
            //   housekeeping
            // ------------------------------------------
            // undefine comparator after performing action in order not to poise other queries
            // TODO: decouple/isolate this behavior from "global" scope, i.e. this is not reentrant
            self.documents.comparator = undefined;


            // ------------------------------------------
            //   ui tuning
            // ------------------------------------------
            $('.pagination').removeClass('span10');
            $('.pagination').addClass('span12');

            // TODO: selecting page size with DEPATISnet is currently not possible
            //$('.page-size-chooser').parent().remove();


            // ------------------------------------------
            //   downstream signalling
            // ------------------------------------------

            // propagate list of found document numbers to results collection
            // in order to make it possible to indicate which documents are missing
            self.results.set_reference_document_numbers(self.documents.get_document_numbers());

            // signal the results are ready
            self.trigger('results:ready');

        });

    },

    // comparator to bring collection items into same order of upstream result list
    documents_apply_comparator: function(documents_requested) {

        // TODO: decouple/isolate this behavior from "global" scope, i.e. this is not reentrant
        this.documents.comparator = function(document) {

            var debug = false;

            // get document number
            // TODO: maybe use .get_document_id() ?
            var document_id_full = document.get('@country') + document.get('@doc-number') + document.get('@kind');
            debug && log('document_id_full:', document_id_full);

            // compare against document numbers _with_ kindcode
            var index = findIndex(documents_requested, function(item) {
                return _.string.startsWith(item, document_id_full);
            });
            debug && log('index-1', index);

            // fall back to compare against document numbers w/o kindcode
            if (index == undefined) {

                var document_id_short = document.get('@country') + document.get('@doc-number');
                index = findIndex(documents_requested, function(item) {
                    return _.string.startsWith(item, document_id_short);
                });
                // advance by one, since we usually want to insert _after_ that one
                if (index != undefined) {
                    index++;
                }
                debug && log('index-2', index);
            }

            // again, fall back to compare against full-cycle neighbors
            if (index == undefined) {

                var full_cycle_numbers_full = document.attributes.get_full_cycle_numbers();
                var full_cycle_numbers = _.difference(full_cycle_numbers_full, [document_id_full]);

                // check each full-cycle member ...
                _.each(full_cycle_numbers, function(full_cycle_number) {
                    var full_cycle_number_nokindcode = patent_number_strip_kindcode(full_cycle_number);
                    // ... if it exists in list of requested documents
                    var index_tmp = findIndex(documents_requested, function(document_requested) {

                        var outcome =
                            _.string.startsWith(document_requested, full_cycle_number) ||
                            _.string.startsWith(document_requested, full_cycle_number_nokindcode);
                        return outcome;
                    });
                    if (index_tmp != undefined) {
                        index = index_tmp;
                    }
                });

                // advance by one, since we usually want to insert _after_ that one
                if (index != undefined) {
                    index++;
                }
                debug && log('index-3', index);
            }

            // if not found yet, put it to the end of the list
            if (index == undefined) {
                if (self.documents) {
                    index = self.documents.length;
                }
                debug && log('index-4', index);
            }

            return index;
        }

    },

    // add placeholders for missing documents to model
    documents_add_placeholders: function(documents_requested) {

        var debug = false;

        // list of requested documents w/o kindcode
        var documents_requested_kindcode = documents_requested;
        var documents_requested_nokindcode = _.map(documents_requested, patent_number_strip_kindcode);

        // list of documents in response with and w/o kindcode
        var documents_response_kindcode = [];
        var documents_response_nokindcode = [];

        // full-cycle publication numbers per document
        var documents_full_cycle_map = {};

        // collect information from response documents
        this.documents.each(function(document) {
            var document_id_kindcode = document.get('@country') + document.get('@doc-number') + document.get('@kind');
            var document_id_nokindcode = document.get('@country') + document.get('@doc-number');
            documents_response_kindcode.push(document_id_kindcode);
            documents_response_nokindcode.push(document_id_nokindcode);

            // build map for each number knowing its full-cycle neighbours
            var full_cycle_numbers_full = document.attributes.get_full_cycle_numbers();
            _.each(full_cycle_numbers_full, function(number) {
                if (!documents_full_cycle_map[number]) {
                    var full_cycle_numbers = _.difference(full_cycle_numbers_full, [number]);
                    documents_full_cycle_map[number] = full_cycle_numbers;
                }
            });
        });
        debug && log('documents_response_kindcode:', documents_response_kindcode);
        debug && log('documents_response_nokindcode:', documents_response_nokindcode);
        debug && log('documents_full_cycle_map:', documents_full_cycle_map);


        // compute list of missing documents with local alternatives

        // v1: naive
        //var documents_missing = _.difference(documents_requested, documents_response);

        // v2: sophisticated
        var documents_missing = [];
        _.each(documents_requested_kindcode, function(document_requested_kindcode) {

            var document_requested_nokindcode = patent_number_strip_kindcode(document_requested_kindcode);

            // compare with kindcodes
            var result_found =
                _.contains(documents_response_kindcode, document_requested_kindcode);

            // optionally, also compare without kindcodes
            if (document_requested_kindcode == document_requested_nokindcode) {
                result_found =
                    result_found ||
                    _.contains(documents_response_nokindcode, document_requested_nokindcode);
            }

            if (!result_found) {

                // populate list of possible local alternatives for given number w/o kindcode
                var alternatives_local = _.filter(documents_response_kindcode, function(item) {
                    return _.string.startsWith(item, document_requested_nokindcode);
                });

                // also add documents from full-cycle neighbours to list of possible local alternatives
                var full_cycle_numbers = documents_full_cycle_map[document_requested_kindcode];

                // fall back searching the full-cycle map w/o kindcodes
                if (_.isEmpty(full_cycle_numbers)) {
                    _.each(documents_full_cycle_map, function(value, key) {
                        if (_.string.startsWith(key, document_requested_nokindcode)) {
                            full_cycle_numbers = value;
                        }
                    });
                }

                // propagate the results
                if (!_.isEmpty(full_cycle_numbers)) {
                    Array.prototype.push.apply(alternatives_local, full_cycle_numbers);
                }

                // per-document response
                var document_missing = {
                    'number': document_requested_kindcode,
                    'alternatives_local':_.unique(alternatives_local),
                };

                documents_missing.push(document_missing);
            }

        });
        debug && log('documents_missing:', documents_missing);


        // inject placeholder objects for all missing documents
        var _this = this;
        _.each(documents_missing, function(document_missing) {

            // split patent number into components
            var patent = split_patent_number(document_missing.number);

            // inject placeholder model
            _this.documents.add(new GenericExchangeDocument({
                '__type__': 'ops-placeholder',
                '@country': patent.country,
                '@doc-number': patent.number,
                '@kind': patent.kind,
                'alternatives_local': document_missing.alternatives_local,
            }), {sort: false});
        });
        //log('documents:', this.documents);

        // sort documents in bulk
        if (this.documents.comparator) {
            this.documents.sort();
        }

        // trigger re-rendering through model-change
        this.documents.trigger('reset', this.documents);

    },

    // initialize model from url query parameters ("numberlist")
    parse_numberlist: function(payload) {
        if (!_.isEmpty(payload)) {
            var fieldname;
            var parts = payload.split(/=/);
            if (parts.length == 1) {
                fieldname = 'pn';
                payload   = parts[0];
            } else if (parts.length == 2) {
                fieldname = parts[0];
                payload   = parts[1];
            }
            var numberlist = _(payload.split(/[,\n]/)).map(function(entry) {
                return entry.trim();
            }).filter(function(entry) {
                return !(_.isEmpty(entry) || _.string.startsWith(entry, '//') || _.string.startsWith(entry, '#'));
            });
            return {data: numberlist, fieldname: fieldname};
        }
    },

    perform_numberlistsearch: function(options) {
        //log('perform_numberlistsearch');
        var numberlist = this.parse_numberlist($('#numberlist').val());
        if (numberlist) {
            var _this = this;
            normalize_numberlist(numberlist.data.join(',')).then(function(normalized) {
                var numbers_normalized = normalized['numbers-normalized']['all'];
                //log('numbers_normalized:', numbers_normalized);

                //var publication_numbers = numberlist.data;
                var publication_numbers = numbers_normalized || numberlist.data;
                var hits = publication_numbers.length;

                // actually perform the listsearch
                _this.perform_listsearch(options, undefined, publication_numbers, hits, numberlist.fieldname, 'OR');
            });
        } else {
            this.ui.notify("An empty numberlist can't be requested, please add some publication numbers.", {type: 'warning', icon: 'icon-align-justify'});
        }
    },

    compute_range: function(options) {
        var page_size = this.metadata.get('page_size');
        var default_range = '1-' + page_size;
        var range = options && options.range ? options.range : default_range;
        return range;
    },

    propagate_datasource_message: function(response) {
        log('propagate_datasource_message');
        this.ui.user_alert(response['message'], 'warning');
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
        // TODO: refactor using a Marionette Region
        if (this.projectChooserView) {
            this.projectChooserView.stopListening();
        }
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
        this.stopListening(null, "change:rate");
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
                _this.basketModel.add(number, {'reset_seen': true});
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
                item.save({score: score, dismiss: dismiss, seen: undefined}, {
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

    document_seen_twice: function(document_number) {

        // skip saving as "seen" if already in basket
        if (this.basketModel.exists(document_number)) {

            // if we occur the document a second time, mark as seen visually by increasing opacity
            var basket = this.basketModel.get_entry_by_number(document_number);
            if (basket.get('seen')) {
                return true;
            }

        }

        return false;
    },

    document_mark_seen: function(document_number) {
        var _this = this;

        if (!document_number) {
            return;
        }

        // skip saving as "seen" if already in basket
        if (this.basketModel.exists(document_number)) {
            return;
        }

        log('document_mark_seen:', document_number);

        this.basketModel.add(document_number).then(function(item) {

            item.save({seen: true}, {
                success: function() {

                    // don't backpropagate in realtime, this would probably immediately color the document gray
                    //_this.basketModel.trigger('change:rate', item, document_number);

                }, error: function() {
                    console.error('"seen" save error', document_number, item);
                }
            });

        });

    },


    // tear down user interface, clear all widgets
    shutdown_gui: function() {

        // basket and associated document indicators
        this.basketModel && this.basketModel.destroy();
        this.basket_bind_actions();
        this.basketView && this.basketView.render();

        // comments
        this.comments.store.set();

        // projects
        this.projects.reset();
        this.projectChooserView.clear();

    },

    user_has_module: function(module) {
        var module_abo = _(this.config.get('user.modules')).contains(module);
        var development_mode = this.config.get('request.host_name') == 'localhost';
        return module_abo || development_mode;
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
        model: this.metadata,
        bottom_pager: true,
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
