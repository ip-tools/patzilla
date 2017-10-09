// -*- coding: utf-8 -*-
// (c) 2013-2017 Andreas Motl, Elmyra UG

QueryLinkMixin = Backbone.Model.extend({

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
