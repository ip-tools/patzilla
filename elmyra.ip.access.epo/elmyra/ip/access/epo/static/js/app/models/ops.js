// -*- coding: utf-8 -*-
// (c) 2013-2017 Andreas Motl, Elmyra UG

OpsPublishedDataSearch = Backbone.Model.extend({
    url: '/api/ops/published-data/search',
    keywords: [],
    perform: function(documents, metadata, query, range, more_options) {

        log('OpsPublishedDataSearch.perform');

        more_options = more_options || {};

        opsChooserApp.ui.indicate_activity(true);
        //$('.pager-area').hide();

        // TODO: enhance this as soon as we're in AMD land
        //$(opsChooserApp.paginationViewBottom.el).hide();

        // Propagate family member swapping
        var query_data = metadata.get('query_data');
        var family_swap_default = query_data && query_data['modifiers'] && Boolean(query_data['modifiers']['family-swap-ger']);

        var self = this;
        var _this = this;
        return this.fetch({
            data: $.param({ expression: query.expression, filter: query.filter, range: range, family_swap_default: family_swap_default}),
            success: function(model, response, options) {

                // Only gather keywords in regular OPS search mode
                if (metadata.get('searchmode') != 'subsearch') {
                    var keywords = options.xhr.getResponseHeader('X-Elmyra-Query-Keywords');
                    if (keywords) {
                        // workaround for weird Chrome bug: "X-Elmyra-Query-Keywords" headers are recieved duplicated
                        keywords = keywords.replace(/(.+), \[.+\]/, '$1');
                        self.keywords = jQuery.parseJSON(keywords);
                    }
                }

                opsChooserApp.ui.indicate_activity(false);
                opsChooserApp.ui.reset_content();

                console.log("response data:", response);
                // TODO: Get rid of this!? This should be handled by the error path if backend responds with proper HTTP status.
                if (_.isEmpty(response) || opsChooserApp.ui.propagate_cornice_errors(response)) {
                    documents.reset();
                    return;
                }

                //$('.pager-area').show();

                // get "node" containing record list from nested json response
                var search_result = response['ops:world-patent-data']['ops:biblio-search']['ops:search-result'];

                // unwrap response by creating a list of model objects from records
                var entries = [];
                var entries_full = [];
                if (!_.isEmpty(search_result)) {

                    // get query_data from metadata
                    var query_data = metadata.get('query_data');
                    query_data = query_data || {};
                    _.defaults(query_data, {'modifiers': {}});

                    // document display strategy: regular vs. full-cycle
                    var mode_full_cycle = Boolean(query_data['modifiers']['full-cycle']);

                    // document sort order: recent vs. descending
                    var order_recent_first = Boolean(query_data['modifiers']['recent-pub']);
                    var order_past_first = Boolean(query_data['modifiers']['first-pub']);

                    // search_result is nested, collect representative result documents
                    // while retaining additional result documents inside ['bibliographic-data']['full-cycle']
                    var results = [];
                    var exchange_documents_containers = to_list(search_result['exchange-documents']);
                    _(exchange_documents_containers).each(function(exchange_documents_container) {
                        var exchange_documents = to_list(exchange_documents_container['exchange-document']);

                        // collect full-cycle information from other result documents
                        var representations = [];
                        _(exchange_documents).each(function(exchange_document) {
                            // TODO: implement more sophisticated decisions how to order the documents
                            representations.push(new OpsExchangeDocument(exchange_document));
                        });
                        _(exchange_documents).each(function(exchange_document) {
                            exchange_document['full-cycle'] = representations;
                        });


                        // sort exchange documents by publication date
                        if (order_recent_first || order_past_first) {
                            exchange_documents = _.sortBy(exchange_documents, function(exchange_document) {
                                var document_id = (new OpsBaseModel()).attributes.get_document_id(
                                    exchange_document['bibliographic-data'], 'publication', 'docdb');
                                var isodate = document_id.isodate;
                                exchange_document.document_id = document_id;
                                return isodate;
                            });

                            if (order_recent_first) {

                                // sort reverse chronologically
                                exchange_documents = exchange_documents.reverse();

                                // downvote EP..A3 documents
                                //log('exchange_documents:', exchange_documents);
                                /*
                                var document_id = exchange_documents[0].document_id;
                                if (document_id['country'] == 'EP' && document_id['kind'] == 'A3') {
                                    _.move(exchange_documents, 0, 1);
                                }
                                */
                            }
                        }

                        // document display strategy: regular vs. full-cycle

                        // a) display all documents (full-cycle)
                        if (mode_full_cycle) {
                            results = $.merge(results, exchange_documents);

                        // b) use first result document as representative document
                        // TODO: implement more sophisticated decisions which document to choose as the representative
                        } else {
                            var representative_entry = exchange_documents[0];
                            results.push(representative_entry);
                        }

                    });

                    entries = self.make_models(results);

                }

                // propagate data to model collection instance
                documents.reset(entries, {silent: more_options.silent});

                // propagate metadata to model
                var biblio_search = response['ops:world-patent-data']['ops:biblio-search'];
                var result_count = biblio_search['@total-result-count'];
                var result_range_node = biblio_search['ops:range'];
                var result_range = result_range_node['@begin'] + '-' + result_range_node['@end'];
                var query_origin = {'expression': biblio_search['ops:query']['$']};
                var query_real = query_origin;
                metadata.set({
                    result_count: result_count,
                    result_range: result_range,
                    result_count_received: entries ? entries.length : 0,
                    query_origin: query_origin,
                    query_real: query_real,
                });
                metadata.set('keywords', _.union(self.keywords, metadata.get('keywords')));

            },
            error: function(model, xhr) {

                opsChooserApp.ui.indicate_activity(false);
                opsChooserApp.ui.reset_content({documents: true});

                if (xhr.status == 404) {
                    return;

                } else {
                    console.error('OPS search failed:', xhr);
                    opsChooserApp.ui.propagate_backend_errors(xhr);
                }

            }
        });

    },

    make_models: function(results) {
        var models = [];
        _(results).each(function(exchange_document) {
            if (exchange_document['@status'] == 'invalid result') {
                console.error('OPS INVALID RESULT:', exchange_document);
            } else {
                var model = new OpsExchangeDocument(exchange_document);
                models.push(model);
            }
        });
        return models;
    },

});

OpsExchangeMetadata = Backbone.Model.extend({

    defaults: {
        // these carry state, so switching the navigator into a special mode, currently
        reviewmode: false,

        datasource: 'ops',
        searchmode: null,
        page_size: 25,
        result_count: null,
        result_range: null,
        result_count_received: null,
        query_origin: null,
        query_real: null,
        pagination_entry_count: 12,
        pagination_pagesize_choices: [25, 50, 75, 100],
        pagination_current_page: 1,
        keywords: [],
        maximum_results: 2000,

        get_url: function() {
            var url =
                window.location.pathname +
                '?query=' + encodeURIComponent($('#query').val()) +
                '&pagesize=' + this.page_size;
            return url;
        },
        get_url_print: function() {
            return this.get_url() + '&mode=print';
        },
        get_url_pdf: function() {
            var url = this.get_url() + '&pdf=true';
            return url;
        },

    },

    initialize: function(collection) {
        var url = $.url(window.location.href);

        // propagate page size from url
        var pagesize = url.param('pagesize');
        if (pagesize) {
            this.set('page_size', parseInt(pagesize));
        }

        // TODO: propagate page number from url

    },

    resetToDefaults: function() {
        //this.clear();
        this.set(this.defaults);
    },

    resetSomeDefaults: function(options) {
        this.set(_(this.defaults).pick(
            'searchmode', 'result_count', 'result_range', 'result_count_received',
            'query_origin', 'query_real', 'keywords', 'page_size', 'maximum_results'
        ));
        if (options && options.clear) {
            this.set(_(this.defaults).pick(
                'pagination_current_page'
            ));
        }
    },

});

OpsPublishedDataCrawler = DatasourceCrawler.extend({

    initialize: function(options) {
        log('OpsPublishedDataCrawler.initialize');
        options = options || {};
        options.datasource = 'ops';
        this.__proto__.constructor.__super__.initialize.apply(this, arguments);
    },

    decode_numberlist: function(payload) {
        return payload['ops:world-patent-data']['ops:biblio-search']['ops:search-result']['publication-numbers'];
    },

});


OpsExchangeDocument = OpsBaseModel.extend({

        defaults: {},

        initialize: function(options) {
            this.set('datasource', 'ops');
            // TODO: enhance this as soon as we're in AMD land
            this.printmode = opsChooserApp.config.get('mode') == 'print';
        },

        select: function() {
            this.set('selected', true);
        },
        unselect: function() {
            this.set('selected', false);
        },

        get_datasource_label: function() {
            return 'EPO/OPS';
        },

        get_patent_number: function() {
            return this.get('@country') + this.get('@doc-number') + this.get('@kind');
        },

        get_publication_number: function(format) {
            var document_id = this.get_publication_reference(format);
            return document_id.fullnumber;
        },

        get_application_number: function(format) {
            var document_id = this.get_application_reference(format);
            return document_id.fullnumber;
        },

        get_publication_reference: function(format) {
            return OpsBaseModel.prototype.get_publication_reference(this.get('bibliographic-data'), format);
        },

        get_application_reference: function(format) {
            return OpsBaseModel.prototype.get_application_reference(this.get('bibliographic-data'), format);
        },

        get_patent_citation_list: function(links, id_type) {
            return OpsBaseModel.prototype.get_patent_citation_list(this.get('bibliographic-data'), links, id_type);
        },

        has_full_cycle: function() {
            return !_.isEmpty(this.get('full-cycle'));
        },

        get_full_cycle: function() {
            var results = [];
            var entries = this.get('full-cycle');
            _(entries).each(function(entry) {
                results.push(entry);
            });
            return results;
        },

        get_full_cycle_numbers: function() {
            var numbers = _.map(this.get_full_cycle(), function(model_pubcycle) {
                return model_pubcycle.get_document_number();
            });
            return numbers;
        },

});

_.extend(OpsExchangeDocument.prototype, OpsHelpers.prototype, {

        selected: false,

        // TODO: maybe move these methods to "viewHelpers"
        // http://lostechies.com/derickbailey/2012/04/26/view-helpers-for-underscore-templates/
        // https://github.com/marionettejs/backbone.marionette/wiki/View-helpers-for-underscore-templates#using-this-with-backbonemarionette

        get_title_list: function() {
            var title_list = [];
            var title_node = this['bibliographic-data']['invention-title'];
            if (title_node) {
                title_list = _.map(to_list(title_node), function(title) {
                    var lang_prefix = title['@lang'] && '[' + title['@lang'].toUpperCase() + '] ' || '[OL] ';
                    return lang_prefix + title['$'];
                });
            }
            // Poor mans sorting. Will yield titles in order of DE, EN, FR, OL, which seems to be a reasonable order.
            title_list.sort();
            return title_list;
        },

        get_abstract_list: function() {
            var abstract_list = [];
            var languages_seen = [];
            if (this['abstract']) {
                var abstract_node = to_list(this['abstract']);
                var abstract_list = abstract_node.map(function(node) {
                    var text_nodelist = to_list(node['p']);
                    var text = text_nodelist.map(function(node) { return node['$']; }).join(' ');
                    var lang = node['@lang'] ? node['@lang'].toUpperCase() : '';
                    var lang_prefix = lang ? '[' + lang + '] ' : '';
                    lang && languages_seen.push(lang);
                    return lang_prefix + text;
                });
            }

            // add possibility to acquire abstracts in german
            var country = this['@country'];
            if (country == 'DE' && !_(languages_seen).contains('DE')) {
                abstract_list.push(
                    '[DE] <a href="#" class="abstract-acquire" data-lang="de">OPS lacks german abstract, try to ' +
                    'acquire from different data source</a>');
            }

            return abstract_list;
        },

        get_applicants: function(links) {

            try {
                var applicants_root_node = this['bibliographic-data']['parties']['applicants'];
            } catch(e) {
                return [];
            }

            applicants_root_node = applicants_root_node || [];
            var applicants_node = applicants_root_node['applicant'];
            var applicants_list = this.parties_to_list(applicants_node, 'applicant-name');
            if (links) {
                applicants_list = this.enrich_links(applicants_list, 'applicant');
            }
            return applicants_list;

        },

        get_inventors: function(links) {

            try {
                var inventors_root_node = this['bibliographic-data']['parties']['inventors'];
            } catch(e) {
                return [];
            }

            inventors_root_node = inventors_root_node || [];
            var inventors_node = inventors_root_node['inventor'];
            var inventor_list = this.parties_to_list(inventors_node, 'inventor-name');
            if (links) {
                inventor_list = this.enrich_links(inventor_list, 'inventor');
            }
            return inventor_list;

        },

        parties_to_list: function(container, value_attribute_name) {

            // deserialize list of parties (applicants/inventors) from exchange payload
            var sequence_max = "0";
            var groups = {};
            _.each(container, function(item) {
                var data_format = item['@data-format'];
                var sequence = item['@sequence'];
                var value = _.string.trim(item[value_attribute_name]['name']['$'], ', ');
                groups[data_format] = groups[data_format] || {};
                groups[data_format][sequence] = value;
                if (sequence > sequence_max)
                    sequence_max = sequence;
            });
            //console.log(groups);

            // TODO: somehow display in gui which one is the "epodoc" and which one is the "original" value
            var entries = [];
            _.each(_.range(1, parseInt(sequence_max) + 1), function(sequence) {
                sequence = sequence.toString();
                var epodoc_value = groups['epodoc'][sequence];
                var original_value = groups['original'][sequence];

                //entries.push(epodoc_value + ' / ' + original_value);
                //entries.push(original_value);

                var canonical_value = original_value;
                if (epodoc_value) {
                    // strip country suffix from e.g. "L'ORÉAL [FR]"
                    canonical_value = epodoc_value.replace(/\[.+?\]/, '').trim();
                }

                var entry = {
                    display: canonical_value,
                    canonical: canonical_value,
                    epodoc: epodoc_value,
                    original: original_value,
                }

                entries.push(entry);
            });

            return entries;

        },

        get_classification_schemes: function() {
            return ['IPC', 'IPC-R', 'CPC', 'UC', 'FI', 'FTERM'];
        },

        get_classifications: function(links) {
            var classifications = {};
            classifications['IPC'] = this.get_classifications_ipc(links);
            classifications['IPC-R'] = this.get_classifications_ipcr(links);
            _(classifications).extend(this.get_classifications_more(links));
            //log('classifications:', classifications);
            return classifications;
        },

        get_classifications_ipc: function(links) {
            var entries = [];
            var container = this['bibliographic-data']['classification-ipc'];
            if (container) {
                var nodelist = to_list(container['text']);
                entries = _.map(nodelist, function(node) {
                    return node['$'];
                });
            }

            if (links) {
                entries = this.enrich_links(entries, 'ipc', quotate);
            }
            return entries;
        },

        get_classifications_ipcr: function(links) {
            var entries = [];
            var container = this['bibliographic-data']['classifications-ipcr'];
            if (container && container['classification-ipcr']) {
                var nodelist = to_list(container['classification-ipcr']);
                entries = _.map(nodelist, function(node) {
                    return node['text']['$'];
                });
            }

            entries = _(entries).map(function(entry) {
                return entry.substring(0, 15).replace(/ /g, '');
            });

            if (links) {
                entries = this.enrich_links(entries, 'ipc', quotate);
            }
            return entries;
        },

        get_classifications_more: function(links) {

            var classifications = {};
            var container = this['bibliographic-data']['patent-classifications'];
            var cpc_fieldnames = ['section', 'class', 'subclass', 'main-group', '/', 'subgroup'];

            var _this = this;

            if (container && container['patent-classification']) {
                var nodelist = to_list(container['patent-classification']);
                _(nodelist).each(function(node) {

                    var scheme = node['classification-scheme']['@scheme'];

                    var defaults = {};
                    defaults[scheme] = [];
                    _.defaults(classifications, defaults);

                    var entry;
                    if (scheme == 'CPC') {
                        var entry_parts = [];
                        _(cpc_fieldnames).each(function(cpc_fieldname) {
                            if (cpc_fieldname == '/') {
                                entry_parts.push('/');
                                return;
                            }
                            if (node[cpc_fieldname]) {
                                var part = node[cpc_fieldname]['$'];
                                entry_parts.push(part);
                            } else {
                                console.error(
                                    'Unknown cpc classification field "' + cpc_fieldname + '" ' +
                                    'for document "' + _this.get_document_number() + '":', node);
                            }
                        });
                        entry = entry_parts.join('');

                    } else if (scheme == 'UC' || scheme == 'FI' || scheme == 'FTERM') {
                        // UC was sighted with US documents, FI and FTERM with JP ones
                        entry = node['classification-symbol']['$'];

                    } else {
                        console.error('Unknown classification scheme "' + scheme + '" for document "' + _this.get_document_number() + '":', node);
                    }

                    if (!_.isEmpty(entry)) {
                        classifications[scheme].push(entry);
                    }

                });
            }

            if (links) {
                _.each(classifications, function(value, key) {
                    if (key == 'CPC') {
                        classifications[key] = _this.enrich_links(value, 'cpc', quotate);
                    }
                });
            }

            //log('classifications:', classifications);

            return classifications;
        },

        get_priority_claims: function(links) {
            var _this = this;
            var entries = [];
            var container = this['bibliographic-data']['priority-claims'];
            if (container) {
                var nodelist = to_list(container['priority-claim']);
                _(nodelist).each(function(node) {
                    var priority_epodoc = _this.get_document_id(node, null, 'epodoc');
                    var priority_original = _this.get_document_id(node, null, 'original');
                    if (!_.isEmpty(priority_epodoc)) {
                        var entry =
                            '<td class="span2">' + (priority_epodoc.isodate || '--') + '</td>' +
                            '<td class="span3">' + (priority_epodoc.docnumber && _this.enrich_link(priority_epodoc.docnumber, 'spr') || '--') + '</td>' +
                            '<td>';
                        if (!_.isEmpty(priority_original.docnumber)) {
                            entry += 'original: ' + priority_original.docnumber;
                        }
                        entry += '</td>';
                        entries.push(entry);
                    }
                });
            }
            return entries;
        },
        get_application_references: function(links) {
            var appnumber_epodoc = this.get_application_number('epodoc');
            var appnumber_original = this.get_application_number('original');
            var entry =
                '<td class="span2">' + (this.get_application_date() || '--') + '</td>' +
                '<td class="span3">' + (this.enrich_link(appnumber_epodoc, 'sap') || '--') + '</td>' +
                '<td>';
            if (!_.isEmpty(appnumber_original)) {
                entry += 'original: ' + appnumber_original;
            }
            entry += '</td>';
            return entry;
        },

        has_citations: function() {
            return this.get('bibliographic-data') && Boolean(this.get('bibliographic-data')['references-cited']);
        },

        get_citing_query: function() {
            var query = 'ct=' + this.get_publication_number('epodoc');
            return query;
        },
        get_same_citations_query: function() {
            var items = this.get_patent_citation_list(false, 'epodoc');
            return this.get_items_query(items, 'ct', 'OR');
        },
        get_all_citations_query: function() {
            var items = this.get_patent_citation_list(false, 'epodoc');
            return this.get_items_query(items, 'pn', 'OR');
        },
        get_items_query: function(items, fieldname, operator) {
            // FIXME: limit query to 10 items due to ops restriction
            items = items.slice(0, 10);
            items = items.map(function(item) { return fieldname + '=' + item; });
            var query = items.join(' ' + operator + ' ');
            return query;
        },

        _expand_links: function(text) {
            var urlPattern = /(http|ftp|https):\/\/[\w-]+(\.[\w-]+)+([\w.,@?^=%&amp;:\/~+#-]*[\w@?^=%&amp;\/~+#-])?/g;
            _(text.match(urlPattern)).each(function(item) {
                text = text.replace(item, '<a href="' + item + '" target="_blank">' + item + '</a>');
            });
            return text;
        },

        _add_crossref: function(text) {
            var printmode = opsChooserApp.config.get('mode') == 'print';
            if (printmode) {
                return text;
            } else {
                text += '&nbsp;&nbsp;<a href="http://search.crossref.org/?q=' + encodeURIComponent(text.replace(/^- /, '')) + '" target="_blank" class="incognito"><i class="icon-external-link"></i></a>';
                return text;
            }
        },

        get_npl_citation_list: function() {
            var self = this;
            var results = [];
            var container_top = this['bibliographic-data']['references-cited'];
            if (container_top) {
                var container = to_list(container_top['citation']);
                results = container
                    .filter(function(item) { return item['nplcit']; })
                    .map(function(item) { return item['nplcit']['text']['$']; })
                    //.map(self._expand_links)
                    .map(self._add_crossref)
                ;
            }
            return results;
        },

        has_fulltext: function() {
            // Compute whether fulltexts are available for this document
            var countries_allowed = opsChooserApp.config.get('system').total.fulltext_countries;
            return _(countries_allowed).contains(this['@country']);
        },

        // date values inside publication|application-reference
        search_date: function(node) {
            var value = null;
            _.each(node, function(item) {
                if (!value && item['date'] && item['date']['$']) {
                    value = item['date']['$'];
                }
            });
            return value;
        },

        get_publication_date: function() {
            return isodate_compact_to_verbose(this.search_date(this.get('bibliographic-data')['publication-reference']['document-id']));
        },

        get_application_date: function() {
            return isodate_compact_to_verbose(this.search_date(this.get('bibliographic-data')['application-reference']['document-id']));
        },

});

OpsExchangeDocumentCollection = Backbone.Collection.extend({

    model: OpsExchangeDocument,

    initialize: function(collection) {
        var self = this;
    },

    get_document_numbers: function() {
        var numbers = [];
        _.each(this.models, function(model) {

            // push the document numbers
            numbers.push(model.get_document_number());

            // push more numbers from full-cycle
            var full_cycle_numbers = model.get_full_cycle_numbers();
            Array.prototype.push.apply(numbers, full_cycle_numbers);
        });

        // make list of unique items
        numbers = _.unique(numbers);

        return numbers;
    },

    get_placeholder_document_numbers: function() {
        // Returns list of document numbers used as placeholders
        var numbers = [];
        _.each(this.models, function(model) {
            if (model.get('__type__') == 'ops-placeholder') {
                numbers.push(model.get_document_number());
            }
        });
        return numbers;
    },

});


OpsFulltext = Marionette.Controller.extend({

    initialize: function(document_number) {
        log('OpsFulltext.initialize');
        this.document_number = document_number;
    },

    get_datasource_label: function() {
        return 'EPO/OPS';
    },

    get_claims: function() {

        var _this = this;
        var deferred = $.Deferred();

        var url = _.template('/api/ops/<%= document_number %>/claims')({ document_number: this.document_number});
        $.ajax({url: url, async: true})
            .success(function(payload) {
                if (payload) {
                    var claims = payload['ops:world-patent-data']['ftxt:fulltext-documents']['ftxt:fulltext-document']['claims'];
                    //console.log('claims', document_number, claims);

                    // TODO: maybe unify with display_description
                    var content_parts = _(to_list(claims['claim']['claim-text'])).map(function(item) {
                        return '<p>' + _(item['$']).escape().replace(/\n/g, '<br/>') + '</p>';
                    });
                    var content_text = content_parts.join('\n');
                    var response = {
                        html: content_text,
                        lang: claims['@lang'],
                    };
                    deferred.resolve(response, _this.get_datasource_label());
                }
            }).error(function(error) {
                console.warn('Error while fetching claims from OPS for', _this.document_number, error);
                deferred.resolve({html: 'No data available'});
            });

        return deferred.promise();

    },

    get_description: function() {

        var _this = this;
        var deferred = $.Deferred();

        var url = _.template('/api/ops/<%= document_number %>/description')({ document_number: this.document_number});
        $.ajax({url: url, async: true})
            .success(function(payload) {
                if (payload) {
                    var description = payload['ops:world-patent-data']['ftxt:fulltext-documents']['ftxt:fulltext-document']['description'];
                    //console.log('description', document_number, description);

                    // TODO: maybe unify with display_claims
                    var content_parts = _(to_list(description.p)).map(function(item) {
                        return '<p>' + _(item['$']).escape().replace(/\n/g, '<br/><br/>') + '</p>';
                    });
                    var content_text = content_parts.join('\n');
                    var response = {
                        html: content_text,
                        lang: description['@lang'],
                    };
                    deferred.resolve(response, _this.get_datasource_label());
                }
            }).error(function(error) {
                console.warn('Error while fetching description from OPS for', _this.document_number, error);
                deferred.resolve({html: 'No data available'});
            });

        return deferred.promise();

    },

});



OpsFamilyMember = OpsBaseModel.extend(OpsHelpers.prototype, {
    parse: function(response) {
        response['priority-claim'] = to_list(response['priority-claim']);
        return response;
    }
});

OpsFamilyCollection = Backbone.Collection.extend({

    model: OpsFamilyMember,

    initialize: function(models, options) {
        this.document_number = options.document_number;
        this.constituents = options.constituents;
    },

    url: function(options) {
        var url = _.template('/api/ops/publication/<%= document_number %>/family/inpadoc')({ document_number: this.document_number});
        if (this.constituents) {
            url += '?constituents=' + this.constituents;
        }
        return url;
    },

    parse: function(response) {
        return to_list(response['ops:world-patent-data']['ops:patent-family']['ops:family-member']);
    }

});
