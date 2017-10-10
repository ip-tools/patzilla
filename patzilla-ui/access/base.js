// -*- coding: utf-8 -*-
// (c) 2013-2017 Andreas Motl, Elmyra UG

DatasourceSearch = Backbone.Model.extend({
    keywords: [],
    perform: function(query, options) {

        var query_parameters = { expression: query.expression, filter: query.filter };
        _.extend(query_parameters, options);

        // debugging
        log('DatasourceSearch.query_parameters:', query_parameters);
        //log('params:', $.param(query_parameters));

        navigatorApp.ui.indicate_activity(true);

        var self = this;
        var _options = options;
        return this.fetch({
            async: true,
            // TODO: Add JSON POST
            method: 'post',
            data: $.param(query_parameters),
            success: function (payload, response, options) {
                navigatorApp.ui.indicate_activity(false);
                //navigatorApp.ui.reset_content();

                // Clear current keywords
                self.keywords = [];

                // Use keywords from comfort form
                var keywords_comfort_raw = _options.keywords;
                if (!_.isEmpty(keywords_comfort_raw)) {
                    var keywords_comfort = self.decode_header_json(keywords_comfort_raw) || [];
                    log('keywords_comfort:', keywords_comfort);
                    self.keywords = self.keywords.concat(keywords_comfort);
                }

                // Use keywords from search backend or query expression in expert mode
                var keywords_backend_raw = options.xhr.getResponseHeader('X-PatZilla-Query-Keywords');
                if (keywords_backend_raw) {
                    var keywords_backend = self.decode_header_json(keywords_backend_raw) || [];
                    log('keywords_backend:', keywords_backend);
                    self.keywords = self.keywords.concat(keywords_backend);
                }

            },
            error: function(e, xhr) {

                console.error("DatasourceSearch error:", e, xhr);

                navigatorApp.ui.indicate_activity(false);
                navigatorApp.ui.reset_content({documents: true});

                navigatorApp.ui.propagate_backend_errors(xhr, {url: self.url});
            }
        });

    },

    decode_header_json: function(raw) {

        // workaround for weird Chrome bug: "X-PatZilla-Query-Keywords" headers are recieved duplicated
        // example: ["siemens", "bosch"], ["siemens", "bosch"]

        if (raw) {
            // wrap in yet another list
            raw = '[' + raw + ']';
            var data = jQuery.parseJSON(raw);
            if (!_.isEmpty(data)) {
                return data[0];
            }
        }
    },

});


DatasourceCrawler = Marionette.Controller.extend({

    initialize: function(options) {
        log('DatasourceCrawler.initialize');
        options = options || {};
        this.datasource = options.datasource;
        this.query = options.query;
        this.constituents = options.constituents;
        this.query_data = options.query_data || {};
        this.filter = options.filter || {};
    },

    start: function() {
        var deferred = $.Deferred();
        var more_params = $.param({
            'query_data': this.query_data,
        });
        var url_tpl = _.template('/api/<%= datasource %>/published-data/crawl/<%= constituents %>?expression=<%= expression %>&filter=<%= filter %>&<%= more_params %>');
        var url = url_tpl({
            datasource: this.datasource,
            constituents: this.constituents,
            expression: encodeURIComponent(this.query.expression),
            filter: encodeURIComponent(this.query.filter),
            more_params: more_params,
        });
        //log('url:', url);

        var _this = this;
        $.ajax({url: url, async: true})
            .success(function(payload) {
                if (payload) {
                    if (_this.constituents == 'pub-number') {

                        // Get numberlist from response
                        var numberlist = _this.decode_numberlist(payload);

                        // Apply arbitrary named filter to numberlist
                        numberlist = _this.apply_filter(numberlist);

                        deferred.resolve(numberlist);
                    } else {
                        deferred.reject('Unknown constituents "' + _this.constituents + '"');
                    }
                } else {
                    deferred.reject('Empty response');
                }
            }).error(function(error) {
                deferred.reject(JSON.stringify(error));
            });
        return deferred;
    },

    decode_numberlist: function(payload) {
        return payload['numbers'];
    },

    apply_filter: function(numberlist) {

        // strip patent kindcode from all numberlist items,
        // then build list of unique entries
        if (this.filter.strip_kindcodes) {
            numberlist = _(numberlist).map(function(item) {
                // strip patent kindcode for the poorest
                return patent_number_strip_kindcode(item);
            });
            numberlist = _(numberlist).uniq();
        }
        return numberlist;
    },

});


GenericExchangeDocument = Backbone.Model.extend({});

_.extend(GenericExchangeDocument.prototype,  {

    get_datasource_label: function() {
        return undefined;
    },

    get_patent_number: function() {
        return this.get_document_id().fullnumber;
    },

    get_document_id: function() {
        var data = {
            country: this.get('@country'),
            docnumber: this.get('@doc-number'),
            kind: this.get('@kind'),
        };
        data.fullnumber = (data.country || '') + (data.docnumber || '') + (data.kind || '');
        return data;
    },

    get_document_number: function() {
        return this.get_patent_number();
    },

    get_publication_number: function(format) {
        var document_id = this.get_publication_reference(format);
        return document_id.fullnumber;
    },

    get_application_number: function(format) {
        var document_id = this.get_application_reference(format);
        return document_id.fullnumber;
    },

    get_full_cycle: function() {
        return [];
    },

    get_full_cycle_numbers: function() {
        return [];
    },

    get_publication_reference: function(format) {
        return this.get_document_id();
    },

    get_application_reference: function(format) {
        return this.get_document_id();
    },

    get_citations_environment_button: function(options) {
    },
    get_patent_citation_list: function(links, id_type) {
        return [];
    },

    get_title_list: function() {
        return [];
    },

    get_abstract_list: function() {
        return [];
    },

    get_applicants: function(links) {
        return [];
    },

    get_inventors: function(links) {
        return [];
    },

    get_classification_schemes: function() {
        return [];
        //return ['IPC', 'IPC-R', 'CPC', 'UC', 'FI', 'FTERM'];
    },
    get_classifications: function(links) {
        return {};
    },

    get_priority_claims: function(links) {
        return [];
    },
    get_application_references: function(links) {
    },

    has_citations: function() {
        return false;
    },

    // TODO: Refactor away from here to vaporize the dependency on OpsBaseModel
    /*
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
     */
    get_citing_query: function() {},
    get_same_citations_query: function() {},
    get_all_citations_query: function() {},
    get_items_query: function() {},

    get_npl_citation_list: function() {
        return [];
    },

    has_fulltext: function() {
        return false;
    },

    has_full_cycle: function() {
        return false;
    },

    get_publication_date: function() {},
    get_application_date: function() {},

    enrich_links: function() {},
    enrich_link: function() {},

});
