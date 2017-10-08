// -*- coding: utf-8 -*-
// (c) 2013-2017 Andreas Motl, Elmyra UG

OpsBaseModel = Backbone.Model.extend({

        get_document_id: function(node, reference_type, format) {
            /*
             reference_type = publication|application
             format = docdb|epodoc
             */
            node = node || this;
            var document_ids;
            if (reference_type) {
                var reference = reference_type + '-reference';
                document_ids = to_list(node[reference]['document-id']);
            } else {
                document_ids = to_list(node['document-id']);
            }
            var document_id = _(document_ids).find(function(item) {
                return item['@document-id-type'] == format;
            });

            var data = this.flatten_document_id(document_id);
            if (format == 'docdb') {
                data.isodate = isodate_compact_to_verbose(data.date);
                data.fullnumber = (data.country || '') + (data.docnumber || '') + (data.kind || '');

            } else if (format == 'epodoc') {
                data.isodate = isodate_compact_to_verbose(data.date);
                data.fullnumber = data.docnumber;

            } else if (format == 'original') {
                data.fullnumber = data.docnumber;

            }

            return data;

        },

        get_document_number: function() {
            return this.get_patent_number();
        },

        get_publication_reference: function(node, format) {
            return this.get_document_id(node, 'publication', format);
        },

        get_application_reference: function(node, format) {
            return this.get_document_id(node, 'application', format);
        },

        get_publication_number: function(node, format) {
            var document_id = this.get_publication_reference(node, format);
            return document_id.fullnumber;
        },

        get_application_number: function(node, format) {
            var document_id = this.get_application_reference(node, format);
            return document_id.fullnumber;
        },

        flatten_document_id: function(dict) {
            // TODO: not recursive yet
            var newdict = {};
            _(dict).each(function(value, key) {
                if (key == '@document-id-type') {
                    key = 'format';
                } else if (key == 'doc-number') {
                    key = 'docnumber';
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

        get_citations_environment_button: function(options) {
            //log('OpsBaseModel.get_citations_environment_button');
            options = options || {};
            var tpl = _.template($('#ops-citations-environment-button-template').html());
            return tpl({data: this, options: options});
        },

        get_patent_citation_list: function(node, links, id_type) {

            node = node || this;

            id_type = id_type || 'docdb';
            var self = this;
            var results = [];

            if (!node || !node['references-cited']) {
                return [];
            }

            var container_top = node['references-cited'];
            if (container_top) {
                var container = to_list(container_top['citation']);
                results = container
                    .filter(function(item) { return item['patcit'] && item['patcit']['document-id']; })
                    .map(function(item) {
                        var document_id = self.get_document_id(item['patcit'], null, id_type);
                        var fullnumber = self.flatten_document_id(document_id).fullnumber;

                        // fall back to epodoc format, if ops format yields empty number
                        if (_.isEmpty(fullnumber)) {
                            document_id = self.get_document_id(item['patcit'], null, 'epodoc');
                            fullnumber = self.flatten_document_id(document_id).fullnumber;
                        }
                        return fullnumber;
                    })
                ;
            }
            if (links) {
                results = QueryLinkMixin.prototype.enrich_links(results, 'pn', null, {'no_modifiers': true});
            }
            return results;
        },

});
