// -*- coding: utf-8 -*-
// (c) 2013,2014 Andreas Motl, Elmyra UG

OpsPublishedDataSearch = Backbone.Model.extend({
    url: '/api/ops/published-data/search',
    keywords: [],
    perform: function(documents, metadata, query, range) {

        log('OpsPublishedDataSearch.perform');

        opsChooserApp.ui.indicate_activity(true);
        //$('.pager-area').hide();

        // TODO: enhance this as soon as we're in AMD land
        $(opsChooserApp.paginationViewBottom.el).hide();

        var self = this;
        return this.fetch({
            data: $.param({ query: query, range: range}),
            success: function(model, response, options) {

                var keywords = options.xhr.getResponseHeader('X-Elmyra-Query-Keywords');
                if (keywords) {
                    // workaround for weird Chrome bug: "X-Elmyra-Query-Keywords" headers are recieved duplicated
                    keywords = keywords.replace(/(.+), \[.+\]/, '$1');
                    self.keywords = jQuery.parseJSON(keywords);
                }

                opsChooserApp.ui.indicate_activity(false);
                opsChooserApp.ui.reset_content();

                console.log("response data:");
                console.log(response);

                if (_.isEmpty(response)) {
                    documents.reset();
                    return;
                }

                $('.pager-area').show();

                // get "node" containing record list from nested json response
                var search_result = response['ops:world-patent-data']['ops:biblio-search']['ops:search-result'];

                // unwrap response by creating a list of model objects from records
                var entries = [];
                var entries_full = [];
                if (!_.isEmpty(search_result)) {

                    // search_result is nested, collect representative result documents
                    // while retaining additional result documents inside ['bibliographic-data']['full-cycle']
                    var results = [];
                    var exchange_documents_containers = to_list(search_result['exchange-documents']);
                    _(exchange_documents_containers).each(function(exchange_documents_container) {
                        var exchange_documents = to_list(exchange_documents_container['exchange-document']);

                        // collect full-cycle information from other result documents
                        var representations = [];
                        _(exchange_documents).each(function(exchange_document) {
                            representations.push(new OpsExchangeDocument(exchange_document));
                        });
                        _(exchange_documents).each(function(exchange_document) {
                            exchange_document['bibliographic-data']['full-cycle'] = representations;
                        });

                        // a) display all documents (full-cycle)
                        if (opsChooserApp.config.get('mode.full-cycle')) {
                            results = $.merge(results, exchange_documents);

                        // b) use first result document as representative document
                        } else {
                            var representative_entry = exchange_documents[0];
                            results.push(representative_entry);
                        }

                    });

                    entries = self.make_models(results);

                }

                // propagate data to model collection instance
                documents.reset(entries);

                // propagate metadata to model
                var biblio_search = response['ops:world-patent-data']['ops:biblio-search'];
                var result_count = biblio_search['@total-result-count'];
                var result_range_node = biblio_search['ops:range'];
                var result_range = result_range_node['@begin'] + '-' + result_range_node['@end'];
                var query_origin = biblio_search['ops:query']['$'];
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
            error: function(model, response) {

                //console.log("api error: " + response.responseText);

                opsChooserApp.ui.indicate_activity(false);
                opsChooserApp.ui.reset_content({documents: true});

                var response = jQuery.parseJSON(response.responseText);
                if (response['status'] == 'error') {
                    _.each(response['errors'], function(error) {
                        var tpl = _.template($('#backend-error-template').html());

                        // convert simple error format to detailed error format
                        error.description = error.description || {};
                        if (_.isString(error.description)) {
                            error.description = {content: error.description};
                        }
                        _(error.description).defaults({headers: {}});

                        var alert_html = tpl(error);
                        $('#alert-area').append(alert_html);
                    });
                    $(".very-short").shorten({showChars: 0, moreText: 'more', lessText: 'less'});
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
        // TODO: move to their respective places
        maximum_results: {
            'ops': 2000,
            'depatisnet': 1000,
            'google': 1000,
        },

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
            'searchmode', 'result_count', 'result_range', 'result_count_received', 'query_origin', 'query_real', 'keywords'
        ));
        if (options && options.clear) {
            this.set(_(this.defaults).pick(
                'pagination_current_page'
            ));
        }
    },

});

OpsExchangeDocument = Backbone.Model.extend({

    defaults: {
        selected: false,

        // TODO: move these methods to "viewHelpers"
        // http://lostechies.com/derickbailey/2012/04/26/view-helpers-for-underscore-templates/
        // https://github.com/marionettejs/backbone.marionette/wiki/View-helpers-for-underscore-templates#using-this-with-backbonemarionette

        get_patent_number: function() {
            return this['@country'] + this['@doc-number'] + this['@kind'];
        },

        get_document_number: function() {
            return this.get_patent_number();
        },

        get_publication_number: function(source) {
            var publication_id = this.get_publication_reference(source);
            return (publication_id.country || '') + (publication_id.number || '') + (publication_id.kind || '');
        },

        get_application_number: function(source) {
            var application_id = this.get_application_reference(source);
            return (application_id.country || '') + (application_id.number || '') + (application_id.kind || '');
        },

        get_linkmaker: function() {
            return new Ipsuite.LinkMaker(this);
        },

        get_full_cycle: function() {
            var results = [];
            var entries = this['bibliographic-data']['full-cycle'];
            _(entries).each(function(entry) {
                //entry['document-id'] = entry['country'] + entry['doc-number'] + entry['kind'];
                results.push(entry);
            });
            return results;
        },

        _flatten_textstrings: function(dict) {
            // TODO: not recursive yet
            var newdict = {};
            _(dict).each(function(value, key) {
                if (key == '@document-id-type') {
                    key = 'type';
                } else if (key == 'doc-number') {
                    key = 'number';
                }
                if (typeof(value) == 'object') {
                    var realvalue = value['$'];
                    if (realvalue) {
                        value = realvalue;
                    }
                }
                newdict[key] = value;
            });
            return newdict;
        },

        get_publication_reference: function(source) {
            // source = docdb|epodoc
            var entries = this['bibliographic-data']['publication-reference']['document-id'];
            var document_id = _(entries).find(function(item) {
                return item['@document-id-type'] == source;
            });
            return this._flatten_textstrings(document_id);
        },

        get_application_reference: function(source) {
            // source = docdb|epodoc
            var entries = this['bibliographic-data']['application-reference']['document-id'];
            var document_id = _(entries).find(function(item) {
                return item['@document-id-type'] == source;
            });
            return this._flatten_textstrings(document_id);
        },

        get_title_list: function() {
            var title_list = [];
            var title_node = this['bibliographic-data']['invention-title'];
            if (title_node) {
                title_list = _.map(to_list(title_node), function(title) {
                    var lang_prefix = title['@lang'] && '[' + title['@lang'].toUpperCase() + '] ' || '';
                    return lang_prefix + title['$'];
                });
            }
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
                    'acquire from different data source.</a>');
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

                var use_value = original_value;
                if (epodoc_value) {
                    use_value = epodoc_value.replace(/\[.+?\]/, '').trim();
                }
                entries.push(use_value);
            });

            return entries;

        },

        has_ipc: function() {
            return Boolean(this['bibliographic-data']['classification-ipc']);
        },
        get_ipc_list: function(links) {
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

        has_ipcr: function() {
            return Boolean(this['bibliographic-data']['classifications-ipcr']);
        },
        get_ipcr_list: function(links) {
            var entries = [];
            var container = this['bibliographic-data']['classifications-ipcr'];
            if (container) {
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

        has_cpc: function() {
            return Boolean(this['bibliographic-data']['patent-classifications']);
        },
        get_cpc_list: function(links) {
            var entries = [];
            var container = this['bibliographic-data']['patent-classifications'];
            var cpc_fieldnames = ['section', 'class', 'subclass', 'main-group', '/', 'subgroup'];

            var _this = this;

            if (container) {
                var nodelist = to_list(container['patent-classification']);
                _(nodelist).each(function(node) {
                    var scheme = node['classification-scheme']['@scheme'];
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
                                console.error('Unknown cpc classification field "' + cpc_fieldname + '" for document "' + _this.get_document_number() + '":', node);
                            }
                        });
                        var entry = entry_parts.join('');
                        entries.push(entry);

                    } else if (scheme == 'FI' || scheme == 'FTERM') {
                        // TODO: JP documents carry these

                    } else {
                        console.error('Unknown classification scheme "' + scheme + '" for document "' + _this.get_document_number() + '":', node);
                    }
                });
            }

            if (links) {
                entries = this.enrich_links(entries, 'cpc', quotate);
            }
            return entries;
        },

        get_priority_claims: function(links) {
            var _this = this;
            var entries = [];
            var container = this['bibliographic-data']['priority-claims'];
            if (container) {
                var nodelist = to_list(container['priority-claim']);
                _(nodelist).each(function(node) {
                    var priority = _this.get_priority_claim_document_id(node, 'epodoc');
                    if (!_.isEmpty(priority)) {
                        var entry =
                            _this.enrich_link(priority.number, 'spr', priority.number) + ', ' +
                                moment(priority.date, 'YYYYMMDD').format('YYYY-MM-DD');
                        entries.push(entry);
                    }
                });
            }
            return entries;
        },
        get_priority_claim_document_id: function(node, source) {
            // source = docdb|epodoc
            var entries = to_list(node['document-id']);
            var document_id = _(entries).find(function(item) {
                return item['@document-id-type'] == source;
            });
            return this._flatten_textstrings(document_id);
        },

        _find_document_number: function(container, id_type) {
            for (i in container) {
                var item = container[i];
                if (item['@document-id-type'] == id_type) {
                    var docnumber =
                        (item['country'] ? item['country']['$'] : '') +
                        (item['doc-number'] ? item['doc-number']['$'] : '') +
                        (item['kind'] ? item['kind']['$'] : '');
                    return docnumber;
                }
            }
        },

        has_citations: function() {
            return Boolean(this['bibliographic-data']['references-cited']);
        },

        get_patent_citation_list: function(links, id_type) {
            id_type = id_type || 'docdb';
            var self = this;
            var results = [];
            var container_top = this['bibliographic-data']['references-cited'];
            if (container_top) {
                var container = to_list(container_top['citation']);
                results = container
                    .filter(function(item) { return item['patcit']; })
                    .map(function(item) { return self._find_document_number(item['patcit']['document-id'], id_type); })
                ;
            }
            if (links) {
                results = this.enrich_links(results, 'pn');
            }
            return results;
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

        get_npl_citation_list: function() {
            var self = this;
            var results = [];
            var container_top = this['bibliographic-data']['references-cited'];
            if (container_top) {
                var container = to_list(container_top['citation']);
                results = container
                    .filter(function(item) { return item['nplcit']; })
                    .map(function(item) { return item['nplcit']['text']['$']; })
                    .map(self._expand_links)
                ;
            }
            return results;
        },

        has_fulltext: function() {
            /*
            3.1.2. Fulltext inquiry and retrieval including description or claims
                   Note, Currently full texts (description and/or claims) are only available for the following
                   authorities: EP, WO, AT, CA (claims only), CH.

               -- http://documents.epo.org/projects/babylon/eponet.nsf/0/7AF8F1D2B36F3056C1257C04002E0AD6/$File/OPS_RWS_ReferenceGuide_version1210_EN.pdf
            */
            var countries_allowed = ['EP', 'WO', 'AT', 'CA', 'CH'];

            // 2014-07-02: Add fulltexts for DE and US through DEPATISconnect
            countries_allowed.push('DE');
            countries_allowed.push('US');

            return _(countries_allowed).contains(this['@country']);
        },

        format_date: function(value) {
            if (value) {
                return value.slice(0, 4) + '-' + value.slice(4, 6) + '-' + value.slice(6, 8);
            }
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
            return this.format_date(this.search_date(this['bibliographic-data']['publication-reference']['document-id']));
        },

        get_application_date: function() {
            return this.format_date(this.search_date(this['bibliographic-data']['application-reference']['document-id']));
        },

    },

    initialize: function(options) {
        // TODO: enhance this as soon as we're in AMD land
        this.printmode = opsChooserApp.config.get('mode') == 'print';
    },

    get_document_number: function() {
        return this.attributes.get_patent_number();
    },

    select: function() {
        this.set('selected', true);
    },
    unselect: function() {
        this.set('selected', false);
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
            numbers.push(model.get_document_number());
            _.each(model.attributes.get_full_cycle(), function(model_pubcycle) {
                numbers.push(model_pubcycle.get_document_number());
            });
        });
        return numbers;
    },

});


OpsFulltext = Marionette.Controller.extend({

    initialize: function(document_number) {
        log('OpsFulltext.initialize');
        this.document_number = document_number;
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
                    deferred.resolve(response);
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
                    deferred.resolve(response);
                }
            }).error(function(error) {
                console.warn('Error while fetching description from OPS for', _this.document_number, error);
                deferred.resolve({html: 'No data available'});
            });

        return deferred.promise();

    },

});
