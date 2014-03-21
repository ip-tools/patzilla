// -*- coding: utf-8 -*-
// (c) 2013,2014 Andreas Motl, Elmyra UG

OpsPublishedDataSearch = Backbone.Model.extend({
    url: '/api/ops/published-data/search',
    perform: function(documents, metadata, query, range) {

        indicate_activity(true);

        documents.reset();
        //$('.pager-area').hide();
        $(opsChooserApp.paginationViewBottom.el).hide();

        var self = this;
        this.fetch({
            data: $.param({ query: query, range: range}),
            success: function (payload) {

                indicate_activity(false);
                $('#alert-area').empty();
                $('.pager-area').show();

                //console.log("payload raw:");
                //console.log(payload);
                console.log("payload data:");
                console.log(payload['attributes']);

                // get "node" containing record list from nested json response
                var search_result = payload['attributes']['ops:world-patent-data']['ops:biblio-search']['ops:search-result'];

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
                var biblio_search = payload['attributes']['ops:world-patent-data']['ops:biblio-search'];
                var result_count = biblio_search['@total-result-count'];
                var result_range_node = biblio_search['ops:range'];
                var result_range = result_range_node['@begin'] + '-' + result_range_node['@end'];
                var query_real = biblio_search['ops:query']['$'];
                metadata.set({result_count: result_count, result_range: result_range, query_real: query_real});

                // run action bindings here after rendering data entries
                listview_bind_actions();

            },
            error: function(e, xhr) {

                //console.log("error: " + xhr.responseText);

                indicate_activity(false);
                $('#alert-area').empty();
                documents.reset();

                response = jQuery.parseJSON(xhr.responseText);
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
        page_size: 25,
        result_count: null,
        result_range: null,
        query_real: null,
        pagination_entry_count: 11,
        pagination_pagesize_choices: [25, 50, 75, 100],
    }

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
            var entries = this['bibliographic-data']['publication-reference']['document-id'];
            var document_id = _(entries).find(function(item) {
                return item['@document-id-type'] == source;
            });
            return this._flatten_textstrings(document_id);
        },

        get_application_reference: function(source) {
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
                entries.push(original_value);
            });

            return entries;

        },

        get_ipc_list: function(links) {
            var ipc_list = [];
            var ipc_node_top = this['bibliographic-data']['classifications-ipcr'];
            if (ipc_node_top) {
                var ipc_node = to_list(ipc_node_top['classification-ipcr']);
                ipc_list = _.map(ipc_node, function(ipc) {
                    return ipc['text']['$'];
                });
            }

            if (links) {
                ipc_list = this.enrich_links(ipc_list, 'ipc', function(value) {
                    return value.substring(0, 15).replace(/ /g, '')
                });
            }
            return ipc_list;

        },

        enrich_links: function(container, attribute, value_modifier) {
            var self = this;
            return _.map(container, function(item) {
                return self.enrich_link(item, attribute, item, value_modifier)
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
                link_template = _.template('<a class="query-link" href="" data-query-attribute="<%= attribute %>" data-query-value="<%= value %>"><%= label %></a>');
            } else if (kind == 'external') {
                query = encodeURIComponent(attribute + '=' + value);
                link_template = _.template('<a href="?query=<%= query %>" target="<%= target %>" class="incognito"><%= label %></a>');
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

        get_patent_citation_list: function(links) {
            var self = this;
            var results = [];
            var container_top = this['bibliographic-data']['references-cited'];
            if (container_top) {
                var container = to_list(container_top['citation']);
                results = container
                    .filter(function(item) { return item['patcit']; })
                    .map(function(item) { return self._find_document_number(item['patcit']['document-id'], 'docdb'); })
                ;
            }
            if (links) {
                results = this.enrich_links(results, 'pn');
            }
            return results;
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

        get_drawing_url: function() {
            // http://ops.epo.org/3.1/rest-services/published-data/images/EP/1000000/PA/firstpage.png?Range=1
            // http://ops.epo.org/3.1/rest-services/published-data/images/US/20130311929/A1/thumbnail.tiff?Range=1
            var url_tpl = _.template('/api/drawing/<%= patent_number %>');
            var url = url_tpl({patent_number: this.get_patent_number()});
            return url;
        },

        get_fullimage_url: function() {
            // http://ops.epo.org/3.1/rest-services/published-data/images/EP/1000000/A1/fullimage.pdf?Range=1
            var url_tpl = _.template('/api/ops/<%= patent_number %>/image/full');
            var url = url_tpl({patent_number: this.get_patent_number()});
            return url;
        },

        get_espacenet_pdf_url: function() {
            // http://worldwide.espacenet.com/espacenetDocument.pdf?flavour=trueFull&FT=D&CC=US&NR=6269530B1&KC=B1
            var url_tpl = _.template('http://worldwide.espacenet.com/espacenetDocument.pdf?flavour=trueFull&FT=D&CC=<%= country %>&NR=<%= docnumber %><%= kind %>&KC=<%= kind %>');
            var url = url_tpl({country: this['@country'], docnumber: this['@doc-number'], kind: this['@kind']});
            return url;
        },

        get_ops_pdf_url: function() {
            // /api/ops/EP0666666B1/pdf/all
            var url_tpl = _.template('/api/ops/<%= country %><%= docnumber %><%= kind %>/pdf/all');
            var url = url_tpl({country: this['@country'], docnumber: this['@doc-number'], kind: this['@kind']});
            return url;
        },

        get_epo_register_url: function() {
            // https://register.epo.org/application?number=EP95480005
            var document_id = this.get_application_reference('docdb');
            var url_tpl = _.template('https://register.epo.org/application?number=<%= country %><%= number %>');
            var url = url_tpl(document_id);
            return url;
        },

        get_inpadoc_legal_url: function() {
            // http://worldwide.espacenet.com/publicationDetails/inpadoc?CC=US&NR=6269530B1&KC=B1&FT=D
            var url_tpl = _.template('http://worldwide.espacenet.com/publicationDetails/inpadoc?FT=D&CC=<%= country %>&NR=<%= docnumber %><%= kind %>&KC=<%= kind %>');
            var url = url_tpl({country: this['@country'], docnumber: this['@doc-number'], kind: this['@kind']});
            return url;
        },

        get_dpma_register_url: function() {

            // TODO: use only for DE- and WO-documents

            // DE19630877.1 / DE19630877A1 / DE000019630877C2
            // http://localhost:6543/ops/browser?query=pn=DE19630877A1
            // http://localhost:6543/jump/dpma/register?pn=DE19630877
            // https://register.dpma.de/DPMAregister/pat/register?AKZ=196308771

            // DE102012009645.3 / DE102012009645A1
            // http://localhost:6543/ops/browser?query=pn=DE102012009645
            // http://localhost:6543/jump/dpma/register?pn=DE102012009645
            // https://register.dpma.de/DPMAregister/pat/register?AKZ=1020120096453

            // 1. DE102012009645 works
            //    -            DE102012009645A1: no
            //    - [docdb]    DE102012009645A: no
            //    - [epodoc]   DE20121009645: no
            //    - [original] 102012009645: no
            //    => use docdb format, but without kindcode
            //
            // 2. 102012009645 finds WO document 2012009645
            //    works as well: WO2012009645

            // 3. PCT/US2011/044199 does not work yet, why/how?

            var document_id = this.get_application_reference('docdb');
            var url_tpl = _.template('/office/dpma/register/application/<%= country %><%= number %>?redirect=true');
            var url = url_tpl(document_id);
            return url;
        },

        get_uspto_pair_url: function() {
            // http://portal.uspto.gov/pair/PublicPair
            var url_tpl = _.template('http://portal.uspto.gov/pair/PublicPair');
            var url = url_tpl({country: this['@country'], docnumber: this['@doc-number'], kind: this['@kind']});
            return url;
        },

        get_inpadoc_family_url: function() {
            // http://worldwide.espacenet.com/publicationDetails/inpadocPatentFamily?CC=US&NR=6269530B1&KC=B1&FT=D
            var url_tpl = _.template('http://worldwide.espacenet.com/publicationDetails/inpadocPatentFamily?FT=D&CC=<%= country %>&NR=<%= docnumber %><%= kind %>&KC=<%= kind %>');
            var url = url_tpl({country: this['@country'], docnumber: this['@doc-number'], kind: this['@kind']});
            return url;
        },

        get_ops_family_url: function() {
            // http://ops.epo.org/3.0/rest-services/family/publication/docdb/EP.2070806.B1/biblio,legal
            var url_tpl = _.template('http://ops.epo.org/3.0/rest-services/family/publication/docdb/<%= country %>.<%= docnumber %>.<%= kind %>/biblio,legal');
            var url = url_tpl({country: this['@country'], docnumber: this['@doc-number'], kind: this['@kind']});
            return url;
        },

        get_ccd_viewer_url: function() {
            // http://ccd.fiveipoffices.org/CCD-2.0/html/viewCcd.html?num=CH20130000292&type=application&format=epodoc
            // http://ccd.fiveipoffices.org/CCD-2.0/html/viewCcd.html?num=DE20132003344U&type=application&format=epodoc
            // http://ccd.fiveipoffices.org/CCD-2.0/html/viewCcd.html?num=US201113881490&type=application&format=epodoc
            var document_id = this.get_application_reference('epodoc');
            var url_tpl = _.template('http://ccd.fiveipoffices.org/CCD-2.0.4/html/viewCcd.html?num=<%= number %>&type=application&format=epodoc');
            var url = url_tpl(document_id);
            return url;
        },

        get_depatisnet_url: function() {
            // https://depatisnet.dpma.de/DepatisNet/depatisnet?action=bibdat&docid=DE000004446098C2
            // https://depatisnet.dpma.de/DepatisNet/depatisnet?action=bibdat&docid=EP0666666A2
            // https://depatisnet.dpma.de/DepatisNet/depatisnet?action=bibdat&docid=EP666666A2
            var document_id = this.get_publication_reference('docdb');
            var url_tpl = _.template('https://depatisnet.dpma.de/DepatisNet/depatisnet?action=bibdat&docid=<%= country %><%= number %><%= kind %>');
            var url = url_tpl(document_id);
            return url;
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
