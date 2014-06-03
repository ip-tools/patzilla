// -*- coding: utf-8 -*-
// (c) 2013,2014 Andreas Motl, Elmyra UG

OpsPublishedDataSearch = Backbone.Model.extend({
    url: '/api/ops/published-data/search',
    keywords: [],
    perform: function(documents, metadata, query, range) {

        indicate_activity(true);

        documents.reset();
        //$('.pager-area').hide();
        $(opsChooserApp.paginationViewBottom.el).hide();

        var self = this;
        return this.fetch({
            data: $.param({ query: query, range: range}),
            success: function (model, response, options) {

                self.keywords = jQuery.parseJSON(options.xhr.getResponseHeader('X-Elmyra-Query-Keywords'));

                indicate_activity(false);
                reset_content();

                console.log("response data:");
                console.log(response);

                if (_.isEmpty(response)) {
                    return;
                }

                $('.pager-area').show();

                // get "node" containing record list from nested json response
                var search_result = response['ops:world-patent-data']['ops:biblio-search']['ops:search-result'];

                // unwrap response by creating a list of model objects from records
                var entries;
                if (search_result) {
                    $(opsChooserApp.paginationViewBottom.el).show();
                    var exchange_documents = to_list(search_result['exchange-documents']);
                    entries = _.map(exchange_documents, function(entry) { return new OpsExchangeDocument(entry['exchange-document']); });
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

                //console.log("error: " + response.responseText);

                indicate_activity(false);
                reset_content();

                var response = jQuery.parseJSON(response.responseText);
                if (response['status'] == 'error') {
                    _.each(response['errors'], function(error) {
                        var tpl = _.template($('#backend-error-template').html());
                        var alert_html = tpl(error);
                        $('#alert-area').append(alert_html);
                    });
                    $(".very-short").shorten({showChars: 0, moreText: 'more', lessText: 'less'});
                }
            }
        });

    },
});

OpsExchangeMetadata = Backbone.Model.extend({

    defaults: {
        // these carry state, so switching the navigator into a special mode, currently
        debugmode: false,
        reviewmode: false,

        datasource: null,
        searchmode: null,
        page_size: 25,
        result_count: null,
        result_range: null,
        result_count_received: null,
        query_origin: null,
        query_real: null,
        pagination_entry_count: 12,
        pagination_pagesize_choices: [25, 50, 75, 100],
        keywords: [],

        get_url: function() {
            var url =
                window.location.pathname +
                '?query=' + encodeURIComponent($('#query').val()) +
                '&pagesize=' + this.page_size;
            return url;
        },
        get_url_print: function() {
            return this.get_url() + '&print=true';
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

        // propagate debugmode from url
        var debug = url.param('debug');
        if (debug) {
            this.set('debugmode', true);
        }

    },

    resetToDefaults: function() {
        //this.clear();
        this.set(this.defaults);
    },

    resetSomeDefaults: function() {
        this.set(_(this.defaults).pick(
            'datasource', 'searchmode', 'result_count', 'result_range', 'result_count_received', 'query_origin', 'query_real', 'keywords'
        ));
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
                    var entry =
                        _this.enrich_link(priority.number, 'spr', priority.number) + ', ' +
                        moment(priority.date, 'YYYYMMDD').format('YYYY-MM-DD');
                    entries.push(entry);
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


        enrich_links: function(container, attribute, value_modifier) {
            var self = this;
            return _.map(container, function(item) {

                // v1 replace text with links
                return self.enrich_link(item, attribute, item, value_modifier);

                // v2 use separate icon for link placement
                //var link = self.enrich_link('<i class="icon-external-link icon-small"></i>', attribute, item, value_modifier);
                //return item + '&nbsp;&nbsp;' + link;
            });
        },

        enrich_link: function(label, attribute, value, value_modifier) {

            // fallback: use label, if no value is given
            if (!value) value = label;

            // skip enriching links when in print mode
            // due to phantomjs screwing them up when rendering to pdf
            if (PRINTMODE) {
                return value;
            }

            // TODO: make this configurable!
            var kind = 'external';
            var target = '_blank';
            var query = null;

            // apply supplied modifier function to value
            if (value_modifier)
                value = value_modifier(value);

            // if value contains spaces, wrap into quotes
            // FIXME: do this only, if string is not already quoted, see "services.py":
            //      if '=' not in query and ' ' in query and query[0] != '"' and query[-1] != '"'
            if (_.string.include(value, ' '))
                value = '"' + value + '"';

            // prepare link rendering
            var link_template;
            if (kind == 'internal') {
                link_template = _.template('<a href="" class="query-link" data-query-attribute="<%= attribute %>" data-query-value="<%= value %>"> <%= label %> </a>');
            } else if (kind == 'external') {
                query = encodeURIComponent(attribute + '=' + value);
                link_template = _.template('<a href="?query=<%= query %>" class="query-link incognito" target="<%= target %>"> <%= label %></a>');
            }

            // render link
            if (link_template) {
                var link = link_template({label: label, attribute: attribute, value: value, target: target, query: query});
                return link;
            }

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

});
