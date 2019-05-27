// -*- coding: utf-8 -*-
// (c) 2013-2018 Andreas Motl <andreas.motl@ip-tools.org>

/**
 * ------------------------------------------
 *          main application object
 * ------------------------------------------
 */
NavigatorApp = Backbone.Marionette.Application.extend({

    setup_ui: function() {

        // Initialize content which still resides on page level (i.e. no template yet)
        $('#query').val(this.config.get('query'));

    },

    get_datasource: function() {
        var datasource = $('#datasource > .btn.active').data('value');
        return datasource;
    },

    set_datasource: function(datasource) {

        // Backward compatibility
        if (datasource == 'ifi') {
            datasource = 'ificlaims';
        }

        // Activate appropriate user interface elements
        this.queryBuilderView.setup_datasource_button(datasource);
        this.queryBuilderView.setup_cql_field_chooser();
        this.queryBuilderView.setup_common_form();
        this.queryBuilderView.setup_comfort_form();
    },

    bootstrap_datasource: function() {

        // Acquire "datasource" query parameter.
        var datasource = this.config.get('datasource');

        // Compute preferred data source.
        if (!datasource) {
            var datasources_enabled = this.config.get('datasources_enabled');
            var datasource_preferred = this.theme.get('ui.datasource_preferred');
            if (datasource_preferred && _(datasources_enabled).contains(datasource_preferred)) {
                datasource = datasource_preferred;
            }
        }

        // Use OPS as default data source.
        if (!datasource) {
            datasource = 'ops';
        }

        // Propagate computed data source downstream.
        this.set_datasource(datasource);
    },

    get_query: function() {
        var payload = {
            'expression': $('#query').val(),
            'filter': $('#cql-filter').val(),
        };
        return payload;
    },

    disable_reviewmode: function() {
        this.metadata.set('reviewmode', false);
    },

    populate_metadata: function() {
        var query_data = this.queryBuilderView.get_common_form_data();
        this.metadata.set('query_data', query_data);
    },


    // TODO: move to search.js

    start_search: function(options) {

        options = options || {};

        _.extend(options, {
            reviewmode: false,
            reset: ['pagination_current_page', 'page_size'],
        });

        this.disable_reviewmode();
        this.perform_search(options);
    },

    start_expert_search: function() {
        var query_data = this.queryBuilderView.get_common_form_data();
        this.start_search({flavor: 'cql', query_data: query_data});
    },

    // Perform OPS search and process response
    perform_search: function(options) {

        options = options || {};

        // propagate datasource
        // TODO: Fix me?
        //options.datasource = datasource;


        // 1. initialize search
        var query = this.get_query();
        var datasource = this.get_datasource();
        this.metadata.set('datasource', datasource);
        this.metadata.set('datasource_info', this.datasource_info(datasource));

        // It's probably important to reset e.g. "result_range",
        // because we have to fetch 1-10 for each single result page from OPS
        this.metadata.resetSomeDefaults(options.reset);


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


        // 3. Perform search

        if (_.isEmpty(query.expression)) {
            return;
        }

        // Propagate keywords from comfort form for fallback mechanism
        options.keywords = $('#keywords').val();

        // Propagate bunches of options around
        // a) to metadata object
        // b) to search_info summary object
        // TODO: consolidate somehow
        var search_info = {datasource: datasource, query: query};

        // Logging
        console.info('App.perform_search', '\nsearch_info=', search_info, '\noptions    =', options);

        // Dispatch and propagate options
        if (options.flavor) {
            this.metadata.set('flavor', options.flavor);
            search_info.flavor = options.flavor;
        }
        if (options.query_data) {
            this.metadata.set('query_data', options.query_data);
        }
        search_info.query_data = this.metadata.get('query_data');

        var self = this;
        var _this = this;

        // OPS is the main data source for bibliographic data.
        // It is used for all things display.
        if (datasource == 'ops') {
            var range = this.compute_range(options);
            search_info.range = range;
            this.trigger('search:before', search_info);

            var engine = navigatorApp.search;
            engine.perform(this.documents, this.metadata, query, range).then(function() {

                _this.trigger('search:success', search_info);

                var hits = self.metadata.get('result_count');
                var hits_max = self.metadata.get('maximum_results');
                if (hits == 0) {
                    _this.ui.no_results_alert(search_info);

                } else if (hits > hits_max) {
                    _this.ui.user_alert('Total hits: ' + hits + '.    ' +
                        'The first ' + hits_max + ' hits are accessible from OPS.  ' +
                        'You can narrow your search by adding more search criteria.', 'warning');
                }

                // propagate keywords
                log('engine.keywords:', engine.keywords);
                _this.metadata.set('keywords', engine.keywords);

                // signal the results are ready
                _this.trigger('results:ready');

                // Record the current search query
                search_info.result_count = hits;
                _this.trigger('query:record', search_info);

            }).fail(function(xhr) {

                _this.trigger('search:failure', search_info);

                if (xhr.status == 404) {

                    // Propagate zero result count
                    _this.metadata.set('result_count', 0);

                    // Display "No results" notification
                    _this.ui.no_results_alert(search_info);

                }

                // signal the results are ready
                _this.trigger('results:ready');

            });

        // Generic data source adapters
        } else if (this.has_datasource(datasource)) {
            var datasource_info = this.datasource_info(datasource);
            var engine_class = datasource_info.adapter.search;
            var engine = new engine_class();
            search_info.engine = engine;
            return this.generic_search(search_info, options);

        } else if (datasource == 'google') {

            this.trigger('search:before', search_info);

            // make the pager display the original query
            this.metadata.set('query_origin', query);

            var engine = new GooglePatentSearch();
            engine.search(search_info, query, options);

        } else {
            this.ui.notify('No data source adapter for "' + datasource + '".', {type: 'error', icon: 'icon-search'});
        }

    },

    generic_search: function(search_info, options) {

        this.trigger('search:before', search_info);

        var engine = search_info.engine;
        var query = search_info.query;

        // make the pager display the original query
        this.metadata.set('query_origin', query);

        var _this = this;
        return engine.perform(query, options).then(function(response) {
            options = options || {};

            // Signal search success
            _this.trigger('search:success', search_info);

            log('upstream-response:', response);
            log('engine.keywords:', engine.keywords);

            // Propagate information from backend to user interface

            // Max hits
            _this.metadata.set('maximum_results', response.meta.navigator.max_hits);

            // Message and Keywords
            _this.propagate_datasource_message(response);
            _this.metadata.set('keywords', engine.keywords);

            // Propagate page control parameters to listsearch
            var hits = response.meta.navigator.count_total;
            options['remote_limit'] = response.meta.navigator.limit;

            // Record the current search query
            search_info.result_count = hits;
            _this.trigger('query:record', search_info);

            // Propagate search results to listsearch
            var publication_numbers = response['details'];

            // Perform list search. Currently in buckets of 10.
            _this.perform_listsearch(options, query, publication_numbers, hits, 'pn', 'OR').always(function() {
                // Propagate upstream message again, because "perform_listsearch" currently clears it
                // TODO: Improve these mechanics!
                _this.propagate_datasource_message(response, options);
            });

        }).fail(function(xhr) {

            _this.trigger('search:failure', search_info);

            if (xhr.status == 404) {

                // Propagate zero result count
                _this.metadata.set('result_count', 0);

                // Display "No results" notification
                _this.ui.no_results_alert(search_info);

            } else {
                // TODO: Propagate to frontend. Use "ui.user_alert" or "ui.propagate_cornice_errors"?
                console.error('Generic data search failed:', xhr);
            }

            // Signal the results are ready to run other ui setup tasks
            // e.g. Report issue machinery
            _this.trigger('results:ready');

        });

    },

    send_query: function(query, options) {
        if (query) {
            $('#query').val(query);
            navigatorApp.perform_search(options);
            $(window).scrollTop(0);
        }
    },


    // Perform ops search and process response
    perform_listsearch: function(options, query_origin, entries, hits, field, operator) {

        options = options || {};

        // Debugging
        /*
        log('perform_listsearch.options:', options);
        log('perform_listsearch.query:  ', query_origin);
        log('perform_listsearch.entries:', entries);
        log('perform_listsearch.hits:   ', hits);
        */

        // Filter empty elements from entries
        entries = _.filter(entries, function(entry) {
            return !_.isEmpty(_.string.trim(entry));
        });

        // Querying by single document numbers has a limit of 10 at OPS
        var page_size = 10;
        this.metadata.set('page_size', page_size);
        options.local_limit = page_size;

        // Set parameter to control subsearch.
        this.metadata.set('searchmode', 'subsearch');

        // Prepare searching.
        this.ui.indicate_activity(false);
        this.ui.reset_content();
        //this.ui.reset_content({keep_pager: true, documents: true});

        if (_.isEmpty(entries)) {

            console.warn('Empty entries when performing listsearch at OPS');

            // Display "No results" warning
            var datasource = options.datasource || (options.query_data && options.query_data.datasource);
            this.ui.no_results_alert({datasource: datasource, query: query_origin});

            // Signal the results are (not) ready
            this.trigger('results:ready');

            // Return something async void
            var deferred = $.Deferred();
            deferred.resolve();
            return deferred.promise();
        }


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

        // TODO: Get rid of this!?
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

        // ------------------------------------------
        //   metadata propagation
        // ------------------------------------------
        var _this = this;
        var propagate_metadata = function() {

            // Display original query
            _this.metadata.set('query_origin', query_origin);

            // Override with original result count
            _this.metadata.set('result_count', hits);

            // Amend result range and paging parameter
            _this.metadata.set('result_range', range);

            // FIXME: WTF - 17?
            _this.metadata.set('pagination_entry_count', 17);

        };


        // result entries to display
        var entries_sliced = entries.slice(sstart, ssend);
        //log('entries_sliced:', entries_sliced);

        // Propagate local hit count
        options.local_hits = entries_sliced.length;


        // If there are no results after slicing, skip searching at OPS,
        // but pretend by making up metadata in the same way.
        if (_.isEmpty(entries_sliced)) {

            console.warn('Empty sliced entries when performing listsearch at OPS');

            propagate_metadata();

            this.documents.reset();

            // Signal the results are (not) ready
            this.trigger('results:ready');

            // Return something async void
            var deferred = $.Deferred();
            deferred.resolve();
            return deferred.promise();
        }


        // Propagate to generic result collection
        var datasource_info = this.current_datasource_info();
        if (datasource_info && datasource_info.adapter.entry) {
            if (!_.isEmpty(entries_sliced) && _.isObject(entries_sliced[0])) {
                try {
                    this.results.reset(entries_sliced);
                } catch (ex) {
                    console.warn('Problem propagating data to results collection:', ex);
                    //throw(ex);
                }
            } else {
                this.results.reset();
            }
        } else {
            var datasource = this.get_datasource();
            console.warn('Generic result entry model not implemented for data source "' + datasource + '"');
        }

        // Compute list of requested publication numbers for this slice
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


        // Compute query expression to display documents from OPS
        var query_ops_constraints = _(_.map(publication_numbers, function(publication_number) {
            if (publication_number) {
                // 2016-04-23: Do it without quotes. Does this break anything?
                //return field + '=' + '"' + _.string.trim(publication_number, '"') + '"';
                return field + '=' + _.string.trim(publication_number, '"');
            }
        }));
        var query_ops_cql = query_ops_constraints.join(' ' + operator + ' ');
        console.log('OPS CQL query:', query_ops_cql);

        if (!query_origin) {
            query_origin = {'expression': query_ops_cql};
        }

        //$('#query').val(query_origin);


        // for having a reference to ourselves in nested scopes
        var self = this;
        var _this = this;

        // establish comparator to bring collection items into same order of upstream result list
        // TODO: decouple/isolate this behavior from "global" scope, i.e. this is not reentrant
        this.documents_apply_comparator(publication_numbers);

        //var range = this.compute_range(options);
        return this.search.perform(this.documents, this.metadata, {'expression': query_ops_cql}, '1-10', {silent: true}).always(function() {

            // ------------------------------------------
            //   metadata propagation
            // ------------------------------------------
            propagate_metadata();


            // ------------------------------------------
            //   placeholders
            // ------------------------------------------
            // add placeholders for missing documents to model
            _this.documents_add_placeholders(publication_numbers);


            // ------------------------------------------
            //   data propagation / rendering
            // ------------------------------------------
            // trigger re-rendering through model-change
            _this.documents.trigger('reset', _this.documents);


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
            self.results.set_placeholder_document_numbers(self.documents.get_placeholder_document_numbers());

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


            // 1. Compare against document numbers _with_ kindcode
            var index = findIndex(documents_requested, function(item) {
                return _.string.startsWith(item, document_id_full);
            });
            debug && log('index-1', index);
            if (index != undefined) return index;


            // 2. Fall back to compare against document numbers w/o kindcode
            var document_id_short = document.get('@country') + document.get('@doc-number');
            index = findIndex(documents_requested, function(item) {
                return _.string.startsWith(item, document_id_short);
            });
            debug && log('index-2', index);
            if (index != undefined) return index;

            // 3. again, fall back to compare against full-cycle neighbors
            var full_cycle_numbers_full = document.get_full_cycle_numbers();
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
            debug && log('index-3', index);
            if (index != undefined) return index;

            // 4. if not found yet, put it to the end of the list
            if (self.documents) {
                index = self.documents.length;
            }
            debug && log('index-4', index);
            if (index != undefined) return index;

        }

    },

    // add placeholders for missing documents to model
    documents_add_placeholders: function(documents_requested) {

        var debug = false;

        // list of requested documents w/o kindcode
        var documents_requested_kindcode = documents_requested;
        var documents_requested_nokindcode = _.map(documents_requested, patent_number_strip_kindcode);

        debug && log('documents_requested_kindcode:', documents_requested_kindcode);
        debug && log('documents_requested_nokindcode:', documents_requested_nokindcode);

        // list of documents in response with and w/o kindcode
        var documents_response_kindcode = [];
        var documents_response_nokindcode = [];

        // full-cycle publication numbers per document
        var documents_full_cycle_map = {};

        // which documents have been swapped?
        var documents_swapped = {};

        // collect information from response documents
        this.documents.each(function(document) {
            var document_id_kindcode = document.get('@country') + document.get('@doc-number') + document.get('@kind');
            var document_id_nokindcode = document.get('@country') + document.get('@doc-number');
            documents_response_kindcode.push(document_id_kindcode);
            documents_response_nokindcode.push(document_id_nokindcode);

            // build map for each number knowing its full-cycle neighbours
            var full_cycle_numbers_full = document.get_full_cycle_numbers();
            _.each(full_cycle_numbers_full, function(number) {
                if (!documents_full_cycle_map[number]) {
                    var full_cycle_numbers = _.difference(full_cycle_numbers_full, [number]);
                    documents_full_cycle_map[number] = full_cycle_numbers;
                }
            });

            if (document.get('__meta__')) {
                var swapped = document.get('__meta__')['swapped'];
                if (swapped) {
                    _.each(swapped['list'], function(item) {
                        documents_swapped[item] = true;
                    });
                }
            }
        });
        var document_numbers_swapped = _.keys(documents_swapped);

        debug && log('documents_response_kindcode:', documents_response_kindcode);
        debug && log('documents_response_nokindcode:', documents_response_nokindcode);
        debug && log('documents_full_cycle_map:', documents_full_cycle_map);
        debug && log('document_numbers_swapped:', document_numbers_swapped);


        // Compute list of missing documents respecting local alternatives

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

            // Don't display swapped documents as missing
            if (_.contains(document_numbers_swapped, document_requested_kindcode) ||
                _.contains(document_numbers_swapped, document_requested_nokindcode)) {
                result_found = true;
            }

            if (!result_found) {

                // Compute alternatives
                var alternatives = [];


                // 1. Numbers w/o kindcode
                var nokindcode = _.filter(documents_response_kindcode, function(item) {
                    return _.string.startsWith(item, document_requested_nokindcode);
                });
                Array.prototype.push.apply(alternatives, nokindcode);


                // 2. Documents from full-cycle neighbours
                var full_cycle_numbers = documents_full_cycle_map[document_requested_kindcode];
                // Fall back searching the full-cycle map w/o kindcodes
                if (_.isEmpty(full_cycle_numbers)) {
                    _.each(documents_full_cycle_map, function(value, key) {
                        if (_.string.startsWith(key, document_requested_nokindcode)) {
                            full_cycle_numbers = value;
                        }
                    });
                }
                if (!_.isEmpty(full_cycle_numbers)) {
                    Array.prototype.push.apply(alternatives, full_cycle_numbers);
                }


                // 3. Be graceful to WO anomalies like
                //    - WO2003049775A2 vs. WO03049775A2 or
                //    - WO2001000469A1 vs. WO0100469A1
                if (_.string.startsWith(document_requested_kindcode, "WO")) {
                    //log('documents_response_kindcode:', documents_response_kindcode);
                    var wo_alternatives = _.filter(documents_response_kindcode, function(item) {

                        // Denormalize WO number
                        var wo_number = document_requested_kindcode.slice(2, -2);
                        var wo_kindcode = document_requested_kindcode.slice(-2);

                        // Strip century component from 4-digit year
                        wo_number = wo_number.slice(2);

                        // Compute alternative and compare with current item
                        var wo_short_variants = [];
                        wo_short_variants.push('WO' + wo_number + wo_kindcode);

                        // Strip first digit from number after 2-digit year, if zero
                        if (wo_number.slice(2, 3) == '0') {
                            wo_number = wo_number.slice(0, 2) + wo_number.slice(3);
                            wo_short_variants.push('WO' + wo_number + wo_kindcode);
                        }
                        //log('wo_short_variants:', wo_short_variants);

                        var wo_found = false;
                        _.each(wo_short_variants, function(wo_variant) {
                            if (_.string.startsWith(item, wo_variant)) {
                                wo_found = true;
                                return;
                            }
                        });

                        return wo_found;

                    });
                    Array.prototype.push.apply(alternatives, wo_alternatives);
                }


                // per-document response
                var document_missing = {
                    'number': document_requested_kindcode,
                    'alternatives_local':_.unique(alternatives),
                };

                documents_missing.push(document_missing);
            }

        });
        debug && log('documents_missing:', documents_missing);


        // Skip updating the collection of documents if nothing would change
        if (_.isEmpty(documents_missing)) {
            return;
        }

        // Inject placeholder objects for all missing documents
        var _this = this;
        _.each(documents_missing, function(document_missing) {

            // Split patent number into components
            var patent = split_patent_number(document_missing.number);

            var placeholder;

            // Fall back to IFI Claims for bibliographic data
            var ificlaims_settings = navigatorApp.config.get('system').datasource.ificlaims;
            var ificlaims_allowed =
                ificlaims_settings && ificlaims_settings.details_enabled &&
                _.contains(ificlaims_settings.details_countries, patent.country);

            // || _.isEmpty(document_missing.alternatives_local)
            if (ificlaims_allowed) {
                var ificlaims_doc = new IFIClaimsDocument({document_number: document_missing.number});

                // TODO:
                // Move to async mode! The current problem is that setting "placeholder = ificlaims_doc" is too
                // late for further processing, so the whole function must be made asynchronous.
                try {
                    var r = ificlaims_doc.fetch({sync: true, async: false})
                        .then(function() {
                            console.info('Document "' + document_missing.number + '" available at IFI Claims.');
                            //log('ificlaims.document:', ificlaims_doc);
                            placeholder = ificlaims_doc;
                        })
                        .catch(function(error) {
                            console.warn('Document "' + document_missing.number + '" not available at IFI Claims:', error);
                        });
                } catch(ex) {
                    console.warn(ex);
                }
            }

            // Use a generic placeholder for display as last resort
            if (!placeholder) {
                log('Add placeholder GenericExchangeDocument for:', patent);
                placeholder = new GenericExchangeDocument({
                    '__type__': 'ops-placeholder',
                    '@country': patent.country,
                    '@doc-number': patent.number,
                    '@kind': patent.kind,
                    'alternatives_local': document_missing.alternatives_local,
                });
            }

            // Inject placeholder model
            if (placeholder) {
                _this.documents.add(placeholder, {sort: false});
            }

        });
        //log('documents:', this.documents);

        // sort documents in bulk
        if (this.documents.comparator) {
            this.documents.sort();
        }

    },

    // Initialize model from url query parameters ("numberlist")
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

        options = options || {};

        //log('perform_numberlistsearch');
        var numberlist = this.parse_numberlist($('#numberlist').val());
        if (numberlist) {

            // Reset pager and more before kicking off numberlist search
            this.metadata.resetSomeDefaults(options.reset);

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
            this.ui.notify(
                "An empty numberlist can't be requested, please add some document numbers.",
                {type: 'warning', icon: 'icon-align-justify'});
        }
    },

    compute_range: function(options) {
        var page_size = this.metadata.get('page_size');
        var default_range = '1-' + page_size;
        var range = options && options.range ? options.range : default_range;
        return range;
    },

    propagate_datasource_message: function(response, options) {

        options = options || {};

        log('propagate_datasource_message');

        // Generic backend message
        var bucket = undefined;
        response && response.navigator && (bucket = response.navigator.user_info);
        if (_.isObject(bucket)) {
            this.ui.user_alert(bucket.message, bucket.kind);

        } else if (_.isString(bucket)) {
            this.ui.user_alert(bucket, 'info');
        }

        if (response.message) {
            this.ui.user_alert(response.message, 'warning');
        }

        this.propagate_datasource_signals(response, options);
    },

    propagate_datasource_signals: function(response, options) {

        options = options || {};

        // Special purpose user information signalling

        // 1. Feature "Remove family members"
        var meta = response.meta;
        if (meta && meta.navigator && meta.navigator.postprocess && meta.navigator.postprocess.action == 'feature_family_remove') {

            // How many documents have actually been removed on this result page?
            var count_removed = meta.navigator.postprocess.info.removed;

            // Get information from pager
            var offset = meta.navigator.offset;
            var limit  = meta.navigator.limit;

            // Compute ratio of removed family members vs. total results on this result page
            var family_removed_ratio = count_removed / meta.navigator.count_page;

            // Compute estimated total savings on documents to review
            var count_total           = meta.navigator.count_total;
            var count_total_estimated = count_total * (1 - family_removed_ratio);
            var count_saved_estimated = count_total - count_total_estimated;

            // Propagate informational data to user
            var tpldata = {
                start: offset + 1,
                end:   offset + limit,
                count_removed: count_removed,
                count_total_estimated: Math.floor(count_total_estimated),
                count_saved_estimated: Math.floor(count_saved_estimated),
                family_members_removed: response.navigator.family_members.removed,
                chunksize: meta.navigator.limit,
            };

            if (count_removed > 0) {
                var info_body = require('./results/family-members-removed-some.html')({data: tpldata});
            } else {
                var info_body = require('./results/family-members-removed-none.html')({data: tpldata});
            }
            this.ui.user_alert(info_body, 'info');

            // Display additional information when reaching empty result pages
            if (options.local_hits == 0 && options.local_limit && options.range_end && options.remote_limit) {
                var recommended_next_page_remote =
                    ((Math.floor((options.range_end - 1) / options.remote_limit) + 1) * options.remote_limit) + 1;
                var recommended_next_page_local =
                    Math.floor(recommended_next_page_remote / options.local_limit) + 1;

                var max_page_local = navigatorApp.paginationViewBottom.get_max_page();
                var has_more_results = recommended_next_page_local <= max_page_local;

                if (has_more_results) {
                    tpldata.recommended_next_page_local = recommended_next_page_local;
                }

                var info_body = require('./results/family-members-removed-empty-page.html')({data: tpldata});
                this.ui.user_alert(info_body, 'info');

                // Go to page containing next results after the gap of removed items
                if (has_more_results) {
                    $('#next-page-with-results-button').on('click', function() {
                        navigatorApp.paginationViewBottom.set_page(recommended_next_page_local);
                    });
                }

            }
        }

        if (meta && meta.navigator && meta.navigator.count_total) {
            var hits = meta.navigator.count_total;
            var hits_max = meta.navigator.max_hits;
            if (hits > hits_max) {
                this.ui.user_alert('Total hits: ' + hits + '.    ' +
                    'The first ' + hits_max + ' hits are accessible from datasource "' + meta.upstream.name + '".  ' +
                    'You can narrow your search by adding more search criteria.', 'warning');
            }
        }

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
        this.stopListening(this, 'query:record');
        this.listenTo(this, 'query:record', function(args) {
            project.record_query(args);
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
        // 2016-05-02: Now updating config model after fetching the basket.
        var register_project = function() {
            _this.config.set('project', project.get('name'));
        }

        // Activate basket
        var basket = project.get('basket');

        // Runtime behavior changed when upgrading to jQuery 3. Counter this.
        if (basket == null) {
            console.warn('Reloading project because basket is null:', projectname);
            this.trigger('project:load', projectname);
            return;
        }

        // Refetch basket to work around localforage.backbone vs. backbone-relational woes
        // otherwise, data storage mayhem may happen, because of model.id vs. model.sync.localforageKey mismatch
        // FIXME: it's ridiculous that we don't receive stacktraces from within "then()"
        basket.fetch({
            success: function() {
                $.when(basket.fetch_entries()).then(function() {
                    _this.basket_activate(basket);
                    register_project();
                });
            },
            error: function(e, error) {
                console.error('Error while fetching basket object for project "' + projectname + '":', e, error);
                _this.basket_deactivate();
                register_project();
            },
        });

    },

    project_deactivate: function() {
        $(window).off('focus', this.project_reload);
    },

    project_reload: function() {
        // reload project
        var projectname = navigatorApp.project.get('name');
        navigatorApp.trigger('project:load', projectname);
    },

    // TODO: move to basket.js
    basket_deactivate: function() {

        console.log('App.basket_deactivate');

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

        // FIXME: Experimentally remove this weird/misplaced call.
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
        // TODO: Are old bindings killed properly?
        // FIXME: This style of stopListening is brutal!
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

        if (!this.basketModel) {
            console.warn('Basket subsystem not started. Rating not available.');
            return;
        }

        // TODO: maybe use an event handler for this, instead of a direct method call (e.g. "item:rendered")

        var _this = this;

        // handle checkbox clicks by add-/remove-operations on basket
        /*
        $(".chk-patent-number").on('click', function() {
            var patent_number = this.value;
            if (this.checked)
                _this.basketModel.add(patent_number);
            if (!this.checked)
                _this.basketModel.remove(patent_number);
        });
        */

        // handle button clicks by add-/remove-operations on basket
        $(".add-patent-number").off('click');
        $(".add-patent-number").on('click', function() {
            var patent_number = $(this).data('patent-number');
            _this.basketModel.add(patent_number);
        });
        $(".remove-patent-number").off('click');
        $(".remove-patent-number").on('click', function() {
            var patent_number = $(this).data('patent-number');
            _this.basketModel.remove(patent_number);
        });

        // handle "add all documents"
        $("#basket-add-all-documents").off('click');
        $("#basket-add-all-documents").on('click', function() {
            // collect all document numbers
            _this.documents.each(function(document) {
                var number = document.get_patent_number();
                _this.basketModel.add(number, {'reset_seen': true});
            });

        });

        // setup rating widget
        this.rating.setup_ui({callback: _.bind(this.document_rate, this)});

        // propagate basket contents to Add/Remove button states once when activating the basket
        // TODO: do this conditionally - only if Basket is enabled
        this.documents.each(function(document) {
            var number = document.get_patent_number();
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

        if (!this.basketModel) {
            // TODO: Throw a BasketError here
            throw new Error('Basket not active');
        }

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

        if (!this.basketModel) {
            // TODO: Throw a BasketError here
            throw new Error('Basket not active');
        }

        // skip saving as "seen" if already in basket
        if (this.basketModel.exists(document_number)) {
            return;
        }

        //log('document_mark_seen:', document_number);

        this.basketModel.add(document_number).then(function(item) {

            item.set('seen', true);
            //item.set('seen', true, { silent: true });

            item.save(null, {
                success: function() {

                    //console.info('"seen" save success', document_number, item);

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

        // Shutdown project chooser, being graceful against timing issues re. object lifecycle
        if (this.projectChooserView) {
            this.projectChooserView.clear();
        }

    },

    user_has_module: function(module) {
        var module_abo = _(this.config.get('user.modules')).contains(module);
        var development_mode = this.config.get('request.host_name').endsWith('localhost');
        return module_abo || development_mode;
    },

    register_component: function(name) {
        this.config.get('component_list').push(name);
    },

    component_enabled: function(name) {
        //log('is_enabled?: ', this.config.get('component_list'), name);
        return _.contains(this.config.get('component_list'), name);
    },

    register_datasource: function(name, info) {
        log('Registering data source adapter for "' + name + '"');
        this.config.get('datasources')[name] = info;
    },

    datasource_info: function(name) {
        return this.config.get('datasources')[name];
    },
    has_datasource: function(name) {
        return !_.isEmpty(this.config.get('datasources')[name]);
    },
    current_datasource_info: function() {
        var datasource = this.get_datasource();
        return this.datasource_info(datasource);
    },
    is_datasource_enabled: function(name) {
        var whitelist = navigatorApp.config.get('datasources_enabled');
        return _.contains(whitelist, name);
    },

});
