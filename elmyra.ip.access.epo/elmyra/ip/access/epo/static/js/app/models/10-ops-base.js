// -*- coding: utf-8 -*-
// (c) 2013-2015 Andreas Motl, Elmyra UG

OpsHelpers = Backbone.Model.extend({

    enrich_links: function(container, attribute, value_modifier, options) {

        options = options || {};

        var _this = this;
        return _.map(container, function(item) {

            if (_.isString(item)) {

                // v1 replace text with links
                return _this.enrich_link(item, attribute, item, value_modifier, options);

                // v2 use separate icon for link placement
                //var link = self.enrich_link('<i class="icon-external-link icon-small"></i>', attribute, item, value_modifier);
                //return item + '&nbsp;&nbsp;' + link;

            } else if (_.isObject(item)) {
                item.display = _this.enrich_link(item.display, attribute, item.display, value_modifier, options);
                return item;

            }

        });
    },

    enrich_link: function(label, attribute, value, value_modifier, options) {

        options = options || {};

        // fallback: use label, if no value is given
        if (!value) value = label;

        // skip enriching links when in print mode
        // due to phantomjs screwing them up when rendering to pdf
        var printmode = opsChooserApp.config.get('mode') == 'print';
        if (printmode) {
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
            link_template = _.template('<a href="" class="query-link" data-query-attribute="<%= attribute %>" data-query-value="<%= value %>"><%= label %></a>');
        } else if (kind == 'external') {
            query = encodeURIComponent(attribute + '=' + value);
            link_template = _.template('<a href="?query=<%= query %>" class="query-link incognito" target="<%= target %>" data-no-modifiers="<%= no_modifiers %>"><%= label %></a>');
        }

        // render link
        if (link_template) {
            var link = link_template({label: label, attribute: attribute, value: value, target: target, query: query, 'no_modifiers': options.no_modifiers && 'true' || 'false'});
            return link;
        }

    },

});

OpsBaseModel = Backbone.Model.extend({

    defaults: _({}).extend(OpsHelpers.prototype, {

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
            if (format == 'epodoc') {
                data.fullnumber = data.docnumber;

            } else {
                data.fullnumber = (data.country || '') + (data.docnumber || '') + (data.kind || '');
            }
            data.isodate = this.format_date(data.date);

            return data;

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

        format_date: function(value) {
            if (value) {
                return moment(value, 'YYYYMMDD').format('YYYY-MM-DD');
            }
        },

        get_citations_environment_button: function(options) {
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
                results = this.enrich_links(results, 'pn', null, {'no_modifiers': true});
            }
            return results;
        },

    }),

});
