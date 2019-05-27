// -*- coding: utf-8 -*-
// (c) 2014-2016 Andreas Motl, Elmyra UG

NavigatorConfiguration = Backbone.Model.extend({

    defaults: {
        mode: undefined,
        context: 'default',
        project: 'ad-hoc',
        datasource: undefined,
        'ship-param': 'payload',
        component_list: [],
        datasources: {},
        datasources_enabled: [],
    },

    initialize: function(options) {
        var _this = this;

        console.log('Initialize NavigatorConfiguration');

        options = options || {};

        // preserve original/default attributes
        this._originalAttributes = _.clone(this.attributes);

        // only propagate options with defined values
        _.each(_.keys(options), function(key) {
            var value = options[key];
            if (value) {
                _this.set(key, value);
            }
        });

        this.uri = $.url(window.location.href);
        this.update_baseurl();

    },

    update_baseurl: function() {
        var url = this.uri;
        var baseurl = url.attr('protocol') + '://' + url.attr('host');
        var path = url.attr('path');
        if (url.attr('port')) baseurl += ':' + url.attr('port');

        if (path == '/') {
            // Don't add path if it is the root namespace "/",
            // this would cause anomalies downstream by rendering https://example.org//your/path urls.
        } else if (_.string.startsWith(path, '/view')) {
            // Also, don't add path if it is pointing to /view/... (e.g. /view/pn/EP0666666A2),
            // because in this cases we want the link to be to the domain only (e.g. https://patentview-develop.elmyra.de/)
            // TODO: Maybe also restrict to matching "patentview" in hostname
        } else {
            baseurl += path;
        }

        this.set('baseurl', baseurl);

    },

    // send current state of config to browser history.pushState
    history_pushstate: function() {

        // get current parameters from url
        var params = this.uri.param();

        // aggregate parameters comprising viewer state, currently a 4-tuple
        // see also components/permalink.js:PermalinkPlugin.query_parameters_viewstate
        var state = {
            mode: this.get('mode'),
            context: this.get('context'),
            project: this.get('project'),
            datasource: this.get('datasource'),
        };

        // merge current viewer state, but only if
        // - parameter does not differ from its default
        // - the current state is not already described by opaque parameters,
        //   i.e. "op" is not in url or config
        if (!this.uri.param('op')) {
            _.each(state, function(value, key) {
                if (this._originalAttributes[key] != value) {
                    params[key] = value;
                }
            }, this);
        }

        // finally, clear empty parameters
        _.each(params, function(value, key) {
            if (_.isEmpty(value)) {
                delete params[key];
            }
        });

        // push parameters to browser history, changing the url in the location bar
        if (!_.isEmpty(params)) {
            history.pushState({id: 'url-state'}, '', '?' + jQuery.param(params));
        }

    },

});


NavigatorTheme = Backbone.Model.extend({

    defaults: {
    },

    initialize: function() {
        console.log('Initialize NavigatorTheme');
    },
});
