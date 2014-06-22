// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG

IpsuiteNavigatorConfig = Backbone.Model.extend({

    defaults: {
        mode: undefined,
        context: 'default',
        project: 'ad-hoc',
        datasource: 'ops',
        'ship-param': 'payload',
    },

    initialize: function(options) {
        var _this = this;

        options = options || {};

        // only propagate options with defined values
        _.each(_.keys(options), function(key) {
            var value = options[key];
            if (value) {
                _this.set(key, value);
            }
        });

        this.update_baseurl();

    },

    update_baseurl: function() {
        var url = $.url(window.location.href);
        var baseurl = url.attr('protocol') + '://' + url.attr('host');
        if (url.attr('port')) baseurl += ':' + url.attr('port');
        baseurl += url.attr('path');
        this.set('baseurl', baseurl);
    },

    // send current state of config to browser history.pushState
    history_pushstate: function() {

        // get current parameters from url
        var url = $.url(window.location.href);
        var params = url.param();

        // aggregate parameters comprising viewer state, currently a 4-tuple
        var state = {
            mode: this.get('mode'),
            context: this.get('context'),
            project: this.get('project'),
            datasource: this.get('datasource'),
        };

        // merge current viewer state
        _(params).extend(state);

        // clear empty parameters
        for (key in params) {
            var value = params[key];
            if (_.isEmpty(value)) {
                delete params[key];
            }
        }

        // push parameters to browser history, changing the url in the location bar
        history.pushState({id: 'url-clean'}, '', '?' + $.param(params));

    },

});
